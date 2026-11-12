from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SectionOutline(StrictModel):
    heading: str = Field(description="Section heading in the requested language")
    goal: str = Field(description="One sentence describing what the section must establish")
    queries: list[str] = Field(description="Two or three precise English search queries for the PDF library")


class PlanOutput(StrictModel):
    title: str
    sections: list[SectionOutline]


class DraftedSentence(StrictModel):
    text: str = Field(description="One sentence, without author names or years")
    evidence: list[str] = Field(description="Evidence ids that support the sentence, e.g. E1")


class DraftedParagraph(StrictModel):
    sentences: list[DraftedSentence]


class SectionDraftOutput(StrictModel):
    paragraphs: list[DraftedParagraph]


class ClaimJudgment(StrictModel):
    claim_id: str
    verdict: Literal["supported", "partial", "unsupported"]
    rationale: str = Field(description="Empty when supported; otherwise what is missing or wrong")


class VerificationOutput(StrictModel):
    judgments: list[ClaimJudgment]


class RepairedClaim(StrictModel):
    claim_id: str
    action: Literal["rewrite", "drop"]
    text: str = Field(description="Rewritten sentence, empty when dropped")
    evidence: list[str]


class RepairOutput(StrictModel):
    claims: list[RepairedClaim]


class SectionPlan(BaseModel):
    section_id: str
    heading: str
    goal: str
    queries: list[str]


class EvidenceItem(BaseModel):
    label: str
    citation: str
    page: int
    text: str


class ClaimToCheck(BaseModel):
    claim_id: str
    text: str
    evidence: list[EvidenceItem]
