"""Acceptance tests for the local synthetic Medaius P1 pilot."""

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pilots.medaius_p1.cli import run as run_cli
from pilots.medaius_p1.service import (
    DuplicatePatientID,
    InvalidFixture,
    PatientNotFound,
    load_patients,
    make_audit_event,
    retrieve_history,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "pilots" / "medaius_p1" / "fixtures" / "synthetic_patients.json"


class PatientHistoryTests(unittest.TestCase):
    def test_exact_id_returns_full_matching_record(self):
        patients = load_patients(FIXTURE)
        record = retrieve_history(patients, "SYN-PAT-0001")
        self.assertEqual(record["patient_id"], "SYN-PAT-0001")
        self.assertEqual(record["visits"][0]["visit_id"], "SYN-VIS-0001")
        self.assertEqual(record["visits"][0]["observations"][0]["value"], 24.5)
        self.assertTrue(record["synthetic"])

    def test_missing_id_is_not_found(self):
        with self.assertRaises(PatientNotFound):
            retrieve_history(load_patients(FIXTURE), "SYN-PAT-9999")

    def test_no_fuzzy_match(self):
        with self.assertRaises(PatientNotFound):
            retrieve_history(load_patients(FIXTURE), "SYN-PAT-000")

    def test_duplicate_exact_ids_fail_closed(self):
        duplicate = [
            {"patient_id": "SYN-PAT-0001", "synthetic": True, "visits": []},
            {"patient_id": "SYN-PAT-0001", "synthetic": True, "visits": []},
        ]
        with self.assertRaises(DuplicatePatientID):
            retrieve_history(duplicate, "SYN-PAT-0001")

    def test_direct_retrieval_rejects_record_without_synthetic_marker(self):
        patients = [{"patient_id": "SYN-PAT-0001", "visits": []}]
        with self.assertRaises(InvalidFixture):
            retrieve_history(patients, "SYN-PAT-0001")

    def test_direct_retrieval_rejects_non_synthetic_id_prefix(self):
        patients = [{"patient_id": "PAT-0001", "synthetic": True, "visits": []}]
        with self.assertRaises(InvalidFixture):
            retrieve_history(patients, "PAT-0001")

    def test_direct_retrieval_rejects_malformed_record(self):
        with self.assertRaises(InvalidFixture):
            retrieve_history([{"patient_id": "SYN-PAT-0001", "synthetic": True}], "SYN-PAT-0001")

    def test_result_is_copy_not_mutable_source(self):
        patients = load_patients(FIXTURE)
        record = retrieve_history(patients, "SYN-PAT-0001")
        record["visits"].clear()
        self.assertEqual(len(patients[0]["visits"]), 1)

    def test_fixture_sha256_is_unchanged_by_retrieval(self):
        before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        retrieve_history(load_patients(FIXTURE), "SYN-PAT-0001")
        after = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(after, before)

    def test_invalid_fixture_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"patient_id": "SYN-PAT-0001"}), encoding="utf-8")
            with self.assertRaises(InvalidFixture):
                load_patients(path)

    def test_fixture_requires_synthetic_marker_and_synthetic_id_prefix(self):
        valid_record = {
            "patient_id": "SYN-PAT-0001",
            "synthetic": True,
            "visits": [],
        }
        invalid_records = (
            {"patient_id": "SYN-PAT-0001", "visits": []},
            {"patient_id": "SYN-PAT-0001", "synthetic": False, "visits": []},
            {"patient_id": "PAT-0001", "synthetic": True, "visits": []},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps([valid_record]), encoding="utf-8")
            self.assertEqual(len(load_patients(path)), 1)
            for record in invalid_records:
                with self.subTest(record=record):
                    path.write_text(json.dumps([record]), encoding="utf-8")
                    with self.assertRaises(InvalidFixture):
                        load_patients(path)

    def test_audit_event_excludes_patient_data(self):
        event = make_audit_event("req-123", "SUCCESS")
        serialized = json.dumps(event)
        self.assertIn("req-123", serialized)
        self.assertNotIn("SYN-PAT", serialized)
        self.assertNotIn("visits", serialized)
        self.assertEqual(event["action"], "patient_history_retrieval")

    def test_audit_rejects_request_id_with_spaces_or_control_characters(self):
        for request_id in ("has space", "line\\nbreak", "", "x" * 81):
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    make_audit_event(request_id, "SUCCESS")

    def test_audit_rejects_unknown_outcome(self):
        with self.assertRaises(ValueError):
            make_audit_event("req-123", "PATIENT_RECORD")

    def test_cli_writes_a_valid_jsonl_audit_record(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit.jsonl"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = run_cli([
                    "--fixture", str(FIXTURE),
                    "--patient-id", "SYN-PAT-0001",
                    "--request-id", "jsonl-test-001",
                    "--audit-file", str(audit_path),
                ])
            self.assertEqual(code, 0)
            lines = audit_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            event = json.loads(lines[0])
            self.assertEqual(event["request_id"], "jsonl-test-001")
            self.assertEqual(event["outcome"], "SUCCESS")
            self.assertNotIn("SYN-PAT-0001", lines[0])
            self.assertEqual(stdout.getvalue() and json.loads(stdout.getvalue())["patient_id"], "SYN-PAT-0001")

    def test_cli_withholds_result_when_audit_write_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            audit_path = Path(directory) / "audit-is-a-directory"
            audit_path.mkdir()
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = run_cli([
                    "--fixture", str(FIXTURE),
                    "--patient-id", "SYN-PAT-0001",
                    "--audit-file", str(audit_path),
                ])
            self.assertEqual(code, 4)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("audit event could not be persisted", stderr.getvalue())
            self.assertNotIn("SYN-PAT-0001", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
