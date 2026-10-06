import unittest

from src.operating_loop_record import OperatingLoopRecord


class OperatingLoopRecordTests(unittest.TestCase):
    def test_decision_to_execution_trace_is_explicit(self):
        record = OperatingLoopRecord(
            context_id="ctx:1",
            decision_id="dec:1",
            command_id="cmd:1",
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="OBSERVED",
            learning_status="NOT_ADMITTED",
            source_decision_id="dec:1",
        )
        self.assertTrue(record.decision_traceable)
        self.assertFalse(record.externally_validated)

    def test_missing_required_id_is_rejected(self):
        with self.assertRaises(ValueError):
            OperatingLoopRecord(
                context_id="",
                decision_id="dec:1",
                command_id="cmd:1",
                execution_id="exec:1",
                trace_id="trace:1",
                qa_status="PASS",
                evidence_status="UNKNOWN",
                learning_status="NOT_ADMITTED",
            )

    def test_verified_outcome_is_distinct_from_observed_evidence(self):
        observed = OperatingLoopRecord(
            context_id="ctx:1",
            decision_id="dec:1",
            command_id="cmd:1",
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="OBSERVED",
            learning_status="NOT_ADMITTED",
        )
        linked = OperatingLoopRecord(
            context_id="ctx:1",
            decision_id="dec:1",
            command_id="cmd:1",
            execution_id="exec:2",
            trace_id="trace:2",
            qa_status="PASS",
            evidence_status="OUTCOME_LINKED",
            learning_status="ADMITTED",
        )
        self.assertFalse(observed.externally_validated)
        self.assertTrue(linked.externally_validated)


if __name__ == "__main__":
    unittest.main()
