"""Tests for versioned cybersecurity registry persistence and execution guard."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.cybersecurity_registry import (
    GENESIS_HASH,
    RegistryError,
    authorize_execution,
    read_entries,
    record_hash,
    save_version,
    verify_registry,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_RECORD = json.loads((ROOT / "tests/fixtures/cybersecurity/valid-pending-record.json").read_text(encoding="utf-8"))


class CybersecurityRegistryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "registry.jsonl"
        self.record = copy.deepcopy(VALID_RECORD)

    def tearDown(self):
        self.temp.cleanup()

    def test_saves_sequential_versions_and_preserves_history(self):
        first = save_version(self.path, self.record, stored_at="2026-10-27T00:00:00+00:00")
        updated = copy.deepcopy(self.record)
        updated["assessment"]["rationale"] = "Updated evidence review"
        second = save_version(self.path, updated, stored_at="2026-10-27T00:01:00+00:00")
        self.assertEqual((first["version"], second["version"]), (1, 2))
        self.assertEqual(verify_registry(self.path), 2)
        self.assertEqual(read_entries(self.path)[1]["previous_hash"], first["entry_hash"])
        self.assertEqual(read_entries(self.path)[0]["record"]["assessment"]["rationale"], self.record["assessment"]["rationale"])

    def test_rejects_invalid_record_before_persisting(self):
        self.record["assessment"]["decision"] = "remediate"
        with self.assertRaises(RegistryError):
            save_version(self.path, self.record)
        self.assertFalse(self.path.exists())

    def test_detects_tampered_entry(self):
        save_version(self.path, self.record)
        entry = json.loads(self.path.read_text(encoding="utf-8").splitlines()[0])
        entry["record"]["assessment"]["rationale"] = "tampered"
        self.path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RegistryError, "hash mismatch"):
            verify_registry(self.path)

    def test_detects_broken_previous_hash(self):
        save_version(self.path, self.record)
        save_version(self.path, self.record)
        lines = self.path.read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[1])
        entry["previous_hash"] = GENESIS_HASH
        entry["entry_hash"] = record_hash(entry)
        lines[1] = json.dumps(entry)
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RegistryError, "broken hash chain"):
            verify_registry(self.path)

    def approved_record(self):
        r = copy.deepcopy(self.record)
        r["threat"]["verification_status"] = "verified"
        r["threat"]["source_refs"] = ["https://security.example/advisory"]
        r["threat"]["last_verified_at"] = "2026-10-26T00:00:00Z"
        r["asset"]["owner"] = "authorized-ops-team"
        r["assessment"].update({"applicability": "affected", "decision": "remediate"})
        r["approval"].update({
            "status": "approved", "approver": "change-manager",
            "scope": ["asset:ASSET-REPLACE-ME", "action:remediate"],
            "approved_at": "2026-10-27T00:00:00Z",
            "expires_at": "2026-10-28T00:00:00Z",
            "rollback_plan_ref": "evidence:rollback-001",
        })
        return r

    def test_allows_exact_valid_approval(self):
        allowed, reason = authorize_execution(self.approved_record(), "remediate", now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc))
        self.assertTrue(allowed, reason)

    def test_denies_pending_approval(self):
        allowed, _ = authorize_execution(self.record, "remediate", now=datetime(2026, 10, 27, tzinfo=timezone.utc))
        self.assertFalse(allowed)

    def test_denies_expired_approval(self):
        r = self.approved_record()
        r["approval"]["expires_at"] = "2026-10-27T00:30:00Z"
        allowed, reason = authorize_execution(r, "remediate", now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc))
        self.assertFalse(allowed)
        self.assertIn("expired", reason)

    def test_denies_scope_mismatch(self):
        r = self.approved_record()
        r["approval"]["scope"] = ["asset:other-asset", "action:remediate"]
        allowed, reason = authorize_execution(r, "remediate", now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc))
        self.assertFalse(allowed)
        self.assertIn("scope", reason)

    def test_denies_unknown_applicability_even_with_approval(self):
        r = self.approved_record()
        r["assessment"]["applicability"] = "unknown"
        r["assessment"]["decision"] = "hold"
        allowed, reason = authorize_execution(r, "remediate", now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc))
        self.assertFalse(allowed)
        self.assertIn("applicability", reason)

    def test_denies_action_that_differs_from_assessment(self):
        allowed, reason = authorize_execution(self.approved_record(), "monitor", now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc))
        self.assertFalse(allowed)
        self.assertIn("decision", reason)

    def test_authorized_action_wrapper_never_calls_executor_when_denied(self):
        from scripts.cybersecurity_registry import run_authorized_action

        calls = []
        executed, reason, result = run_authorized_action(
            self.record, "remediate", lambda: calls.append("called"),
            now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc),
        )
        self.assertFalse(executed)
        self.assertIn("approval", reason)
        self.assertEqual(calls, [])
        self.assertIsNone(result)

    def test_authorized_action_wrapper_calls_executor_after_valid_approval(self):
        from scripts.cybersecurity_registry import run_authorized_action

        calls = []
        executed, reason, result = run_authorized_action(
            self.approved_record(), "remediate",
            lambda: calls.append("executed") or "ok",
            now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc),
        )
        self.assertTrue(executed, reason)
        self.assertEqual(calls, ["executed"])
        self.assertEqual(result, "ok")

    def test_authorized_action_wrapper_rejects_non_callable_executor(self):
        from scripts.cybersecurity_registry import run_authorized_action

        executed, reason, result = run_authorized_action(
            self.approved_record(), "remediate", None,
            now=datetime(2026, 10, 27, 1, tzinfo=timezone.utc),
        )
        self.assertFalse(executed)
        self.assertIn("callable", reason)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
