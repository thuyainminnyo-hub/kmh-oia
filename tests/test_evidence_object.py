import json
import unittest
from pathlib import Path
from dataclasses import FrozenInstanceError
import re

from src.evidence_object import EvidenceObject


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "evidence-object.schema.json"


class EvidenceObjectTests(unittest.TestCase):
    def make_evidence(self, **overrides):
        values = {
            "evidence_id": "evidence:001",
            "kind": "runtime_trace",
            "source": "kmh-oia",
            "observed_at": "2026-10-14T08:30:00Z",
            "scope": "controlled-pilot",
            "source_revision": "abc1234",
            "artifact_ref": "trace:run-001",
            "run_id": "run-001",
        }
        values.update(overrides)
        return EvidenceObject(**values)

    def test_observed_evidence_requires_provenance_and_artifact_reference(self):
        evidence = self.make_evidence()
        self.assertEqual(evidence.validation_state, "OBSERVED")
        self.assertEqual(evidence.run_id, "run-001")

    def test_at_least_one_execution_reference_is_required(self):
        with self.assertRaisesRegex(ValueError, "execution reference"):
            self.make_evidence(run_id=None)

    def test_artifact_reference_or_digest_is_required(self):
        with self.assertRaisesRegex(ValueError, "artifact_ref or sha256_digest"):
            self.make_evidence(artifact_ref=None)

    def test_non_string_execution_reference_is_rejected_cleanly(self):
        with self.assertRaisesRegex(ValueError, "execution reference"):
            self.make_evidence(run_id=123, command_id=None, trace_id=None, execution_id=None)

    def test_non_string_optional_reference_is_rejected_cleanly(self):
        with self.assertRaisesRegex(ValueError, "trace_id must be a nonblank string"):
            self.make_evidence(trace_id=123)

    def test_non_string_digest_is_rejected_cleanly(self):
        with self.assertRaisesRegex(ValueError, "64 lowercase hexadecimal"):
            self.make_evidence(artifact_ref=None, sha256_digest=123)

    def test_sha256_digest_must_have_exact_format(self):
        with self.assertRaisesRegex(ValueError, "64 lowercase hexadecimal"):
            self.make_evidence(artifact_ref=None, sha256_digest="not-a-digest")

    def test_timezone_is_required(self):
        with self.assertRaisesRegex(ValueError, "RFC-3339"):
            self.make_evidence(observed_at="2026-10-14T08:30:00")

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "RFC-3339"):
            self.make_evidence(observed_at="yesterday")

    def test_timestamp_with_space_separator_is_rejected_for_schema_parity(self):
        with self.assertRaisesRegex(ValueError, "RFC-3339"):
            self.make_evidence(observed_at="2026-10-14 08:30:00+00:00")

    def test_verified_state_requires_validation_reference(self):
        with self.assertRaisesRegex(ValueError, "validation_ref"):
            self.make_evidence(validation_state="VERIFIED")

    def test_outcome_linked_requires_validation_and_outcome_references(self):
        with self.assertRaisesRegex(ValueError, "outcome_ref"):
            self.make_evidence(
                validation_state="OUTCOME_LINKED",
                validation_ref="review:001",
            )

    def test_outcome_linked_accepts_explicit_references(self):
        evidence = self.make_evidence(
            validation_state="OUTCOME_LINKED",
            validation_ref="review:001",
            outcome_ref="outcome:001",
        )
        self.assertEqual(evidence.validation_state, "OUTCOME_LINKED")

    def test_record_is_immutable(self):
        evidence = self.make_evidence()
        with self.assertRaises(FrozenInstanceError):
            evidence.validation_state = "VERIFIED"

    def test_blank_required_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_revision"):
            self.make_evidence(source_revision=" ")

    def test_schema_is_valid_json_and_declares_expected_contract(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            schema["properties"]["validation_state"]["enum"],
            ["OBSERVED", "VERIFIED", "OUTCOME_LINKED"],
        )
        self.assertEqual(len(schema["allOf"]), 4)

    def test_schema_nonblank_pattern_rejects_whitespace_only_values(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        nonblank_pattern = schema["properties"]["source"]["pattern"]
        self.assertIsNotNone(re.search(nonblank_pattern, "kmh-oia"))
        self.assertIsNone(re.search(nonblank_pattern, "   "))

    def test_schema_requires_verification_and_outcome_references_by_state(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        verification_rule, outcome_rule = schema["allOf"][2:]
        self.assertEqual(
            verification_rule["if"]["properties"]["validation_state"]["enum"],
            ["VERIFIED", "OUTCOME_LINKED"],
        )
        self.assertEqual(verification_rule["then"]["required"], ["validation_ref"])
        self.assertEqual(
            outcome_rule["if"]["properties"]["validation_state"]["const"],
            "OUTCOME_LINKED",
        )
        self.assertEqual(outcome_rule["then"]["required"], ["outcome_ref"])


    def test_timestamp_with_invalid_calendar_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "RFC-3339"):
            self.make_evidence(observed_at="2026-02-30T08:30:00Z")

    def test_schema_validation_and_model_parity_when_jsonschema_available(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema dependency is not installed")

        from dataclasses import asdict

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        valid_record = asdict(self.make_evidence())
        validator.validate(valid_record)

        invalid_cases = [
            ({"source": "   "}, {"source": "   "}),
            ({"observed_at": "2026-02-30T08:30:00Z"}, {"observed_at": "2026-02-30T08:30:00Z"}),
            ({"sha256_digest": "BAD"}, {"sha256_digest": "BAD"}),
            (
                {"run_id": None, "command_id": None, "trace_id": None, "execution_id": None},
                {"run_id": None, "command_id": None, "trace_id": None, "execution_id": None},
            ),
            (
                {"validation_state": "VERIFIED", "validation_ref": None},
                {"validation_state": "VERIFIED", "validation_ref": None},
            ),
            (
                {"validation_state": "OUTCOME_LINKED", "validation_ref": "review:001", "outcome_ref": None},
                {"validation_state": "OUTCOME_LINKED", "validation_ref": "review:001", "outcome_ref": None},
            ),
        ]
        for model_overrides, wire_overrides in invalid_cases:
            with self.subTest(overrides=model_overrides):
                try:
                    self.make_evidence(**model_overrides)
                except (TypeError, ValueError):
                    model_rejects = True
                else:
                    model_rejects = False

                wire = {
                    "evidence_id": "evidence:001",
                    "kind": "runtime_trace",
                    "source": "kmh-oia",
                    "observed_at": "2026-10-14T08:30:00Z",
                    "scope": "controlled-pilot",
                    "source_revision": "abc1234",
                    "artifact_ref": "trace:run-001",
                    "sha256_digest": None,
                    "run_id": "run-001",
                    "command_id": None,
                    "trace_id": None,
                    "execution_id": None,
                    "config_version": None,
                    "agent_version": None,
                    "validation_state": "OBSERVED",
                    "validation_ref": None,
                    "outcome_ref": None,
                }
                wire.update(wire_overrides)
                schema_rejects = not validator.is_valid(wire)
                self.assertEqual(model_rejects, schema_rejects, f"model/schema mismatch for {model_overrides!r}")


if __name__ == "__main__":
    unittest.main()
