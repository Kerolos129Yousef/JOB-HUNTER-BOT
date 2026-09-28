"""SQLite-backed store of jobs we have already sent, to avoid duplicates."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime

from .models import Job

log = logging.getLogger(__name__)


class SeenStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                job_id     TEXT PRIMARY KEY,
                title      TEXT,
                company    TEXT,
                location   TEXT,
                url        TEXT,
                sent_at    TEXT
            )
            """
        )
        self._conn.commit()

    def is_seen(self, job_id: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,)
        )
        return cur.fetchone() is not None

    def mark_sent(self, job: Job) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO seen_jobs
                (job_id, title, company, location, url, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id,
                job.title,
                job.company,
                job.location,
                job.url,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self._conn.commit()

    def new_jobs(self, jobs: list[Job]) -> list[Job]:
        """Return only the jobs we have never sent before."""
        return [j for j in jobs if not self.is_seen(j.job_id)]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SeenStore":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
