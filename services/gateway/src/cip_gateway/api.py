import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from cip_contracts import (
    ClaimReview,
    CreateLibraryRequest,
    Draft,
    DraftRequest,
    ExportFormat,
    JobEvent,
    LibrarySummary,
    MetadataPatch,
    RenderRequest,
)
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from cip_gateway.config import Settings
from cip_gateway.jobs import JobManager
from cip_gateway.review import InvalidReviewError, apply_review
from cip_gateway.store import DraftSummary, GatewayStore, Job, JobKind
from cip_gateway.upstream import Upstream

FILENAME = re.compile(r'filename="([^"]+)"')


class LibraryOpened(BaseModel):
    library: LibrarySummary
    job_id: str


class JobAccepted(BaseModel):
    job_id: str


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.DOCX
    include_review_comments: bool = True


class ExportedFile(BaseModel):
    file_name: str
    path: str
    url: str


class ExportResult(BaseModel):
    files: list[ExportedFile]
    pending_review: int


async def as_sse(events: AsyncIterator[JobEvent | None]) -> AsyncIterator[str]:
    yield "retry: 3000\n\n"
    async for event in events:
        yield ": ping\n\n" if event is None else f"id: {event.seq}\ndata: {event.model_dump_json()}\n\n"


def create_app(settings: Settings | None = None, mounts: dict[str, httpx.AsyncBaseTransport] | None = None) -> FastAPI:
    settings = settings or Settings()
    store = GatewayStore(settings.data_dir / "gateway.db")
    jobs = JobManager(store, settings.heartbeat_seconds)
    client = httpx.AsyncClient(mounts=mounts, timeout=60)
    upstream = Upstream(client)
    library, agents, documents = settings.library_url, settings.agents_url, settings.documents_url

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await client.aclose()

    app = FastAPI(title="CIP Research Assistant Gateway", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    def require_job(job_id: str) -> Job:
        job = store.job(job_id)
        if job is None:
            raise HTTPException(404, "No encontré ese trabajo.")
        return job

    def require_draft(draft_id: str) -> Draft:
        draft = store.draft(draft_id)
        if draft is None:
            raise HTTPException(404, "No encontré ese borrador.")
        return draft

    @app.get("/v1/health")
    async def health() -> dict[str, Any]:
        services = [
            await upstream.health("library", f"{library}/health"),
            await upstream.health("agents", f"{agents}/health"),
            await upstream.health("documents", f"{documents}/health"),
        ]
        return {"status": "ok" if all(service["ok"] for service in services) else "degraded", "services": services}

    @app.post("/v1/libraries", status_code=201)
    async def open_library(request: CreateLibraryRequest) -> LibraryOpened:
        response = await upstream.request("POST", f"{library}/libraries", json=request.model_dump())
        summary = LibrarySummary.model_validate(response.json())
        job = jobs.start(
            JobKind.INGESTION, summary.library_id, upstream.events(f"{library}/libraries/{summary.library_id}/ingest")
        )
        return LibraryOpened(library=summary, job_id=job.job_id)

    @app.post("/v1/libraries/{library_id}/reindex", status_code=202)
    async def reindex(library_id: str) -> JobAccepted:
        await upstream.request("GET", f"{library}/libraries/{library_id}")
        job = jobs.start(JobKind.INGESTION, library_id, upstream.events(f"{library}/libraries/{library_id}/ingest"))
        return JobAccepted(job_id=job.job_id)

    @app.get("/v1/libraries/{library_id}")
    async def get_library(library_id: str) -> LibrarySummary:
        return LibrarySummary.model_validate(
            (await upstream.request("GET", f"{library}/libraries/{library_id}")).json()
        )

    @app.patch("/v1/papers/{paper_id}")
    async def patch_paper(paper_id: str, patch: MetadataPatch) -> dict[str, Any]:
        response = await upstream.request(
            "PATCH", f"{library}/papers/{paper_id}", json=patch.model_dump(mode="json", exclude_unset=True)
        )
        return response.json()

    @app.get("/v1/papers/{paper_id}/file")
    async def paper_file(paper_id: str) -> Response:
        response = await upstream.request("GET", f"{library}/papers/{paper_id}/file")
        return Response(response.content, media_type="application/pdf")

    @app.post("/v1/drafts", status_code=202)
    async def create_draft(request: DraftRequest) -> JobAccepted:
        job = jobs.start(
            JobKind.DRAFT, request.library_id, upstream.events(f"{agents}/runs", request.model_dump(mode="json"))
        )
        return JobAccepted(job_id=job.job_id)

    @app.get("/v1/drafts")
    def list_drafts() -> list[DraftSummary]:
        return store.drafts()

    @app.get("/v1/drafts/{draft_id}")
    def get_draft(draft_id: str) -> Draft:
        return require_draft(draft_id)

    @app.patch("/v1/drafts/{draft_id}/claims/{claim_id}")
    def review_claim(draft_id: str, claim_id: str, review: ClaimReview) -> Draft:
        draft = require_draft(draft_id)
        if draft.find_claim(claim_id) is None:
            raise HTTPException(404, "No encontré esa afirmación.")
        try:
            updated = apply_review(draft, claim_id, review)
        except InvalidReviewError as error:
            raise HTTPException(422, str(error)) from error
        store.update_draft(updated)
        return updated

    @app.post("/v1/drafts/{draft_id}/exports")
    async def export_draft(draft_id: str, request: ExportRequest) -> ExportResult:
        draft = require_draft(draft_id)
        target = settings.exports_dir / draft_id
        target.mkdir(parents=True, exist_ok=True)
        formats = [request.format, ExportFormat.BIBTEX] if request.format == ExportFormat.MARKDOWN else [request.format]
        files = []
        for export_format in formats:
            render = RenderRequest(
                draft=draft, format=export_format, include_review_comments=request.include_review_comments
            )
            response = await upstream.request("POST", f"{documents}/render", json=render.model_dump(mode="json"))
            match = FILENAME.search(response.headers.get("content-disposition", ""))
            name = "references.bib" if len(formats) > 1 and export_format == ExportFormat.BIBTEX else None
            name = name or (match.group(1) if match else f"borrador.{export_format.value}")
            path = target / name
            path.write_bytes(response.content)
            files.append(ExportedFile(file_name=name, path=str(path.resolve()), url=f"/v1/exports/{draft_id}/{name}"))
        return ExportResult(files=files, pending_review=draft.stats.pending_review)

    @app.get("/v1/exports/{draft_id}/{file_name}")
    def download_export(draft_id: str, file_name: str) -> FileResponse:
        folder = (settings.exports_dir / draft_id).resolve()
        path = (folder / file_name).resolve()
        if path.parent != folder or not path.is_file():
            raise HTTPException(404, "No encontré ese archivo exportado.")
        return FileResponse(path, filename=file_name)

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str) -> Job:
        return require_job(job_id)

    @app.get("/v1/jobs/{job_id}/events")
    def job_events(job_id: str, after: int = 0, last_event_id: str | None = Header(default=None)) -> StreamingResponse:
        require_job(job_id)
        resume_from = int(last_event_id) if last_event_id and last_event_id.isdigit() else after
        return StreamingResponse(
            as_sse(jobs.subscribe(job_id, resume_from)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/v1/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str) -> dict[str, bool]:
        require_job(job_id)
        return {"cancelled": await jobs.cancel(job_id)}

    return app
