from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from cip_contracts.library import Author, Passage


class Verdict(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REMOVED = "removed"


class Length(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class CitationLink(BaseModel):
    passage_id: str
    paper_id: str
    page: int


class Claim(BaseModel):
    claim_id: str
    text: str
    citations: list[CitationLink] = Field(default_factory=list)
    verdict: Verdict = Verdict.UNSUPPORTED
    rationale: str = ""
    review: ReviewStatus = ReviewStatus.PENDING

    @property
    def needs_review(self) -> bool:
        return self.verdict != Verdict.SUPPORTED and self.review == ReviewStatus.PENDING

    @property
    def is_visible(self) -> bool:
        return self.review != ReviewStatus.REMOVED


class Paragraph(BaseModel):
    claims: list[Claim] = Field(default_factory=list)


class Section(BaseModel):
    section_id: str
    heading: str
    paragraphs: list[Paragraph] = Field(default_factory=list)

    def claims(self) -> list[Claim]:
        return [claim for paragraph in self.paragraphs for claim in paragraph.claims]


class Reference(BaseModel):
    key: str
    paper_id: str
    authors: list[Author] = Field(default_factory=list)
    year: int | None = None
    title: str | None = None
    journal: str | None = None
    doi: str | None = None
    file_name: str = ""


class DraftStats(BaseModel):
    claims: int = 0
    supported: int = 0
    partial: int = 0
    unsupported: int = 0
    pending_review: int = 0
    sources: int = 0


class DraftOptions(BaseModel):
    length: Length = Length.MEDIUM
    language: str = "es"
    citation_style: str = "apa"
    year_from: int | None = None


class DraftRequest(BaseModel):
    library_id: str
    prompt: str = Field(min_length=10, max_length=2000)
    options: DraftOptions = Field(default_factory=DraftOptions)


class Draft(BaseModel):
    draft_id: str
    library_id: str
    prompt: str
    title: str
    language: str = "es"
    sections: list[Section] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    evidence: dict[str, Passage] = Field(default_factory=dict)
    models: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def claims(self) -> list[Claim]:
        return [claim for section in self.sections for claim in section.claims()]

    def find_claim(self, claim_id: str) -> Claim | None:
        return next((claim for claim in self.claims() if claim.claim_id == claim_id), None)

    @property
    def stats(self) -> DraftStats:
        visible = [claim for claim in self.claims() if claim.is_visible]
        return DraftStats(
            claims=len(visible),
            supported=sum(claim.verdict == Verdict.SUPPORTED for claim in visible),
            partial=sum(claim.verdict == Verdict.PARTIAL for claim in visible),
            unsupported=sum(claim.verdict == Verdict.UNSUPPORTED for claim in visible),
            pending_review=sum(claim.needs_review for claim in visible),
            sources=len(self.references),
        )


class ClaimAction(StrEnum):
    ACCEPT = "accept"
    REMOVE = "remove"
    RESTORE = "restore"
    EDIT = "edit"


class ClaimReview(BaseModel):
    action: ClaimAction
    text: str | None = None


class ExportFormat(StrEnum):
    DOCX = "docx"
    MARKDOWN = "md"
    BIBTEX = "bib"


class RenderRequest(BaseModel):
    draft: Draft
    format: ExportFormat = ExportFormat.DOCX
    include_review_comments: bool = True
