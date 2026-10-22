"""Tests for SQLite learning-admission atomicity and idempotency."""
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from pathlib import Path

from src.learning_admission_repository import (
    AdmissionConflictError,
    SQLiteLearningAdmissionRepository,
)


class SQLiteLearningAdmissionRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Path(self.tempdir.name) / "learning.sqlite3"
        self.repo = SQLiteLearningAdmissionRepository(self.db)
        self.payload = dict(
            admission_key="admission:execution-1",
            fingerprint="sha256:fingerprint-1",
            learning_record={"command_id": "cmd-1", "learned": "outcome checked"},
            adaptation_proposal={"id": "adapt:admission-1", "status": "PROPOSED"},
            audit_event={"event_id": "audit:admission-1", "kind": "ADMISSION_COMPLETED"},
            result={"admitted": True, "decision_id": "decision-1"},
        )

    def commit(self, **overrides):
        return self.repo.commit(**{**self.payload, **overrides})

    def test_commit_persists_all_effects(self):
        saved = self.commit()
        self.assertEqual(saved.result, self.payload["result"])
        self.assertEqual(saved.learning_record, self.payload["learning_record"])
        self.assertEqual(saved.adaptation_proposal, self.payload["adaptation_proposal"])
        self.assertEqual(self.repo.counts(), {
            "learning_admissions": 1,
            "learning_records": 1,
            "adaptation_proposals": 1,
            "admission_audit_events": 1,
        })

    def test_duplicate_request_returns_stored_result_without_extra_writes(self):
        first = self.commit()
        second = self.commit(result={"admitted": False, "ignored": True})
        self.assertEqual(second.result, first.result)
        self.assertEqual(self.repo.counts()["learning_records"], 1)
        self.assertEqual(self.repo.counts()["adaptation_proposals"], 1)
        self.assertEqual(self.repo.counts()["admission_audit_events"], 1)


    def test_concurrent_duplicate_requests_persist_one_admission(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            saved = list(pool.map(lambda _: self.repo.commit(**self.payload), range(16)))
        self.assertTrue(all(item.result == self.payload["result"] for item in saved))
        self.assertEqual(self.repo.counts(), {
            "learning_admissions": 1,
            "learning_records": 1,
            "adaptation_proposals": 1,
            "admission_audit_events": 1,
        })

    def test_same_key_different_fingerprint_is_rejected(self):
        self.commit()
        with self.assertRaises(AdmissionConflictError):
            self.commit(fingerprint="sha256:different")
        self.assertEqual(self.repo.counts()["learning_records"], 1)

    def test_failure_at_each_stage_rolls_back_every_table(self):
        for stage in ("admission", "learning_record", "adaptation_proposal", "audit_event"):
            with self.subTest(stage=stage):
                key = f"admission:{stage}"
                args = {
                    **self.payload,
                    "admission_key": key,
                    "fingerprint": f"sha256:{stage}",
                    "learning_record": {"command_id": f"cmd:{stage}", "learned": "x"},
                    "adaptation_proposal": {"id": f"adapt:{stage}", "status": "PROPOSED"},
                    "audit_event": {"event_id": f"audit:{stage}", "kind": "TEST"},
                    "result": {"admitted": True},
                }

                def inject(current, expected=stage):
                    if current == expected:
                        raise OSError(f"injected failure at {expected}")

                with self.assertRaises(OSError):
                    self.repo.commit(**args, before_commit=inject)
                self.assertEqual(self.repo.counts(), {
                    "learning_admissions": 0,
                    "learning_records": 0,
                    "adaptation_proposals": 0,
                    "admission_audit_events": 0,
                })

    def test_restart_preserves_idempotency_result(self):
        self.commit()
        reopened = SQLiteLearningAdmissionRepository(self.db)
        saved = reopened.commit(**self.payload)
        self.assertEqual(saved.result, self.payload["result"])
        self.assertEqual(reopened.counts()["learning_admissions"], 1)

    def test_poor_outcome_proposal_must_remain_proposed(self):
        invalid = {**self.payload["adaptation_proposal"], "status": "APPROVED"}
        with self.assertRaisesRegex(ValueError, "PROPOSED"):
            self.commit(adaptation_proposal=invalid)
        self.assertEqual(self.repo.counts()["learning_admissions"], 0)

    def test_admission_requires_durable_path(self):
        with self.assertRaisesRegex(ValueError, "durable"):
            SQLiteLearningAdmissionRepository(":memory:")


if __name__ == "__main__":
    unittest.main()
