"""Capture CI prerequisite receipts and diagnostics without hiding missing evidence."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


JOB_FIELDS = (
    ("KMH OIA Tests", "tests"),
    ("KMH OIA Performance Evidence", "performance"),
    ("KMH OIA Repository Validation", "repository"),
)
VALID_RESULTS = {"success", "failure", "cancelled", "skipped"}


def capture_ci_evidence(values: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return receipt rows plus diagnostics; preserve evidence even when invalid."""
    errors: list[str] = []
    url = values.get("url", "")
    head_sha = values.get("head_sha", "")
    bundle_sha = values.get("bundle_sha", "")

    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or not re.fullmatch(r"/[^/]+/[^/]+/actions/runs/[0-9]+", parsed.path)
    ):
        errors.append("url must be a GitHub HTTPS Actions run URL")
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        errors.append("head_sha must be a full 40-character lowercase commit SHA")
    if not re.fullmatch(r"[0-9a-f]{40}", bundle_sha):
        errors.append("bundle_sha must be a full 40-character lowercase commit SHA")
    if head_sha != bundle_sha:
        errors.append("head_sha must match bundle_sha")

    rows: list[dict[str, Any]] = []
    for name, key in JOB_FIELDS:
        conclusion = values.get(key, "")
        if conclusion not in VALID_RESULTS:
            errors.append(f"{key} result is missing or unrecognized")
            if not conclusion:
                conclusion = "NOT_VERIFIED"
        rows.append(
            {
                "name": name,
                "url": url,
                "head_sha": head_sha,
                "conclusion": conclusion,
                "is_required_check": True,
            }
        )

    diagnostics = {
        "schema_version": "1.0",
        "capture_status": "CAPTURED_WITH_ERRORS" if errors else "CAPTURED",
        "inputs": {
            "url_present": bool(url),
            "head_sha_present": bool(head_sha),
            "bundle_sha_present": bool(bundle_sha),
            "prerequisite_results": {
                key: values.get(key, "") or "MISSING"
                for _, key in JOB_FIELDS
            },
        },
        "validation_errors": errors,
    }
    return rows, diagnostics


def main() -> int:
    values = {
        "url": os.environ.get("CI_RUN_URL", ""),
        "head_sha": os.environ.get("CI_HEAD_SHA", ""),
        "bundle_sha": os.environ.get("BUNDLE_COMMIT_SHA", ""),
        "tests": os.environ.get("TESTS_RESULT", ""),
        "performance": os.environ.get("PERFORMANCE_RESULT", ""),
        "repository": os.environ.get("REPOSITORY_RESULT", ""),
    }
    rows, diagnostics = capture_ci_evidence(values)
    Path("deployment-ci-runs.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )
    Path("validation-diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    # Do not fail here: preserve receipts and allow the downstream exact-SHA
    # validator to fail closed. The job still fails if required evidence is bad.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
