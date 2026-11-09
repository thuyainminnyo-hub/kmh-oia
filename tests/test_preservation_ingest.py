import json
import tempfile
import unittest
from pathlib import Path

from scripts.preservation_ingest import IntakeError, ingest


class PreservationIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "fixture.mid"
        self.source.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x01\xe0MTrk\x00\x00\x00\x04\x00\xff\x2f\x00")
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_fixture_is_preserved_and_bag_validates(self):
        original = self.source.read_bytes()
        result = ingest(self.source, "fixture-001", self.workspace)
        payload = self.workspace / result["accepted_path"] / "data/source/original.mid"
        self.assertEqual(result["result"], "accepted")
        self.assertEqual(payload.read_bytes(), original)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(result["source_sha256"], result["staged_sha256"])
        self.assertEqual(result["rights_status"], "unknown")

    def test_duplicate_object_id_never_overwrites(self):
        ingest(self.source, "fixture-002", self.workspace)
        with self.assertRaises(IntakeError) as caught:
            ingest(self.source, "fixture-002", self.workspace)
        self.assertEqual(caught.exception.code, "DUPLICATE_OBJECT_ID")

    def test_invalid_object_id_rejected(self):
        with self.assertRaises(IntakeError) as caught:
            ingest(self.source, "../escape", self.workspace)
        self.assertEqual(caught.exception.code, "INVALID_OBJECT_ID")

    def test_symlink_source_rejected(self):
        link = self.root / "linked.mid"
        link.symlink_to(self.source)
        with self.assertRaises(IntakeError) as caught:
            ingest(link, "fixture-003", self.workspace)
        self.assertEqual(caught.exception.code, "SOURCE_SYMLINK")

    def test_missing_source_rejected(self):
        with self.assertRaises(IntakeError) as caught:
            ingest(self.root / "missing.mid", "fixture-004", self.workspace)
        self.assertEqual(caught.exception.code, "SOURCE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
