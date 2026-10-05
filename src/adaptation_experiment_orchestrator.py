"""Orchestrate governed adaptation experiments."""

from dataclasses import dataclass

from .adaptation_engine import AdaptationEngine, AdaptationProposal
from .adaptation_validation import AdaptationExperiment, AdaptationValidationEngine


@dataclass(frozen=True)
class AdaptationExperimentRun:
    adaptation_id: str
    baseline: float
    result: float
    experiment: AdaptationExperiment


class AdaptationExperimentOrchestrator:
    """Start experiments only from approved adaptations; validation remains explicit."""

    def __init__(self, validator: AdaptationValidationEngine | None = None) -> None:
        self.validator = validator or AdaptationValidationEngine()

    def run(
        self,
        proposal: AdaptationProposal,
        *,
        baseline: float,
        result: float,
        higher_is_better: bool = True,
    ) -> AdaptationExperimentRun:
        if proposal.status != "APPROVED":
            raise ValueError("only approved adaptations can start experiments")
        experiment = self.validator.evaluate(
            proposal.id,
            baseline,
            result,
            higher_is_better=higher_is_better,
        )
        return AdaptationExperimentRun(proposal.id, baseline, result, experiment)
