import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

MIN_CHARS_PER_PAGE = 200
HYPHENATED_BREAK = re.compile(r"(\w)-\n(\w)")


class UnreadablePdfError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedPdf:
    pages: list[str]
    info_title: str | None = None
    info_author: str | None = None

    @property
    def has_text_layer(self) -> bool:
        if not self.pages:
            return False
        return sum(len(page.strip()) for page in self.pages) / len(self.pages) >= MIN_CHARS_PER_PAGE / 2

    @property
    def front_matter(self) -> str:
        return "\n".join(self.pages[:2])


def _clean_info(value: object) -> str | None:
    text = str(value).strip() if value else ""
    return text or None


def _normalize(text: str) -> str:
    return HYPHENATED_BREAK.sub(r"\1\2", text.replace("\r", "")).strip()


def extract_pdf(path: Path) -> ExtractedPdf:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise UnreadablePdfError("El PDF está protegido con contraseña.")
        pages = [_normalize(page.extract_text() or "") for page in reader.pages]
        info = reader.metadata or {}
    except UnreadablePdfError:
        raise
    except Exception as error:
        raise UnreadablePdfError("No se pudo abrir el archivo; puede estar dañado o incompleto.") from error
    return ExtractedPdf(
        pages=pages,
        info_title=_clean_info(info.get("/Title")),
        info_author=_clean_info(info.get("/Author")),
    )
