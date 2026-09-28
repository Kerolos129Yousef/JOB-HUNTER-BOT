"""Parse LinkedIn Job Alert email HTML into structured Job objects.

LinkedIn's alert email is a table-based HTML layout. Each job is a link whose
href contains ``/jobs/view/<numeric-id>``. The anchor text is the job title;
the company and location live in the surrounding cell as short text lines.

This parsing is heuristic (LinkedIn changes its markup periodically), so it is
written defensively: if company/location can't be found we still emit the job
with its title and a clean link, which is the part that actually matters.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .models import Job

log = logging.getLogger(__name__)

_JOB_ID_RE = re.compile(r"/jobs/view/(\d+)")
# Boilerplate anchor texts we never want to treat as a job title.
_NON_TITLE = {
    "view job", "see all jobs", "view all", "unsubscribe", "apply",
    "see more jobs", "view more", "linkedin",
}


def _job_id(href: str) -> str | None:
    match = _JOB_ID_RE.search(href or "")
    return match.group(1) if match else None


def _clean_url(job_id: str) -> str:
    """A stable, tracking-free link we can safely share."""
    return f"https://www.linkedin.com/jobs/view/{job_id}/"


def _ancestor_lines(anchor: Tag, max_up: int = 5) -> list[str]:
    """Walk up from the anchor to find a container with title + company + loc.

    Returns the container's text as a list of non-empty lines.
    """
    node: Tag | None = anchor
    best: list[str] = []
    for _ in range(max_up):
        node = node.parent if isinstance(node, Tag) else None
        if node is None:
            break
        text = node.get_text("\n", strip=True)
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        # A good container has a few lines (title, company, location) but is
        # not the whole email body. Stop at the first one that looks right.
        if 2 <= len(lines) <= 6:
            return lines
        best = lines  # remember the last non-empty thing we saw
    return best


def parse_jobs(html: str) -> list[Job]:
    """Extract a de-duplicated list of Jobs from one alert email's HTML."""
    soup = BeautifulSoup(html, "html.parser")
    by_id: dict[str, Job] = {}

    for anchor in soup.find_all("a", href=True):
        job_id = _job_id(anchor["href"])
        if not job_id:
            continue

        title = anchor.get_text(" ", strip=True)
        if not title or title.lower() in _NON_TITLE:
            # This anchor (e.g. a logo image link) points at the job but has no
            # usable title. Keep a placeholder only if we have nothing better.
            if job_id not in by_id:
                by_id[job_id] = Job(job_id, "(untitled)", "", "", _clean_url(job_id))
            continue

        company, location = _company_and_location(anchor, title)
        job = Job(job_id, title, company, location, _clean_url(job_id))

        existing = by_id.get(job_id)
        # Prefer the entry with the most information (real title beats logo link).
        if existing is None or _score(job) > _score(existing):
            by_id[job_id] = job

    jobs = list(by_id.values())
    log.info("Parsed %d unique job(s) from email", len(jobs))
    return jobs


def _company_and_location(anchor: Tag, title: str) -> tuple[str, str]:
    lines = _ancestor_lines(anchor)
    # Drop the title line and obvious boilerplate, keep order.
    rest = [
        ln for ln in lines
        if ln != title and ln.lower() not in _NON_TITLE and not ln.startswith("http")
    ]
    company = rest[0] if len(rest) >= 1 else ""
    location = rest[1] if len(rest) >= 2 else ""
    return company, location


def _score(job: Job) -> int:
    """How complete a job record is — used to keep the richest duplicate."""
    score = 0
    if job.title and job.title != "(untitled)":
        score += 2
    if job.company:
        score += 1
    if job.location:
        score += 1
    return score
