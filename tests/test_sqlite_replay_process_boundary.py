"""Cross-process replay regression for the durable SQLite receipt store.

This test starts independent Python processes against one retained database
file. It proves local OS-process boundary behavior in CI, not target-host
deployment health or multi-host storage behavior.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHILD_PROGRAM = r"""
import json
import sys
from src.receipt_replay_store import SQLiteReceiptReplayStore

store = SQLiteReceiptReplayStore(sys.argv[1])
claim = store.claim("ci-process-provider", "receipt-process-stable-001", "sha256:process-stable-payload")
print(json.dumps({
    "accepted": claim.accepted,
    "reason": claim.reason,
    "healthy": store.health_check(),
}, sort_keys=True))
"""


class SQLiteReceiptReplayProcessBoundaryTests(unittest.TestCase):
    def _run_claim(self, db_path: Path) -> dict[str, object]:
        env = os.environ.copy()
        # Run from repository root and ensure local imports resolve from the
        # checkout in GitHub Actions and typical developer invocations.
        root = Path(__file__).resolve().parents[1]
        env["PYTHONPATH"] = str(root) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        result = subprocess.run(
            [sys.executable, "-c", CHILD_PROGRAM, str(db_path)],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        import json

        return json.loads(result.stdout)

    def test_duplicate_receipt_is_rejected_by_a_separate_os_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cross-process-replay.sqlite3"

            # Child process 1 makes the durable claim then exits fully.
            first = self._run_claim(db_path)
            self.assertTrue(first["healthy"])
            self.assertTrue(first["accepted"], first["reason"])

            # Child process 2 has a fresh interpreter and connection, but the
            # same retained database file and receipt identity.
            second = self._run_claim(db_path)
            self.assertTrue(second["healthy"])
            self.assertFalse(second["accepted"], second["reason"])
            self.assertIn("replay", str(second["reason"]).lower())


if __name__ == "__main__":
    unittest.main()
