from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    JOB_STARTED = "job.started"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    PROGRESS = "progress"
    PAPER_INDEXED = "paper.indexed"
    SECTION_PLANNED = "section.planned"
    SOURCE_FOUND = "source.found"
    SECTION_DRAFTED = "section.drafted"
    CLAIM_CHECKED = "claim.checked"
    WARNING = "warning"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"


TERMINAL_EVENTS = frozenset({EventType.JOB_COMPLETED, EventType.JOB_FAILED, EventType.JOB_CANCELLED})


class Stage(StrEnum):
    INDEXING = "indexing"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    WRITING = "writing"
    VERIFYING = "verifying"
    ASSEMBLING = "assembling"


class JobEvent(BaseModel):
    seq: int = 0
    job_id: str = ""
    type: EventType
    stage: Stage | None = None
    message: str
    progress: float | None = Field(default=None, ge=0, le=1)
    data: dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_terminal(self) -> bool:
        return self.type in TERMINAL_EVENTS

    def to_ndjson(self) -> str:
        return self.model_dump_json() + "\n"
