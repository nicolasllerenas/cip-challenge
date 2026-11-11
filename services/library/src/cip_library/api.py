from collections.abc import Iterator
from pathlib import Path

from cip_contracts import (
    CreateLibraryRequest,
    JobEvent,
    LibrarySummary,
    MetadataPatch,
    Paper,
    PaperMetadata,
    Passage,
    SearchRequest,
)
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from cip_library.chunking import PageChunker
from cip_library.config import Settings
from cip_library.embeddings import build_embedder
from cip_library.ingestion import IngestionService, library_id_for
from cip_library.metadata import CrossrefClient
from cip_library.search import HybridSearcher
from cip_library.store import LibraryStore

NDJSON = "application/x-ndjson"


def as_ndjson(events: Iterator[JobEvent]) -> Iterator[str]:
    return (event.to_ndjson() for event in events)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = LibraryStore(settings.data_dir / "library.db")
    embedder = build_embedder(settings)
    searcher = HybridSearcher(store, embedder)
    ingestion = IngestionService(
        store,
        embedder,
        PageChunker(settings.chunk_size, settings.chunk_overlap),
        searcher,
        CrossrefClient(settings.crossref_mailto) if settings.crossref_enabled else None,
    )
    app = FastAPI(title="CIP Library Service", version="0.1.0")

    def require_library(library_id: str) -> Path:
        path = store.library_path(library_id)
        if path is None:
            raise HTTPException(404, "No conozco esa biblioteca.")
        return Path(path)

    def require_paper(paper_id: str) -> Paper:
        paper = store.get_paper(paper_id)
        if paper is None:
            raise HTTPException(404, "No encontré ese artículo.")
        return paper

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "embedder": embedder.name}

    @app.post("/libraries", status_code=201)
    def create_library(request: CreateLibraryRequest) -> LibrarySummary:
        root = Path(request.path).expanduser()
        if not root.is_dir():
            raise HTTPException(422, "No encuentro esa carpeta. Revisa que exista y que tengas permiso de lectura.")
        library_id = library_id_for(root)
        store.upsert_library(library_id, str(root.resolve()))
        return get_library(library_id)

    @app.get("/libraries/{library_id}")
    def get_library(library_id: str) -> LibrarySummary:
        path = require_library(library_id)
        return LibrarySummary(
            library_id=library_id,
            path=str(path),
            counts=store.counts(library_id),
            papers=store.list_papers(library_id),
        )

    @app.post("/libraries/{library_id}/ingest")
    def ingest(library_id: str) -> StreamingResponse:
        root = require_library(library_id)
        return StreamingResponse(as_ndjson(ingestion.ingest(library_id, root)), media_type=NDJSON)

    @app.post("/libraries/{library_id}/search")
    def search(library_id: str, request: SearchRequest) -> list[Passage]:
        require_library(library_id)
        return searcher.search(library_id, request)

    @app.patch("/papers/{paper_id}")
    def patch_paper(paper_id: str, patch: MetadataPatch) -> Paper:
        paper = require_paper(paper_id)
        merged = {**paper.metadata.model_dump(), **patch.model_dump(exclude_unset=True)}
        return ingestion.update_metadata(paper, PaperMetadata.model_validate(merged))

    @app.get("/papers/{paper_id}/file")
    def paper_file(paper_id: str) -> FileResponse:
        paper = require_paper(paper_id)
        return FileResponse(paper.file_path, media_type="application/pdf", filename=paper.file_name)

    @app.get("/passages/{passage_id}")
    def passage(passage_id: str) -> Passage:
        found = store.passages([passage_id])
        if not found:
            raise HTTPException(404, "No encontré ese fragmento.")
        return found[0]

    return app
