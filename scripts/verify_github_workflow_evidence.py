"""Independently verify CI evidence in a deployment evidence bundle against GitHub Actions.

This checks GitHub's run metadata and actual job conclusions; it does not verify runtime,
tenant ownership, provider receipts, or production safety.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

EXPECTED_JOB_IDS = {
    "KMH OIA Tests": "tests",
    "KMH OIA Performance Evidence": "performance-evidence",
    "KMH OIA Repository Validation": "repository-validation",
}
RUN_URL_RE = re.compile(r"^/([^/]+)/([^/]+)/actions/runs/([0-9]+)/?$")


def _json_request(url: str, token: str | None, opener: Callable[..., Any]) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "kmh-oia-evidence-verifier",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with opener(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("GitHub API response must be a JSON object")
    return data


def verify_bundle(
    bundle: dict[str, Any],
    repository: str,
    *,
    token: str | None = None,
    api_base: str = "https://api.github.com",
    opener: Callable[..., Any] = urlopen,
) -> list[str]:
    """Return errors; an empty list means GitHub-backed CI evidence checks passed."""
    errors: list[str] = []
    commit_sha = bundle.get("bundle_commit_sha")
    # For pull_request events, the tested merge commit and API run head SHA differ.
    source_head_sha = bundle.get("source_head_sha", commit_sha)
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", commit_sha):
        errors.append("bundle_commit_sha must be a full 40-character Git commit SHA")
        return errors
    if not isinstance(source_head_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", source_head_sha):
        errors.append("source_head_sha must be a full 40-character Git commit SHA")
        return errors

    gates = bundle.get("gates")
    if not isinstance(gates, list):
        return ["bundle gates must be a list"]
    ci_gate = next(
        (gate for gate in gates if isinstance(gate, dict) and gate.get("gate") == "repository_ci_for_bundle_commit"),
        None,
    )
    if not isinstance(ci_gate, dict):
        return ["repository_ci_for_bundle_commit gate is missing"]
    rows = ci_gate.get("evidence")
    if not isinstance(rows, list) or not rows:
        return ["CI evidence rows are missing"]

    parsed_rows: list[tuple[dict[str, Any], str, str]] = []
    unique_runs: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"CI evidence row {index} must be an object")
            continue
        name = row.get("name")
        url = row.get("url")
        row_sha = row.get("head_sha")
        if not isinstance(name, str) or name not in EXPECTED_JOB_IDS:
            errors.append(f"CI evidence row {index} has an unknown job name: {name!r}")
            continue
        if not isinstance(url, str):
            errors.append(f"CI evidence row {index} URL is missing")
            continue
        parsed = urlparse(url)
        match = RUN_URL_RE.fullmatch(parsed.path)
        if parsed.scheme != "https" or parsed.netloc != "github.com" or not match:
            errors.append(f"CI evidence row {index} URL is not a canonical GitHub Actions run URL")
            continue
        owner, repo, run_id = match.groups()
        if f"{owner}/{repo}".lower() != repository.lower():
            errors.append(f"CI evidence row {index} URL repository does not match {repository}")
            continue
        if row_sha != commit_sha:
            errors.append(f"CI evidence row {index} head_sha does not match bundle commit")
        parsed_rows.append((row, run_id, EXPECTED_JOB_IDS[name]))
        unique_runs.setdefault(run_id, {"url": url})

    if errors:
        return errors

    api_root = api_base.rstrip("/")
    run_cache: dict[str, dict[str, Any]] = {}
    jobs_cache: dict[str, list[dict[str, Any]]] = {}
    for run_id, data in unique_runs.items():
        try:
            run = _json_request(
                f"{api_root}/repos/{repository}/actions/runs/{run_id}", token, opener
            )
            jobs_response = _json_request(
                f"{api_root}/repos/{repository}/actions/runs/{run_id}/jobs?per_page=100",
                token,
                opener,
            )
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            errors.append(f"GitHub API verification failed for run {run_id}: {type(exc).__name__}")
            continue

        run_cache[run_id] = run
        jobs = jobs_response.get("jobs")
        if not isinstance(jobs, list):
            errors.append(f"GitHub API jobs response for run {run_id} is malformed")
            continue
        jobs_cache[run_id] = [job for job in jobs if isinstance(job, dict)]

        if run.get("head_sha") != source_head_sha:
            errors.append(f"GitHub run {run_id} head_sha does not match bundle commit")
        if run.get("repository", {}).get("full_name", "").lower() != repository.lower():
            errors.append(f"GitHub run {run_id} repository identity does not match")
        expected_url = unique_runs[run_id]["url"].rstrip("/")
        actual_url = str(run.get("html_url", "")).rstrip("/")
        if actual_url != expected_url:
            errors.append(f"GitHub run {run_id} html_url does not match evidence URL")

    for row, run_id, expected_job_id in parsed_rows:
        if run_id not in jobs_cache:
            continue
        job = next(
            (candidate for candidate in jobs_cache[run_id]
             if candidate.get("name") == expected_job_id or candidate.get("id") == expected_job_id),
            None,
        )
        if job is None:
            errors.append(f"GitHub run {run_id} is missing expected job {expected_job_id}")
            continue
        if job.get("status") != "completed":
            errors.append(f"GitHub job {expected_job_id} is not completed")
        if job.get("conclusion") != row.get("conclusion"):
            errors.append(f"GitHub job {expected_job_id} conclusion does not match evidence")
        if job.get("head_sha") and job.get("head_sha") != source_head_sha:
            errors.append(f"GitHub job {expected_job_id} head_sha does not match bundle commit")
        if row.get("is_required_check") is True and job.get("conclusion") != "success":
            errors.append(f"Required GitHub job {expected_job_id} did not succeed")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repository", default="thuyainminnyo-hub/kmh-oia")
    parser.add_argument("--api-base", default="https://api.github.com")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be a JSON object")
        errors = verify_bundle(bundle, args.repository, token=os.environ.get("GITHUB_TOKEN"), api_base=args.api_base)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Evidence verification input error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("Independent GitHub CI evidence verification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Independent GitHub CI evidence verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
