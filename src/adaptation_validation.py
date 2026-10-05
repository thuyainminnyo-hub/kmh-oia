"""Validate whether an approved adaptation improved its target metric."""
from dataclasses import dataclass
from typing import Literal

ExperimentVerdict = Literal["IMPROVED", "NO_IMPROVEMENT", "REGRESSED"]

@dataclass(frozen=True)
class AdaptationExperiment:
    adaptation_id: str
    baseline: float
    result: float
    higher_is_better: bool = True
    verdict: ExperimentVerdict = "NO_IMPROVEMENT"
    delta: float = 0.0
    relative_change: float = 0.0

    @classmethod
    def evaluate(cls, adaptation_id: str, baseline: float, result: float, *, higher_is_better: bool = True):
        if not adaptation_id.strip(): raise ValueError("adaptation_id is required")
        if baseline < 0 or result < 0: raise ValueError("metrics must be non-negative")
        delta = result - baseline
        effective = delta if higher_is_better else -delta
        verdict = "IMPROVED" if effective > 0 else ("REGRESSED" if effective < 0 else "NO_IMPROVEMENT")
        relative = 0.0 if baseline == 0 else delta / baseline
        return cls(adaptation_id, baseline, result, higher_is_better, verdict, delta, relative)

class AdaptationValidationEngine:
    def evaluate(self, adaptation_id: str, baseline: float, result: float, *, higher_is_better: bool = True) -> AdaptationExperiment:
        return AdaptationExperiment.evaluate(adaptation_id, baseline, result, higher_is_better=higher_is_better)

    def should_standardize(self, experiment: AdaptationExperiment) -> bool:
        return experiment.verdict == "IMPROVED"

    def should_revise(self, experiment: AdaptationExperiment) -> bool:
        return experiment.verdict != "IMPROVED"
