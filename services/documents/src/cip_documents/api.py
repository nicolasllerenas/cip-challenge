import re
import unicodedata
from collections.abc import Callable

from cip_contracts import ExportFormat, RenderRequest
from fastapi import FastAPI, Response

from cip_documents.docx_renderer import render_docx
from cip_documents.text_renderers import render_bibtex, render_markdown

MEDIA_TYPES = {
    ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ExportFormat.MARKDOWN: "text/markdown; charset=utf-8",
    ExportFormat.BIBTEX: "application/x-bibtex; charset=utf-8",
}
RENDERERS: dict[ExportFormat, Callable[[RenderRequest], bytes]] = {
    ExportFormat.DOCX: lambda request: render_docx(request.draft, request.include_review_comments),
    ExportFormat.MARKDOWN: lambda request: render_markdown(request.draft).encode(),
    ExportFormat.BIBTEX: lambda request: render_bibtex(request.draft.references).encode(),
}


def file_stem(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:60] or "borrador"


def create_app() -> FastAPI:
    app = FastAPI(title="CIP Documents Service", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/render")
    def render(request: RenderRequest) -> Response:
        filename = f"{file_stem(request.draft.title)}.{request.format.value}"
        return Response(
            RENDERERS[request.format](request),
            media_type=MEDIA_TYPES[request.format],
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return app
