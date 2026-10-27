import unittest

from src.adaptation_engine import AdaptationEngine
from src.operating_memory import OperatingMemoryRecord


def record():
    return OperatingMemoryRecord(
        command_id="cmd-1",
        timestamp="2026-10-05T00:00:00+00:00",
        wanted="Ship outcome",
        did="Ran workflow",
        actual="Workflow completed with rework",
        verified="Trace and QA passed after rework",
        decision="Keep verification gate",
        learned="Rework is recurring",
        changed="Track rework causes",
        next_command="Investigate repeated rework",
        confidence=0.8,
    )


class AdaptationEngineTests(unittest.TestCase):
    def test_propose_from_memory_record(self):
        proposal = AdaptationEngine().propose(
            record(),
            pattern="Repeated rework",
            problem="Quality defects recur",
            proposed_change="Add pre-execution QA checklist",
            expected_effect="Reduce rework",
            next_experiment="Run checklist for next 5 commands",
        )
        self.assertEqual(proposal.status, "PROPOSED")
        self.assertEqual(proposal.confidence, 0.8)

    def test_distinct_event_ids_with_same_command_id_get_distinct_proposal_ids(self):
        engine = AdaptationEngine()
        first_record = record()
        second_record = OperatingMemoryRecord(
            **{**first_record.__dict__, "event_id": "learning:event-2"}
        )
        first = engine.propose(
            first_record, pattern="Pattern A", problem="Problem A",
            proposed_change="Change A", expected_effect="Effect A",
            next_experiment="Experiment A",
        )
        second = engine.propose(
            second_record, pattern="Pattern B", problem="Problem B",
            proposed_change="Change B", expected_effect="Effect B",
            next_experiment="Experiment B",
        )
        self.assertEqual(first.source_command_id, second.source_command_id)
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.id, "adapt:cmd-1")
        self.assertEqual(second.id, "adapt:learning:event-2")

    def test_governed_lifecycle(self):
        engine = AdaptationEngine()
        proposal = engine.propose(
            record(),
            pattern="Repeated rework",
            problem="Quality defects recur",
            proposed_change="Add pre-execution QA checklist",
            expected_effect="Reduce rework",
            next_experiment="Run checklist for next 5 commands",
        )
        approved = engine.approve(proposal)
        self.assertEqual(approved.status, "APPROVED")
        applied = engine.apply(approved)
        self.assertEqual(applied.status, "APPLIED")
        with self.assertRaises(ValueError):
            engine.apply(proposal)


if __name__ == "__main__":
    unittest.main()
