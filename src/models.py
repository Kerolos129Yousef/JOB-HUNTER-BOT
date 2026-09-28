"""Shared data types."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Job:
    job_id: str            # LinkedIn numeric job id (from /jobs/view/<id>) — used for dedup
    title: str
    company: str
    location: str
    url: str               # clean https://www.linkedin.com/jobs/view/<id> link

    def __post_init__(self) -> None:
        self.title = (self.title or "").strip()
        self.company = (self.company or "").strip()
        self.location = (self.location or "").strip()
