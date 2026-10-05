import unittest
from src.drift_revalidation import DriftRevalidationTrigger
from src.revalidation_orchestrator import RevalidationOrchestrator
from src.standard_registry import StandardVersionRegistry
from src.standardization_engine import OperatingStandard

class RevalidationOrchestratorTests(unittest.TestCase):
    def test_trigger_runs_end_to_end(self):
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        drift=StandardVersionRegistry().detect_drift(standard,"cmd:1","Skip evidence")
        trigger=DriftRevalidationTrigger().create(drift,evidence_id="ev:1")
        run=RevalidationOrchestrator().run(trigger,standard,observed_effect=.2,outcome_positive=True)
        self.assertEqual(run.revalidation.verdict,"VALID")
        self.assertEqual(run.lifecycle.action,"KEEP")

    def test_untriggered_request_rejected(self):
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        drift=StandardRegistryFixture.drift(standard)
        trigger=DriftRevalidationTrigger().create(drift,evidence_id="ev:1")
        resolved=DriftRevalidationTrigger().resolve(trigger)
        with self.assertRaises(ValueError):
            RevalidationOrchestrator().run(resolved,standard,observed_effect=.2,outcome_positive=True)

class StandardRegistryFixture:
    @staticmethod
    def drift(standard):
        return StandardVersionRegistry().detect_drift(standard,"cmd:1","Skip evidence")

if __name__ == "__main__": unittest.main()
