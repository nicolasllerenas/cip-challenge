from enum import StrEnum

from pydantic import BaseModel, Field


class PaperStatus(StrEnum):
    INDEXED = "indexed"
    NEEDS_OCR = "needs_ocr"
    FAILED = "failed"


class Author(BaseModel):
    family: str
    given: str = ""

    @property
    def initials(self) -> str:
        return " ".join(f"{part[0]}." for part in self.given.replace("-", " ").split() if part)


class PaperMetadata(BaseModel):
    title: str | None = None
    authors: list[Author] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    journal: str | None = None

    @property
    def missing_fields(self) -> list[str]:
        required = {"title": self.title, "authors": self.authors, "year": self.year}
        return [name for name, value in required.items() if not value]


class Paper(BaseModel):
    paper_id: str
    library_id: str
    file_name: str
    file_path: str
    pages: int = 0
    status: PaperStatus
    metadata: PaperMetadata = Field(default_factory=PaperMetadata)
    issues: list[str] = Field(default_factory=list)


class LibraryCounts(BaseModel):
    total: int = 0
    indexed: int = 0
    needs_ocr: int = 0
    failed: int = 0
    incomplete_metadata: int = 0


class LibrarySummary(BaseModel):
    library_id: str
    path: str
    counts: LibraryCounts
    papers: list[Paper] = Field(default_factory=list)


class CreateLibraryRequest(BaseModel):
    path: str


class MetadataPatch(BaseModel):
    title: str | None = None
    authors: list[Author] | None = None
    year: int | None = None
    doi: str | None = None
    journal: str | None = None


class Passage(BaseModel):
    passage_id: str
    paper_id: str
    page: int
    text: str
    score: float = 0.0
    file_name: str = ""
    file_path: str = ""
    metadata: PaperMetadata = Field(default_factory=PaperMetadata)


class SearchRequest(BaseModel):
    queries: list[str] = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)
    per_paper: int = Field(default=2, ge=1, le=10)
    year_from: int | None = None
