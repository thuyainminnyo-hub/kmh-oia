"""Contract checks for the synthetic TGiTrailRun incident fixture.

These tests use only the Python standard library. They are intentionally not a
replacement for a full JSON Schema 2020-12 validator or service-level tests.
"""
from __future__ import annotations

import json
import re
import unittest
from datetime import datetime

from jsonschema import Draft202012Validator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "docs" / "pilots" / "tgi-trailrun-2026"
SCHEMA_PATH = PILOT_DIR / "incident.schema.json"
FIXTURE_PATH = PILOT_DIR / "fixtures" / "incident.synthetic.json"

ALLOWED_STATUS = {
    "REPORTED", "ACKNOWLEDGED", "DISPATCHED", "RESOLVED", "CLOSED"
}
ALLOWED_TRANSITIONS = {
    ("REPORTED", "ACKNOWLEDGED"),
    ("ACKNOWLEDGED", "DISPATCHED"),
    ("DISPATCHED", "RESOLVED"),
    ("RESOLVED", "CLOSED"),
}


def parse_timestamp(value: str) -> datetime:
    """Parse RFC3339-compatible timestamps, including Z suffix."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


class TGiTrailRunIncidentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_schema_is_json_schema_2020_12_with_closed_object(self) -> None:
        self.assertEqual(
            self.schema.get("$schema"),
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(self.schema.get("type"), "object")
        self.assertIs(self.schema.get("additionalProperties"), False)
        self.assertIn("incident_id", self.schema.get("required", []))
        self.assertIn("event_id", self.schema.get("required", []))
        self.assertIn("audit", self.schema.get("required", []))

    def test_synthetic_fixture_is_json_and_has_required_contract_fields(self) -> None:
        required = set(self.schema["required"])
        self.assertTrue(required.issubset(self.fixture.keys()))
        self.assertEqual(self.fixture["schema_version"], "1.0")
        self.assertRegex(self.fixture["incident_id"], r"^inc_[A-Za-z0-9_-]{8,64}$")
        self.assertRegex(self.fixture["event_id"], r"^evt_[A-Za-z0-9_-]{8,64}$")
        self.assertRegex(self.fixture["runner_id"], r"^run_[A-Za-z0-9_-]{4,64}$")

    def test_fixture_uses_allowed_enums_and_has_location_reference(self) -> None:
        props = self.schema["properties"]
        for field in ("event_type", "severity", "status", "reported_by_role", "summary_code"):
            self.assertIn(self.fixture[field], props[field]["enum"])
        self.assertIn(self.fixture["status"], ALLOWED_STATUS)
        self.assertTrue(
            "checkpoint_id" in self.fixture or "last_known_location" in self.fixture
        )

    def test_all_fixture_timestamps_are_timezone_aware(self) -> None:
        parse_timestamp(self.fixture["occurred_at"])
        parse_timestamp(self.fixture["recorded_at"])
        for entry in self.fixture["audit"]:
            parse_timestamp(entry["at"])

    def test_audit_entries_have_required_fields_and_allowed_actions(self) -> None:
        audit_schema = self.schema["properties"]["audit"]["items"]
        for entry in self.fixture["audit"]:
            self.assertTrue(set(audit_schema["required"]).issubset(entry.keys()))
            for field in ("action", "actor_role", "result"):
                self.assertIn(entry[field], audit_schema["properties"][field]["enum"])

    def test_transition_contract_is_linear_and_rejects_skips(self) -> None:
        self.assertIn(("REPORTED", "ACKNOWLEDGED"), ALLOWED_TRANSITIONS)
        self.assertIn(("RESOLVED", "CLOSED"), ALLOWED_TRANSITIONS)
        self.assertNotIn(("REPORTED", "DISPATCHED"), ALLOWED_TRANSITIONS)
        self.assertNotIn(("ACKNOWLEDGED", "RESOLVED"), ALLOWED_TRANSITIONS)

    def test_full_json_schema_2020_12_validation_accepts_fixture(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        validator = Draft202012Validator(self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        self.assertEqual(list(validator.iter_errors(self.fixture)), [])

    def test_full_json_schema_rejects_unknown_field_and_invalid_status(self) -> None:
        validator = Draft202012Validator(self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        unknown_field = dict(self.fixture, unexpected_field="must be rejected")
        self.assertTrue(list(validator.iter_errors(unknown_field)))
        invalid_status = dict(self.fixture, status="AUTONOMOUSLY_TRIAGED")
        self.assertTrue(list(validator.iter_errors(invalid_status)))

    def test_fixture_is_explicitly_synthetic(self) -> None:
        self.assertIn("Synthetic", self.fixture.get("operator_note", ""))
        self.assertEqual(self.fixture["runner_id"], "run_DEMO001")


if __name__ == "__main__":
    unittest.main()
