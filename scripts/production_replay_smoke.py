"""Local deployment smoke test for the durable SQLite replay gate.

Run on the intended deployment host after providing a persistent file path:
    python scripts/production_replay_smoke.py --db-path /var/lib/kmh-oia/evidence-replay.sqlite3

This command is deliberately explicit and will fail if the path does not
already exist, avoiding accidental creation of a database on the wrong volume.
The smoke test uses independent OS processes and a unique receipt ID. It
verifies that the store remains healthy and rejects a duplicate claim. It does
not verify a real external provider or the whole application deployment.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


CHILD_PROGRAM = r"""
import json
import sys
from src.receipt_replay_store import SQLiteReceiptReplayStore

store = SQLiteReceiptReplayStore(sys.argv[1])
claim = store.claim(sys.argv[2], sys.argv[3], sys.argv[4])
print(json.dumps({
    "accepted": claim.accepted,
    "reason": claim.reason,
    "healthy": store.health_check(),
}, sort_keys=True))
"""


def run_claim(db_path: Path, provider: str, record_id: str, content_hash: str) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    completed = subprocess.run(
        [sys.executable, "-c", CHILD_PROGRAM, str(db_path), provider, record_id, content_hash],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    result = json.loads(completed.stdout)
    if not isinstance(result, dict):
        raise RuntimeError("Child process returned an invalid result shape")
    return result


def smoke_test(db_path: Path) -> dict[str, object]:
    if not db_path.exists() or not db_path.is_file():
        raise FileNotFoundError(
            f"Database path must already exist on the intended persistent volume: {db_path}"
        )
    # Random per-run ID prevents the smoke test from colliding with previous
    # checks or actual provider receipts.
    suffix = uuid.uuid4().hex
    provider = "kmh-oia-deployment-smoke"
    record_id = f"smoke:{suffix}"
    content_hash = f"sha256:smoke:{suffix}"

    first = run_claim(db_path, provider, record_id, content_hash)
    second = run_claim(db_path, provider, record_id, content_hash)
    passed = (
        first.get("healthy") is True
        and first.get("accepted") is True
        and second.get("healthy") is True
        and second.get("accepted") is False
        and "replay" in str(second.get("reason", "")).lower()
    )
    return {
        "schema_version": "1.0",
        "test": "sqlite_replay_across_independent_os_processes",
        "db_path": str(db_path),
        "first_process": first,
        "second_process": second,
        "result": "PASS" if passed else "FAIL",
        "scope": "SQLite file health and duplicate-replay rejection across local OS processes only",
        "limitations": [
            "Does not authenticate a real external provider.",
            "Does not prove the database path belongs to a configured persistent volume beyond operator-supplied path.",
            "Does not prove multi-host or distributed-store behavior.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        required=True,
        type=Path,
        help="Existing SQLite database file on the deployment host's intended persistent volume",
    )
    args = parser.parse_args()
    try:
        report = smoke_test(args.db_path)
    except Exception as exc:
        report = {
            "schema_version": "1.0",
            "test": "sqlite_replay_across_independent_os_processes",
            "db_path": str(args.db_path),
            "result": "FAIL",
            "error_type": type(exc).__name__,
            "scope": "local OS-process replay smoke test",
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
