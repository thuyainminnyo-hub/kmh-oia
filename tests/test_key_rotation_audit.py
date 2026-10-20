"""Tests for the local hash-chained key rotation audit prototype."""
import json
import tempfile
import unittest
from pathlib import Path

from src.key_rotation_audit import (
    KeyRotationEvent,
    append_rotation_event,
    verify_rotation_audit,
)


class KeyRotationAuditTests(unittest.TestCase):
    def event(self, action, key_id, actor="security-reviewer", reason="controlled key rotation",
              accepted=None, previous=None):
        return KeyRotationEvent.create(
            action=action,
            key_id=key_id,
            actor_id=actor,
            reason=reason,
            accepted_key_ids=accepted if accepted is not None else {key_id},
            previous_active_key_id=previous,
        )

    def test_appended_events_form_a_valid_hash_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit" / "key-rotation.jsonl"
            first = append_rotation_event(
                self.event("KEY_ACTIVATED", "key-v2", accepted={"key-v1", "key-v2"}, previous="key-v1"),
                path,
            )
            second = append_rotation_event(
                self.event("KEY_RETIRED", "key-v1", accepted={"key-v2"}, previous="key-v2"),
                path,
            )
            self.assertEqual(first["sequence"], 1)
            self.assertEqual(second["sequence"], 2)
            self.assertEqual(second["previous_hash"], first["entry_hash"])
            self.assertTrue(verify_rotation_audit(path))

    def test_tampered_record_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotation.jsonl"
            append_rotation_event(self.event("KEY_ACTIVATED", "key-v2"), path)
            lines = path.read_text(encoding="utf-8").splitlines()
            item = json.loads(lines[0])
            item["event"]["reason"] = "rewritten after the event"
            path.write_text(json.dumps(item) + "\n", encoding="utf-8")
            self.assertFalse(verify_rotation_audit(path))
            with self.assertRaisesRegex(ValueError, "tampered"):
                append_rotation_event(self.event("KEY_RETIRED", "key-v1"), path)

    def test_wrong_sequence_and_broken_chain_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotation.jsonl"
            append_rotation_event(self.event("KEY_ACTIVATED", "key-v2"), path)
            append_rotation_event(self.event("KEY_DEPRECATED", "key-v1", accepted={"key-v1", "key-v2"}), path)
            entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            entries[1]["previous_hash"] = "0" * 64
            path.write_text("".join(json.dumps(item) + "\n" for item in entries), encoding="utf-8")
            self.assertFalse(verify_rotation_audit(path))

    def test_invalid_event_fields_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "actor_id"):
            self.event("KEY_ACTIVATED", "key-v2", actor=" ")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.event("KEY_ROTATED", "key-v2")
        with self.assertRaisesRegex(ValueError, "duplicates"):
            self.event("KEY_ACTIVATED", "key-v2", accepted=["key-v2", "key-v2"])

    def test_empty_or_missing_audit_is_valid_empty_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.jsonl"
            self.assertTrue(verify_rotation_audit(path))


if __name__ == "__main__":
    unittest.main()
