import unittest

from src.p15_7_drill_records import DrillRecord, OperationalDrillRecordValidator


class P157DrillRecordTests(unittest.TestCase):
    def test_complete_record_is_valid(self):
        record = DrillRecord(
            "rb-001",
            "rollback",
            "staging",
            "2026-10-02T05:00:00Z",
            "2026-10-02T05:10:00Z",
            "operator-1",
            "passed",
            "run-log-001",
        )
        OperationalDrillRecordValidator().validate(record)

    def test_incomplete_record_is_rejected(self):
        record = DrillRecord("rb-001", "rollback", "staging", "", "2026-10-02T05:10:00Z", "operator-1", "passed", "run-log")
        with self.assertRaises(ValueError):
            OperationalDrillRecordValidator().validate(record)

    def test_both_successful_drill_types_are_required(self):
        validator = OperationalDrillRecordValidator()
        rollback = DrillRecord("rb-001", "rollback", "staging", "start", "end", "operator", "passed", "log")
        incident = DrillRecord("inc-001", "incident_response", "staging", "start", "end", "operator", "passed", "log")
        validator.require_success_evidence((rollback, incident))

    def test_missing_or_failed_drill_is_rejected(self):
        validator = OperationalDrillRecordValidator()
        rollback = DrillRecord("rb-001", "rollback", "staging", "start", "end", "operator", "failed", "log")
        with self.assertRaises(RuntimeError):
            validator.require_success_evidence((rollback,))


if __name__ == "__main__":
    unittest.main()
