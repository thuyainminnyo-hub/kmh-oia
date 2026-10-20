"""Capture a fail-closed target-host evidence receipt.

Run this on the intended deployment host from the exact checkout being tested.
This tool does not independently prove a mount is persistent: an operator must
inspect the actual storage configuration and explicitly confirm it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from scripts.production_replay_smoke import smoke_test


SHA_RE = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


def resolve_checkout_sha(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Cannot determine current checkout commit SHA") from exc
    sha = result.stdout.strip()
    if not SHA_RE.fullmatch(sha):
        raise RuntimeError("Current checkout did not return a full Git commit SHA")
    return sha.lower()


def capture_target_evidence(
    *,
    db_path: Path,
    environment_id: str,
    host_or_service_id: str,
    persistent_volume_confirmed: bool,
    expected_commit_sha: str,
    repo_root: Path,
) -> dict[str, object]:
    if not environment_id.strip():
        raise ValueError("environment_id must not be empty")
    if not host_or_service_id.strip():
        raise ValueError("host_or_service_id must not be empty")
    if persistent_volume_confirmed is not True:
        raise ValueError("Persistent-volume confirmation is required; do not guess")
    if not SHA_RE.fullmatch(expected_commit_sha):
        raise ValueError("expected_commit_sha must be a full 40- or 64-character Git SHA")

    actual_sha = resolve_checkout_sha(repo_root)
    expected_sha = expected_commit_sha.lower()
    if actual_sha != expected_sha:
        raise ValueError(
            f"Checkout SHA mismatch: expected {expected_sha}, found {actual_sha}"
        )

    report = smoke_test(db_path)
    if report.get("result") != "PASS":
        raise RuntimeError(f"Target-host smoke test did not pass: {report.get('result')}")

    # Use the end of the smoke run as its timestamp, with explicit UTC offset.
    tested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "environment_id": environment_id.strip(),
        "host_or_service_id": host_or_service_id.strip(),
        "persistent_volume_confirmed": True,
        "database_path": str(db_path),
        "smoke_test_report": report,
        "smoke_tested_at_utc": tested_at,
        "commit_sha": actual_sha,
        "capture_schema_version": "1.0",
        "operator_confirmation_scope": (
            "Operator asserted persistent storage after independently inspecting the target mount; "
            "this script does not verify storage-platform configuration."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--host-or-service-id", required=True)
    parser.add_argument("--expected-commit-sha", required=True)
    parser.add_argument(
        "--confirm-persistent-volume",
        action="store_true",
        help="Confirm only after independently checking the actual target mount/volume",
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        evidence = capture_target_evidence(
            db_path=args.db_path,
            environment_id=args.environment_id,
            host_or_service_id=args.host_or_service_id,
            persistent_volume_confirmed=args.confirm_persistent_volume,
            expected_commit_sha=args.expected_commit_sha,
            repo_root=args.repo_root,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"target evidence capture failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "output": str(args.output),
        "result": evidence["smoke_test_report"]["result"],
        "commit_sha": evidence["commit_sha"],
        "smoke_tested_at_utc": evidence["smoke_tested_at_utc"],
        "persistent_volume_confirmed": evidence["persistent_volume_confirmed"],
        "next_gate": "operator-confirmed local host receipt only; external outcome/provider remain separate",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
