"""Negative and positive contract tests for the cybersecurity registry schema."""
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/cybersecurity-threat-record.schema.json").read_text(encoding="utf-8"))
VALID_RECORD = json.loads((ROOT / "tests/fixtures/cybersecurity/valid-pending-record.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

class CybersecuritySchemaTests(unittest.TestCase):
    def assert_invalid(self, record, path_prefix=None):
        errors = list(VALIDATOR.iter_errors(record))
        self.assertTrue(errors, "record unexpectedly passed schema validation")
        if path_prefix:
            self.assertTrue(any(".".join(map(str, e.absolute_path)).startswith(path_prefix) for e in errors), errors)

    def test_pending_unknown_applicability_hold_is_valid(self):
        self.assertEqual(list(VALIDATOR.iter_errors(VALID_RECORD)), [])

    def test_unknown_applicability_cannot_authorize_remediation(self):
        record = copy.deepcopy(VALID_RECORD)
        record["assessment"]["decision"] = "remediate"
        self.assert_invalid(record, "assessment")

    def test_verified_threat_requires_source_and_timestamp(self):
        record = copy.deepcopy(VALID_RECORD)
        record["threat"]["verification_status"] = "verified"
        self.assert_invalid(record, "threat")

    def test_completed_execution_requires_before_and_after_evidence(self):
        record = copy.deepcopy(VALID_RECORD)
        record["execution"]["status"] = "completed"
        record["execution"]["result"] = "succeeded"
        self.assert_invalid(record, "execution")

    def test_passed_qa_requires_reviewer_and_evidence(self):
        record = copy.deepcopy(VALID_RECORD)
        record["qa"]["status"] = "passed"
        self.assert_invalid(record, "qa")

    def test_approved_change_requires_scope_approver_and_rollback_plan(self):
        record = copy.deepcopy(VALID_RECORD)
        record["approval"]["status"] = "approved"
        self.assert_invalid(record, "approval")

    def test_unknown_fields_are_rejected(self):
        record = copy.deepcopy(VALID_RECORD)
        record["assessment"]["bypass_gate"] = True
        self.assert_invalid(record, "assessment")

if __name__ == "__main__":
    unittest.main(verbosity=2)
