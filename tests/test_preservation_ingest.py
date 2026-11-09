import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

import bagit

from scripts.preservation_ingest import IntakeError, ingest, validate_manifest_paths


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

    def test_concurrent_same_object_id_is_atomically_reserved(self):
        entered_capture = threading.Event()
        release_capture = threading.Event()
        original_capture = __import__("scripts.preservation_ingest", fromlist=["_capture_source"])._capture_source
        outcomes = []

        def blocking_capture(source, destination):
            entered_capture.set()
            if not release_capture.wait(timeout=5):
                raise RuntimeError("test capture release timed out")
            return original_capture(source, destination)

        def first_ingest():
            try:
                outcomes.append(("first", ingest(self.source, "race-001", self.workspace)))
            except Exception as exc:
                outcomes.append(("first_error", exc))

        with patch("scripts.preservation_ingest._capture_source", side_effect=blocking_capture):
            thread = threading.Thread(target=first_ingest)
            thread.start()
            self.assertTrue(entered_capture.wait(timeout=5), "first ingest did not reach capture")
            with self.assertRaises(IntakeError) as caught:
                ingest(self.source, "race-001", self.workspace)
            self.assertEqual(caught.exception.code, "OBJECT_ID_RESERVED")
            release_capture.set()
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive(), "first ingest did not finish")

        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0][0], "first")
        self.assertEqual(outcomes[0][1]["result"], "accepted")
        self.assertFalse((self.workspace / "reservations" / "race-001.lock").exists())

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
        (Path(bag.path) / "data" / "data" / "payload.bin").unlink()
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
        reloaded_bag = bagit.Bag(bag.path)
        with self.assertRaises(bagit.BagValidationError):
            reloaded_bag.validate()

    def test_missing_source_rejected(self):
        with self.assertRaises(IntakeError) as caught:
            ingest(self.root / "missing.mid", "fixture-004", self.workspace)
        self.assertEqual(caught.exception.code, "SOURCE_NOT_FOUND")

    def _make_manifest_root(self, manifest_name, entry, payload=True):
        root = self.root / ("manifest-case-" + manifest_name.replace("/", "_"))
        root.mkdir()
        if payload:
            (root / "data").mkdir()
        (root / manifest_name).write_text(entry + "\\n", encoding="utf-8")
        return root

    def test_payload_manifest_parent_traversal_rejected(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  ../outside.bin")
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "UNSAFE_MANIFEST_PATH")

    def test_payload_manifest_absolute_path_rejected(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  /tmp/outside.bin")
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "UNSAFE_MANIFEST_PATH")

    def test_payload_manifest_windows_drive_path_rejected(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  C:/outside.bin")
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "UNSAFE_MANIFEST_PATH")

    def test_payload_manifest_symlink_parent_rejected(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  link/payload.bin")
        outside = self.root / "outside"
        outside.mkdir()
        (root / "data" / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "MANIFEST_PATH_SYMLINK")

    def test_percent_encoded_parent_traversal_rejected(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  %2e%2e/outside.bin")
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "UNSAFE_MANIFEST_PATH")

if __name__ == "__main__":
    unittest.main()
