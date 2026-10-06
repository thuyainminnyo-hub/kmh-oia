"""Bridge improved adaptation experiments into governed standard proposals."""
from dataclasses import dataclass
from .adaptation_validation import AdaptationExperiment
from .standardization_engine import OperatingStandard, StandardizationEngine

@dataclass(frozen=True)
class StandardizationFeedback:
    experiment: AdaptationExperiment
    standard: OperatingStandard | None
    action: str
    reason: str

class ExperimentStandardizationBridge:
    def __init__(self, engine: StandardizationEngine | None = None):
        self.engine = engine or StandardizationEngine()

    def feedback(self, experiment: AdaptationExperiment, *, rule: str, expected_effect: str) -> StandardizationFeedback:
        if experiment.verdict == "IMPROVED":
            standard = self.engine.propose(experiment, rule=rule, expected_effect=expected_effect)
            return StandardizationFeedback(experiment, standard, "STANDARD_PROPOSED", "validated improvement can enter governance")
        action = "REVISE" if experiment.verdict == "REGRESSED" else "LEARN"
        return StandardizationFeedback(experiment, None, action, "experiment did not improve the target metric")
