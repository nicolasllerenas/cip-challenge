import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from cip_contracts import LibraryCounts, Paper, PaperMetadata, PaperStatus, Passage

from cip_library.chunking import Chunk

SCHEMA = """
CREATE TABLE IF NOT EXISTS libraries (
    library_id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL REFERENCES libraries ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    pages INTEGER NOT NULL,
    status TEXT NOT NULL,
    metadata TEXT NOT NULL,
    issues TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    rowid INTEGER PRIMARY KEY,
    passage_id TEXT UNIQUE NOT NULL,
    paper_id TEXT NOT NULL REFERENCES papers ON DELETE CASCADE,
    library_id TEXT NOT NULL,
    page INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_by_library ON chunks (library_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='chunks', content_rowid='rowid', tokenize='porter unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS chunks_after_insert AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, text) VALUES (new.rowid, new.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_after_delete AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
END;
"""

PASSAGE_COLUMNS = "c.passage_id, c.paper_id, c.page, c.text, p.file_name, p.file_path, p.metadata"


def _year_allowed(metadata: PaperMetadata, year_from: int | None) -> bool:
    return year_from is None or metadata.year is None or metadata.year >= year_from


class LibraryStore:
    def __init__(self, database: Path) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self._database = database
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def upsert_library(self, library_id: str, path: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO libraries VALUES (?, ?, ?)",
                (library_id, path, datetime.now(UTC).isoformat()),
            )

    def library_path(self, library_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT path FROM libraries WHERE library_id = ?", (library_id,)).fetchone()
        return row["path"] if row else None

    def fingerprints(self, library_id: str) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT paper_id, fingerprint FROM papers WHERE library_id = ?", (library_id,)
            ).fetchall()
        return {row["paper_id"]: row["fingerprint"] for row in rows}

    def save_paper(self, paper: Paper, fingerprint: str, chunks: list[Chunk], vectors: np.ndarray) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE paper_id = ?", (paper.paper_id,))
            connection.execute(
                "INSERT OR REPLACE INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    paper.paper_id,
                    paper.library_id,
                    paper.file_name,
                    paper.file_path,
                    fingerprint,
                    paper.pages,
                    paper.status.value,
                    paper.metadata.model_dump_json(),
                    json.dumps(paper.issues, ensure_ascii=False),
                ),
            )
            connection.executemany(
                "INSERT INTO chunks (passage_id, paper_id, library_id, page, text, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        f"{paper.paper_id}:{chunk.ordinal}",
                        paper.paper_id,
                        paper.library_id,
                        chunk.page,
                        chunk.text,
                        vector.astype(np.float32).tobytes(),
                    )
                    for chunk, vector in zip(chunks, vectors, strict=True)
                ],
            )

    def remove_missing(self, library_id: str, present: set[str]) -> None:
        stale = set(self.fingerprints(library_id)) - present
        with self._connect() as connection:
            for paper_id in stale:
                connection.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
                connection.execute("DELETE FROM papers WHERE paper_id = ?", (paper_id,))

    def _paper(self, row: sqlite3.Row) -> Paper:
        return Paper(
            paper_id=row["paper_id"],
            library_id=row["library_id"],
            file_name=row["file_name"],
            file_path=row["file_path"],
            pages=row["pages"],
            status=PaperStatus(row["status"]),
            metadata=PaperMetadata.model_validate_json(row["metadata"]),
            issues=json.loads(row["issues"]),
        )

    def list_papers(self, library_id: str) -> list[Paper]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM papers WHERE library_id = ? ORDER BY file_name", (library_id,)
            ).fetchall()
        return [self._paper(row) for row in rows]

    def get_paper(self, paper_id: str) -> Paper | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
        return self._paper(row) if row else None

    def update_paper(self, paper: Paper) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE papers SET metadata = ?, issues = ? WHERE paper_id = ?",
                (
                    paper.metadata.model_dump_json(),
                    json.dumps(paper.issues, ensure_ascii=False),
                    paper.paper_id,
                ),
            )

    def counts(self, library_id: str) -> LibraryCounts:
        papers = self.list_papers(library_id)
        return LibraryCounts(
            total=len(papers),
            indexed=sum(paper.status == PaperStatus.INDEXED for paper in papers),
            needs_ocr=sum(paper.status == PaperStatus.NEEDS_OCR for paper in papers),
            failed=sum(paper.status == PaperStatus.FAILED for paper in papers),
            incomplete_metadata=sum(
                bool(paper.metadata.missing_fields) for paper in papers if paper.status == PaperStatus.INDEXED
            ),
        )

    def lexical_search(self, library_id: str, match_query: str, limit: int) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT c.passage_id FROM chunks_fts JOIN chunks c ON c.rowid = chunks_fts.rowid "
                "WHERE chunks_fts MATCH ? AND c.library_id = ? ORDER BY bm25(chunks_fts) LIMIT ?",
                (match_query, library_id, limit),
            ).fetchall()
        return [row["passage_id"] for row in rows]

    def vectors(self, library_id: str) -> tuple[list[str], np.ndarray]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT passage_id, embedding FROM chunks WHERE library_id = ? ORDER BY rowid", (library_id,)
            ).fetchall()
        if not rows:
            return [], np.zeros((0, 0), dtype=np.float32)
        return [row["passage_id"] for row in rows], np.vstack(
            [np.frombuffer(row["embedding"], dtype=np.float32) for row in rows]
        )

    def passages(self, passage_ids: list[str], year_from: int | None = None) -> list[Passage]:
        if not passage_ids:
            return []
        placeholders = ",".join("?" * len(passage_ids))
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT {PASSAGE_COLUMNS} FROM chunks c JOIN papers p ON p.paper_id = c.paper_id "
                f"WHERE c.passage_id IN ({placeholders})",
                passage_ids,
            ).fetchall()
        by_id = {
            row["passage_id"]: Passage(
                passage_id=row["passage_id"],
                paper_id=row["paper_id"],
                page=row["page"],
                text=row["text"],
                file_name=row["file_name"],
                file_path=row["file_path"],
                metadata=PaperMetadata.model_validate_json(row["metadata"]),
            )
            for row in rows
        }
        ordered = (by_id[passage_id] for passage_id in passage_ids if passage_id in by_id)
        return [passage for passage in ordered if _year_allowed(passage.metadata, year_from)]
