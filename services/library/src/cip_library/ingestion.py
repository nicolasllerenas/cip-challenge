import hashlib
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from cip_contracts import EventType, JobEvent, Paper, PaperMetadata, PaperStatus, Stage

from cip_library.chunking import PageChunker
from cip_library.embeddings import Embedder
from cip_library.metadata import CrossrefClient, extract_metadata, merge_metadata, metadata_issues
from cip_library.pdf import UnreadablePdfError, extract_pdf
from cip_library.search import HybridSearcher
from cip_library.store import LibraryStore

OCR_ISSUE = "Parece un PDF escaneado: no tiene texto seleccionable, así que no puedo citarlo sin OCR."


def short_hash(value: str, length: int = 16) -> str:
    return hashlib.sha1(value.encode()).hexdigest()[:length]


def library_id_for(path: Path) -> str:
    return short_hash(str(path.resolve()), 12)


def file_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_pdfs(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf")


class IngestionService:
    def __init__(
        self,
        store: LibraryStore,
        embedder: Embedder,
        chunker: PageChunker,
        searcher: HybridSearcher,
        crossref: CrossrefClient | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._chunker = chunker
        self._searcher = searcher
        self._crossref = crossref

    def _index(self, library_id: str, paper_id: str, path: Path, fingerprint: str) -> Paper:
        paper = Paper(
            paper_id=paper_id,
            library_id=library_id,
            file_name=path.name,
            file_path=str(path),
            status=PaperStatus.FAILED,
        )
        try:
            extracted = extract_pdf(path)
        except UnreadablePdfError as error:
            failed = paper.model_copy(update={"issues": [str(error)]})
            self._store.save_paper(failed, fingerprint, [], np.zeros((0, 0)))
            return failed
        metadata = extract_metadata(extracted)
        if self._crossref and metadata.doi:
            metadata = merge_metadata(metadata, self._crossref.lookup(metadata.doi))
        chunks = self._chunker.split(extracted.pages) if extracted.has_text_layer else []
        status = PaperStatus.INDEXED if chunks else PaperStatus.NEEDS_OCR
        issues = metadata_issues(metadata) if status == PaperStatus.INDEXED else [OCR_ISSUE]
        indexed = paper.model_copy(
            update={"pages": len(extracted.pages), "status": status, "metadata": metadata, "issues": issues}
        )
        vectors = self._embedder.embed_documents([chunk.text for chunk in chunks]) if chunks else np.zeros((0, 0))
        self._store.save_paper(indexed, fingerprint, chunks, vectors)
        return indexed

    def ingest(self, library_id: str, root: Path) -> Iterator[JobEvent]:
        files = discover_pdfs(root)
        yield JobEvent(
            type=EventType.JOB_STARTED,
            stage=Stage.INDEXING,
            message=f"Encontré {len(files)} PDFs en «{root.name}»",
            data={"total": len(files)},
        )
        if not files:
            yield JobEvent(
                type=EventType.JOB_FAILED,
                stage=Stage.INDEXING,
                message="No encontré archivos PDF en esta carpeta. Elige la carpeta donde guardas tus artículos.",
                data={"code": "empty_folder"},
            )
            return
        known = self._store.fingerprints(library_id)
        present: set[str] = set()
        for position, path in enumerate(files, start=1):
            paper_id = short_hash(f"{library_id}:{path.relative_to(root).as_posix()}")
            present.add(paper_id)
            fingerprint = file_fingerprint(path)
            reused = known.get(paper_id) == fingerprint
            paper = self._store.get_paper(paper_id) if reused else None
            paper = paper or self._index(library_id, paper_id, path, fingerprint)
            yield JobEvent(
                type=EventType.PAPER_INDEXED,
                stage=Stage.INDEXING,
                message=paper.file_name,
                progress=position / len(files),
                data={"paper": paper.model_dump(mode="json"), "reused": reused},
            )
        self._store.remove_missing(library_id, present)
        self._searcher.invalidate(library_id)
        counts = self._store.counts(library_id)
        yield JobEvent(
            type=EventType.JOB_COMPLETED,
            stage=Stage.INDEXING,
            message=f"{counts.indexed} de {counts.total} artículos listos para citar",
            progress=1.0,
            data={"counts": counts.model_dump()},
        )

    def update_metadata(self, paper: Paper, metadata: PaperMetadata) -> Paper:
        issues = metadata_issues(metadata) if paper.status == PaperStatus.INDEXED else paper.issues
        updated = paper.model_copy(update={"metadata": metadata, "issues": issues})
        self._store.update_paper(updated)
        return updated
