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
            evidence_refs=("trace:trace:1", "qa:cmd:1"),
        )
        self.assertTrue(record.decision_traceable)
        self.assertFalse(record.externally_validated)
        self.assertIsNone(record.learning_admission_id)
        self.assertIsNone(record.decision_change_id)

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
            evidence_refs=("trace:trace:1",),
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
            evidence_refs=("trace:trace:2", "outcome:outcome:2"),
            learning_admission_id="learn-admit:2",
            decision_change_id="decision-change:2",
        )
        self.assertFalse(observed.externally_validated)
        self.assertTrue(linked.externally_validated)

    def test_admitted_learning_requires_evidence_and_admission_id(self):
        base = dict(
            context_id="ctx:1",
            decision_id="dec:1",
            command_id="cmd:1",
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="VERIFIED",
            learning_status="ADMITTED",
        )
        with self.assertRaisesRegex(ValueError, "evidence reference"):
            OperatingLoopRecord(**base, learning_admission_id="learn-admit:1")
        with self.assertRaisesRegex(ValueError, "learning_admission_id"):
            OperatingLoopRecord(**base, evidence_refs=("trace:trace:1",))

    def test_decision_change_requires_admitted_learning(self):
        with self.assertRaisesRegex(ValueError, "requires admitted learning"):
            OperatingLoopRecord(
                context_id="ctx:1",
                decision_id="dec:1",
                command_id="cmd:1",
                execution_id="exec:1",
                trace_id="trace:1",
                qa_status="PASS",
                evidence_status="OBSERVED",
                learning_status="NOT_ADMITTED",
                evidence_refs=("trace:trace:1",),
                decision_change_id="decision-change:1",
            )

    def test_duplicate_or_blank_evidence_refs_are_rejected(self):
        base = dict(
            context_id="ctx:1",
            decision_id="dec:1",
            command_id="cmd:1",
            execution_id="exec:1",
            trace_id="trace:1",
            qa_status="PASS",
            evidence_status="OBSERVED",
            learning_status="NOT_ADMITTED",
        )
        with self.assertRaisesRegex(ValueError, "unique"):
            OperatingLoopRecord(**base, evidence_refs=("trace:1", "trace:1"))
        with self.assertRaisesRegex(ValueError, "blank"):
            OperatingLoopRecord(**base, evidence_refs=(" ",))


if __name__ == "__main__":
    unittest.main()
