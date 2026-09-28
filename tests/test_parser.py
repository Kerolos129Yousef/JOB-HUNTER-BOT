"""Basic sanity tests for parsing + filtering (no network, no Gmail needed).

Run:  python -m pytest -q     (or)     python tests/test_parser.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.filters import filter_jobs  # noqa: E402
from src.parser import parse_jobs  # noqa: E402

# A trimmed-down version of a LinkedIn Job Alert email body.
SAMPLE_HTML = """
<html><body>
<table>
  <tr><td>
    <a href="https://www.linkedin.com/comm/jobs/view/3812345678/?trk=eml-abc">
      Senior DevOps Engineer
    </a>
    <div>Acme Cloud</div>
    <div>Cairo, Egypt (Remote)</div>
  </td></tr>
  <tr><td>
    <a href="https://www.linkedin.com/comm/jobs/view/3899999999/?trk=eml-xyz">
      Site Reliability Engineer (SRE)
    </a>
    <div>Globex</div>
    <div>Remote</div>
  </td></tr>
  <tr><td>
    <a href="https://www.linkedin.com/comm/jobs/view/3700000000/?trk=eml-qqq">
      Marketing Manager
    </a>
    <div>Initech</div>
    <div>Dubai</div>
  </td></tr>
</table>
</body></html>
"""


def test_parse_extracts_jobs():
    jobs = parse_jobs(SAMPLE_HTML)
    ids = {j.job_id for j in jobs}
    assert ids == {"3812345678", "3899999999", "3700000000"}, ids
    devops = next(j for j in jobs if j.job_id == "3812345678")
    assert devops.title == "Senior DevOps Engineer"
    assert devops.url == "https://www.linkedin.com/jobs/view/3812345678/"
    print("OK: parsed", len(jobs), "jobs")


def test_keyword_filter():
    jobs = parse_jobs(SAMPLE_HTML)
    kept = filter_jobs(
        jobs,
        keywords=["devops", "sre", "site reliability", "platform engineer"],
        exclude=["manager"],
    )
    titles = sorted(j.title for j in kept)
    assert titles == ["Senior DevOps Engineer", "Site Reliability Engineer (SRE)"], titles
    print("OK: kept", titles)


if __name__ == "__main__":
    test_parse_extracts_jobs()
    test_keyword_filter()
    print("\nAll tests passed ✅")
