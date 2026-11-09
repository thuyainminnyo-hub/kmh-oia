import json
import os
import tempfile
import unittest
from pathlib import Path

import bagit

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
        accepted_bag = payload.parents[2]
        bagit.Bag(str(accepted_bag)).validate()
        self.assertTrue((accepted_bag / "manifest-sha256.txt").is_file())
        self.assertTrue((accepted_bag / "manifest-sha512.txt").is_file())
        self.assertTrue((accepted_bag / "tagmanifest-sha256.txt").is_file())
        self.assertTrue((accepted_bag / "tagmanifest-sha512.txt").is_file())
        self.assertEqual(result["manifest_algorithms"], ["sha256", "sha512"])
        self.assertNotEqual(result["validation_tool_version"], "unknown")
        self.assertFalse((accepted_bag / "intake-receipt.json").exists())
        report = self.workspace / "reports" / (result["object_id"] + "-" + result["run_id"] + ".json")
        self.assertTrue(report.is_file())

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

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO test requires POSIX mkfifo")
    def test_fifo_source_rejected_without_blocking(self):
        fifo = self.root / "source.fifo"
        os.mkfifo(fifo)
        with self.assertRaises(IntakeError) as caught:
            ingest(fifo, "fixture-005", self.workspace)
        self.assertEqual(caught.exception.code, "SOURCE_NOT_REGULAR_FILE")

    def _make_test_bag(self, name):
        bag_root = self.root / name
        bag_root.mkdir()
        (bag_root / "data").mkdir()
        (bag_root / "data" / "payload.bin").write_bytes(b"preservation-test-payload")
        return bagit.make_bag(str(bag_root), checksums=["sha256", "sha512"])

    def test_payload_tampering_detected(self):
        bag = self._make_test_bag("tampered")
        payload = Path(bag.path) / "data" / "payload.bin"
        payload.write_bytes(b"tampered-payload")
        with self.assertRaises(bagit.BagValidationError):
            bag.validate()

    def test_missing_payload_detected(self):
        bag = self._make_test_bag("missing")
        (Path(bag.path) / "data" / "payload.bin").unlink()
        with self.assertRaises(bagit.BagValidationError):
            bag.validate()

    def test_unexpected_payload_detected(self):
        bag = self._make_test_bag("unexpected")
        (Path(bag.path) / "data" / "extra.bin").write_bytes(b"unexpected")
        with self.assertRaises(bagit.BagValidationError):
            bag.validate()

    def test_corrupt_tag_manifest_detected(self):
        bag = self._make_test_bag("corrupt-tag")
        tag_manifest = Path(bag.path) / "tagmanifest-sha512.txt"
        tag_manifest.write_text("0" * 128 + "  bagit.txt\n", encoding="utf-8")
        with self.assertRaises(bagit.BagValidationError):
            bag.validate()

    def test_missing_source_rejected(self):
        with self.assertRaises(IntakeError) as caught:
            ingest(self.root / "missing.mid", "fixture-004", self.workspace)
        self.assertEqual(caught.exception.code, "SOURCE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
