"""Keyword filtering for jobs."""
from __future__ import annotations

import logging

from .models import Job

log = logging.getLogger(__name__)


def matches(job: Job, keywords: list[str], exclude: list[str]) -> bool:
    """True if the job title matches an include keyword and no exclude keyword.

    Matching is case-insensitive substring matching on the title. If the title
    is missing we fall back to matching against company text too, so we don't
    silently drop jobs whose title failed to parse.
    """
    haystack = job.title.lower()
    if not haystack or haystack == "(untitled)":
        haystack = job.company.lower()

    if exclude and any(word in haystack for word in exclude):
        return False

    if not keywords:
        return True  # no filter configured -> keep everything

    return any(word in haystack for word in keywords)


def filter_jobs(
    jobs: list[Job], keywords: list[str], exclude: list[str]
) -> list[Job]:
    kept = [j for j in jobs if matches(j, keywords, exclude)]
    log.info("Kept %d/%d job(s) after keyword filter", len(kept), len(jobs))
    return kept
