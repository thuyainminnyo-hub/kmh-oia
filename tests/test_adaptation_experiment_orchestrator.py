import unittest

from src.adaptation_engine import AdaptationEngine
from src.adaptation_experiment_orchestrator import AdaptationExperimentOrchestrator
from src.adaptation_validation import AdaptationValidationEngine
from src.operating_memory import OperatingMemoryRecord


class AdaptationExperimentOrchestratorTests(unittest.TestCase):
    def proposal(self, status="APPROVED"):
        record = OperatingMemoryRecord(
            "cmd:1", "2026-10-05T00:00:00", "wanted", "did", "actual",
            "verified", "decision", "learned", "changed", "next", 0.9
        )
        proposal = AdaptationEngine().propose(
            record,
            pattern="quality",
            problem="rework",
            proposed_change="add QA gate",
            expected_effect="reduce defects",
            next_experiment="run QA gate",
        )
        return proposal if status == "PROPOSED" else AdaptationEngine().approve(proposal)

    def test_approved_adaptation_runs_validation_experiment(self):
        result = AdaptationExperimentOrchestrator().run(
            self.proposal(), baseline=10, result=12
        )
        self.assertEqual(result.adaptation_id, "adapt:cmd:1")
        self.assertEqual(result.experiment.verdict, "IMPROVED")

    def test_proposed_adaptation_cannot_run(self):
        with self.assertRaises(ValueError):
            AdaptationExperimentOrchestrator().run(
                self.proposal("PROPOSED"), baseline=10, result=12
            )

    def test_regression_is_preserved_for_governance_review(self):
        result = AdaptationExperimentOrchestrator().run(
            self.proposal(), baseline=10, result=8
        )
        self.assertEqual(result.experiment.verdict, "REGRESSED")


if __name__ == "__main__":
    unittest.main()
