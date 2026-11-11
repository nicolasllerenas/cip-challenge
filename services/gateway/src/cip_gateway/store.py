import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from cip_contracts import Draft, DraftStats, EventType, JobEvent
from pydantic import BaseModel

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    job_id TEXT NOT NULL REFERENCES jobs ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (job_id, seq)
);
CREATE TABLE IF NOT EXISTS drafts (
    draft_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

STATUS_BY_EVENT = {
    EventType.JOB_COMPLETED: "completed",
    EventType.JOB_FAILED: "failed",
    EventType.JOB_CANCELLED: "cancelled",
}


class JobKind(StrEnum):
    INGESTION = "ingestion"
    DRAFT = "draft"


class Job(BaseModel):
    job_id: str
    kind: JobKind
    subject_id: str
    status: str
    message: str
    created_at: datetime
    last_seq: int = 0


class DraftSummary(BaseModel):
    draft_id: str
    job_id: str
    title: str
    created_at: datetime
    stats: DraftStats


def now() -> str:
    return datetime.now(UTC).isoformat()


class GatewayStore:
    def __init__(self, database: Path) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self._database = database
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def interrupted_jobs(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT job_id FROM jobs WHERE status = 'running'").fetchall()
        return [row["job_id"] for row in rows]

    def create_job(self, kind: JobKind, subject_id: str) -> Job:
        job = Job(
            job_id=uuid4().hex,
            kind=kind,
            subject_id=subject_id,
            status="running",
            message="",
            created_at=datetime.now(UTC),
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?)",
                (job.job_id, job.kind.value, job.subject_id, job.status, job.message, job.created_at.isoformat()),
            )
        return job

    def job(self, job_id: str) -> Job | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT j.*, COALESCE(MAX(e.seq), 0) AS last_seq FROM jobs j "
                "LEFT JOIN events e ON e.job_id = j.job_id WHERE j.job_id = ? GROUP BY j.job_id",
                (job_id,),
            ).fetchone()
        return Job.model_validate(dict(row)) if row else None

    def append_event(self, job_id: str, event: JobEvent) -> JobEvent:
        with self._connect() as connection:
            seq = connection.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE job_id = ?", (job_id,)
            ).fetchone()[0]
            stored = event.model_copy(update={"seq": seq, "job_id": job_id})
            connection.execute("INSERT INTO events VALUES (?, ?, ?)", (job_id, seq, stored.model_dump_json()))
            status = STATUS_BY_EVENT.get(event.type, "running")
            connection.execute(
                "UPDATE jobs SET status = ?, message = ? WHERE job_id = ?", (status, event.message, job_id)
            )
        return stored

    def events(self, job_id: str, after: int = 0) -> list[JobEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM events WHERE job_id = ? AND seq > ? ORDER BY seq", (job_id, after)
            ).fetchall()
        return [JobEvent.model_validate_json(row["payload"]) for row in rows]

    def save_draft(self, job_id: str, draft: Draft) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO drafts VALUES (?, ?, ?, ?, ?, ?)",
                (draft.draft_id, job_id, draft.title, draft.model_dump_json(), draft.created_at.isoformat(), now()),
            )

    def update_draft(self, draft: Draft) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE drafts SET payload = ?, updated_at = ? WHERE draft_id = ?",
                (draft.model_dump_json(), now(), draft.draft_id),
            )

    def draft(self, draft_id: str) -> Draft | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM drafts WHERE draft_id = ?", (draft_id,)).fetchone()
        return Draft.model_validate_json(row["payload"]) if row else None

    def drafts(self) -> list[DraftSummary]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM drafts ORDER BY created_at DESC").fetchall()
        return [
            DraftSummary(
                draft_id=row["draft_id"],
                job_id=row["job_id"],
                title=row["title"],
                created_at=row["created_at"],
                stats=Draft.model_validate(json.loads(row["payload"])).stats,
            )
            for row in rows
        ]
