"""Process-termination recovery tests for the file-backed SQLite proposal store.

These tests exercise SQLite process-crash recovery around transaction commit.
They do not simulate power loss, filesystem write reordering, or cross-store atomicity.
"""
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.adaptation_engine import AdaptationEngine
from src.adaptation_proposal_repository import (
    AdaptationProposalConflict,
    SQLiteAdaptationProposalRepository,
)
from src.operating_memory import OperatingMemoryRecord


_CHILD_TRANSACTION = r"""
import os
import sqlite3
import sys

path, phase = sys.argv[1], sys.argv[2]
connection = sqlite3.connect(path, timeout=10)
connection.execute("PRAGMA busy_timeout = 10000")
connection.execute(
    """INSERT INTO adaptation_proposals
       (proposal_id, idempotency_key, payload_hash, payload_json, status)
       VALUES (?, ?, ?, ?, ?)""",
    (
        "adapt:crash-event",
        "learning:crash-event",
        "sha256:crash-payload",
        '{"id":"adapt:crash-event","source_command_id":"cmd:crash"}',
        "PROPOSED",
    ),
)
if phase == "after_commit":
    connection.commit()
    os._exit(74)
os._exit(73)
"""


class SQLiteProposalProcessCrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.record = OperatingMemoryRecord(
            command_id="cmd:crash",
            timestamp="2026-10-30T00:00:00+00:00",
            wanted="wanted",
            did="did",
            actual="actual",
            verified="verified",
            decision="decision",
            learned="learned",
            changed="changed",
            next_command="next",
            confidence=0.8,
            event_id="learning:crash-event",
        )
        self.proposal_kwargs = {
            "pattern": "quality",
            "problem": "poor outcome",
            "proposed_change": "review rule",
            "expected_effect": "improve outcome",
            "next_experiment": "shadow test",
        }

    def _terminate_writer(self, path, phase, expected_exit):
        result = subprocess.run(
            [sys.executable, "-c", _CHILD_TRANSACTION, str(path), phase],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected_exit,
            msg=f"child stdout={result.stdout!r}; stderr={result.stderr!r}",
        )

    def _assert_database_integrity(self, path):
        import sqlite3

        with sqlite3.connect(path) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        self.assertEqual(result, ("ok",))

    def test_process_termination_before_commit_rolls_back_then_retry_creates_one_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proposals.sqlite3"
            repository = SQLiteAdaptationProposalRepository(str(path))

            # Child exits with an uncommitted INSERT still open.
            self._terminate_writer(path, "before_commit", 73)

            self.assertIsNone(repository.get("learning:crash-event"))
            self._assert_database_integrity(path)

            # A normal application retry creates the canonical proposal.
            proposal = AdaptationEngine(repository).propose(
                self.record, **self.proposal_kwargs
            )
            retried = AdaptationEngine(
                SQLiteAdaptationProposalRepository(str(path))
            ).propose(self.record, **self.proposal_kwargs)

            self.assertEqual(proposal.id, "adapt:learning:crash-event")
            self.assertEqual(retried.id, proposal.id)
            self.assertEqual(retried.status, "PROPOSED")
            self.assertEqual(
                repository.get(proposal.id)["status"],
                "PROPOSED",
            )
            self._assert_database_integrity(path)

    def test_process_termination_after_commit_preserves_row_and_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proposals.sqlite3"
            repository = SQLiteAdaptationProposalRepository(str(path))

            # Child commits the INSERT and then exits without orderly connection close.
            self._terminate_writer(path, "after_commit", 74)

            stored = repository.get("learning:crash-event")
            self.assertIsNotNone(stored)
            self.assertEqual(stored["id"], "adapt:crash-event")
            self.assertEqual(stored["status"], "PROPOSED")
            self._assert_database_integrity(path)

            # Application retry must return the already committed canonical row.
            proposal = AdaptationEngine(repository).propose(
                self.record, **self.proposal_kwargs
            )
            self.assertEqual(proposal.id, "adapt:learning:crash-event")
            self.assertEqual(proposal.status, "PROPOSED")
            self.assertEqual(
                repository.get("learning:crash-event")["id"],
                proposal.id,
            )
            self._assert_database_integrity(path)

    def test_proposal_id_collision_under_different_idempotency_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = SQLiteAdaptationProposalRepository(
                str(Path(tmp) / "proposals.sqlite3")
            )
            engine = AdaptationEngine(repository)
            original = engine.propose(self.record, **self.proposal_kwargs)
            conflicting = replace(original, problem="different immutable content")

            with self.assertRaisesRegex(
                AdaptationProposalConflict,
                "proposal id already belongs to another event",
            ):
                repository.get_or_create(
                    conflicting,
                    idempotency_key="learning:different-event",
                )

            stored = repository.get(original.id)
            self.assertEqual(stored["problem"], "poor outcome")
            self.assertEqual(stored["status"], "PROPOSED")


if __name__ == "__main__":
    unittest.main()
