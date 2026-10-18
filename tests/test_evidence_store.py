"""Tests for the append-only JSONL evidence store."""
import tempfile
import unittest
from pathlib import Path

from src.evidence_object import EvidenceObject
from src.evidence_store import JsonlEvidenceStore


class JsonlEvidenceStoreTests(unittest.TestCase):
    def make_evidence(self, evidence_id="evidence:001", trace_id="trace:001"):
        return EvidenceObject(
            evidence_id=evidence_id,
            kind="runtime_trace",
            source="kmh-oia",
            observed_at="2026-10-18T01:00:00Z",
            scope="controlled-pilot",
            source_revision="test-revision",
            artifact_ref=f"artifact:{evidence_id}",
            trace_id=trace_id,
        )

    def test_append_and_get_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEvidenceStore(Path(directory) / "evidence.jsonl")
            expected = self.make_evidence()
            store.append(expected)
            self.assertEqual(store.get(expected.evidence_id), expected)

    def test_duplicate_id_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            store = JsonlEvidenceStore(path)
            original = self.make_evidence()
            store.append(original)
            with self.assertRaisesRegex(ValueError, "already exists"):
                store.append(self.make_evidence(trace_id="trace:changed"))
            self.assertEqual(store.get(original.evidence_id), original)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_records_survive_store_recreation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            expected = self.make_evidence()
            JsonlEvidenceStore(path).append(expected)
            reopened = JsonlEvidenceStore(path)
            self.assertEqual(reopened.get(expected.evidence_id), expected)

    def test_list_by_trace_returns_only_matching_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEvidenceStore(Path(directory) / "evidence.jsonl")
            first = self.make_evidence("evidence:001", "trace:shared")
            second = self.make_evidence("evidence:002", "trace:shared")
            other = self.make_evidence("evidence:003", "trace:other")
            for item in (first, second, other):
                store.append(item)
            self.assertEqual(store.list_by_trace("trace:shared"), [first, second])

    def test_invalid_store_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text('{"evidence_id": "incomplete"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid evidence record"):
                JsonlEvidenceStore(path)


if __name__ == "__main__":
    unittest.main()
