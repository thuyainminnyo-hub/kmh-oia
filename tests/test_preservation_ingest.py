import json
import os
import subprocess
import sys
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
        (root / manifest_name).write_text(entry + "\n", encoding="utf-8")
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
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  data/link/payload.bin")
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

    def test_payload_manifest_accepts_bag_root_relative_data_path(self):
        root = self._make_manifest_root("manifest-sha256.txt", "0" * 64 + "  data/payload.bin")
        (root / "data" / "payload.bin").write_bytes(b"payload")
        validate_manifest_paths(root)

    def test_tag_manifest_rejects_payload_path(self):
        root = self._make_manifest_root("tagmanifest-sha256.txt", "0" * 64 + "  data/payload.bin")
        with self.assertRaises(IntakeError) as caught:
            validate_manifest_paths(root)
        self.assertEqual(caught.exception.code, "TAG_PATH_REFERENCES_PAYLOAD")

    def test_recovery_inspection_reports_orphans_without_deleting(self):
        from scripts.preservation_ingest import inspect_incomplete_ingests
        reservations = self.workspace / "reservations"
        staging = self.workspace / "staging"
        reservations.mkdir()
        staging.mkdir()
        lock = reservations / "orphan-001.lock"
        lock.write_text('{"object_id":"orphan-001"}', encoding="utf-8")
        staged = staging / "orphan-run"
        staged.mkdir()
        findings = inspect_incomplete_ingests(self.workspace)
        self.assertEqual({item["kind"] for item in findings}, {"reservation", "staging_directory"})
        self.assertTrue(lock.exists())
        self.assertTrue(staged.exists())

    def test_receipt_failure_after_promotion_preserves_accepted_bag(self):
        from scripts import preservation_ingest as worker
        original_write = worker._write_json
        calls = {"count": 0}
        def fail_final_receipt_once(path, value):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("simulated final receipt write failure")
            return original_write(path, value)
        with patch("scripts.preservation_ingest._write_json", side_effect=fail_final_receipt_once):
            with self.assertRaises(IntakeError) as caught:
                ingest(self.source, "receipt-crash-001", self.workspace)
        self.assertEqual(caught.exception.code, "INGEST_FAILED")
        accepted = self.workspace / "accepted" / "receipt-crash-001"
        self.assertTrue((accepted / "bagit.txt").is_file())
        receipts = [p for p in (self.workspace / "reports").glob("receipt-crash-001-*.json") if not p.name.endswith(".promotion-pending.json")]
        self.assertEqual(len(receipts), 1)
        receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
        self.assertEqual(receipt["result"], "accepted_receipt_pending")
        journals = list((self.workspace / "reports").glob("receipt-crash-001-*.promotion-pending.json"))
        self.assertEqual(len(journals), 1)
        self.assertTrue((self.workspace / "reservations" / "receipt-crash-001.lock").exists())

    def test_recovery_inspection_reports_pending_promotion_journal(self):
        from scripts.preservation_ingest import inspect_incomplete_ingests
        reports = self.workspace / "reports"
        reports.mkdir()
        journal = reports / "object-001-run.promotion-pending.json"
        journal.write_text('{"object_id":"object-001","state":"promotion_pending"}', encoding="utf-8")
        findings = inspect_incomplete_ingests(self.workspace)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["kind"], "promotion_journal")
        self.assertEqual(findings[0]["status"], "promotion_journal_requires_reconciliation")
        self.assertTrue(journal.exists())


    def test_subprocess_crash_at_each_durable_checkpoint(self):
        checkpoints = [
            "reservation_durable",
            "source_captured",
            "bag_validated",
            "journal_durable",
            "promotion_durable",
            "receipt_durable",
            "journal_removed",
            "reservation_released",
        ]
        for checkpoint in checkpoints:
            with self.subTest(checkpoint=checkpoint):
                workspace = self.root / ("workspace-" + checkpoint)
                workspace.mkdir()
                script = r"""
import os, sys
from scripts.preservation_ingest import ingest
source, object_id, workspace, target = sys.argv[1:]
def crash(name):
    if name == target:
        os._exit(91)
ingest(source, object_id, workspace, crash_hook=crash)
"""
                completed = subprocess.run(
                    [sys.executable, "-c", script, str(self.source),
                     "crash-" + checkpoint, str(workspace), checkpoint],
                    cwd=Path(__file__).resolve().parents[1],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(completed.returncode, 91, completed.stderr)
                accepted = workspace / "accepted" / ("crash-" + checkpoint)
                journals = list((workspace / "reports").glob("*.promotion-pending.json")) if (workspace / "reports").exists() else []
                receipts = [p for p in (workspace / "reports").glob("*.json")
                            if not p.name.endswith(".promotion-pending.json")] if (workspace / "reports").exists() else []
                reservation = workspace / "reservations" / ("crash-" + checkpoint + ".lock")
                if checkpoint in ("promotion_durable", "receipt_durable", "journal_removed", "reservation_released"):
                    self.assertTrue((accepted / "bagit.txt").is_file())
                else:
                    self.assertFalse(accepted.exists())
                if checkpoint in ("journal_durable", "promotion_durable", "receipt_durable"):
                    self.assertEqual(len(journals), 1)
                else:
                    self.assertEqual(len(journals), 0)
                if checkpoint in ("receipt_durable", "journal_removed", "reservation_released"):
                    self.assertEqual(len(receipts), 1)
                else:
                    self.assertEqual(len(receipts), 0)
                if checkpoint == "reservation_released":
                    self.assertFalse(reservation.exists())
                else:
                    self.assertTrue(reservation.exists())
                if accepted.exists():
                    bag = bagit.Bag(str(accepted))
                    self.assertTrue(bag.is_valid())
                    payload = accepted / "data/source/original.mid"
                    self.assertEqual(payload.read_bytes(), self.source.read_bytes())


    def _create_pending_journal_for_accepted_bag(self, object_id):
        from scripts.preservation_ingest import _write_json
        receipt = ingest(self.source, object_id, self.workspace)
        run_id = receipt["run_id"]
        journal = self.workspace / "reports" / f"{object_id}-{run_id}.promotion-pending.json"
        _write_json(journal, {
            "schema": "kmh.preservation-promotion-journal.v1",
            "run_id": run_id,
            "object_id": object_id,
            "staging_path": f"staging/{object_id}-{run_id}-missing",
            "accepted_path": f"accepted/{object_id}",
            "source_sha256": receipt["source_sha256"],
            "source_byte_length": receipt["source_byte_length"],
            "state": "promotion_pending",
        })
        return journal, self.workspace / "accepted" / object_id

    def test_read_only_recovery_planner_verifies_accepted_bag_without_mutation(self):
        from scripts.preservation_ingest import plan_ingest_recovery
        journal, accepted = self._create_pending_journal_for_accepted_bag("planner-accepted-001")
        before = {str(p.relative_to(self.workspace)): (p.read_bytes() if p.is_file() else None)
                  for p in self.workspace.rglob("*")}
        plans = plan_ingest_recovery(self.workspace)
        after = {str(p.relative_to(self.workspace)): (p.read_bytes() if p.is_file() else None)
                 for p in self.workspace.rglob("*")}
        self.assertEqual(before, after)
        self.assertTrue(journal.exists())
        self.assertTrue((accepted / "bagit.txt").exists())
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["status"], "accepted_bag_verified_receipt_reconciliation_required")
        self.assertEqual(plans[0]["proposed_action"], "operator_review_finalize_receipt")
        self.assertTrue(plans[0]["evidence"]["candidates"][0]["source_evidence_matches"])

    def test_read_only_recovery_planner_flags_corrupt_accepted_bag(self):
        from scripts.preservation_ingest import plan_ingest_recovery
        journal, accepted = self._create_pending_journal_for_accepted_bag("planner-corrupt-001")
        payload = accepted / "data" / "source" / "original.mid"
        payload.write_bytes(b"tampered")
        plans = plan_ingest_recovery(self.workspace)
        self.assertEqual(plans[0]["status"], "no_matching_valid_bag_found")
        self.assertEqual(plans[0]["proposed_action"], "manual_investigation")
        self.assertTrue(journal.exists())

    def test_read_only_recovery_planner_rejects_journal_path_traversal(self):
        from scripts.preservation_ingest import plan_ingest_recovery, _write_json
        reports = self.workspace / "reports"
        reports.mkdir()
        journal = reports / "unsafe.promotion-pending.json"
        _write_json(journal, {
            "schema": "kmh.preservation-promotion-journal.v1",
            "run_id": "unsafe",
            "object_id": "unsafe-001",
            "staging_path": "staging/../outside",
            "accepted_path": "accepted/unsafe-001",
            "source_sha256": "a" * 64,
            "source_byte_length": 1,
            "state": "promotion_pending",
        })
        plans = plan_ingest_recovery(self.workspace)
        self.assertEqual(plans[0]["status"], "journal_or_path_invalid")
        self.assertEqual(plans[0]["proposed_action"], "manual_investigation")
        self.assertTrue(journal.exists())


if __name__ == "__main__":
    unittest.main()
