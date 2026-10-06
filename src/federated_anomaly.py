"""Deterministic anomaly detection over federated OIA health snapshots."""
from dataclasses import dataclass
from .federated_telemetry import FederatedHealthSnapshot

@dataclass(frozen=True)
class FederatedBaseline:
    qa_pass_rate: float
    blocked_rate: float
    evidence_coverage: float
    drift_rate: float
    revalidation_rate: float

@dataclass(frozen=True)
class FederatedAnomaly:
    metric: str
    baseline: float
    observed: float
    delta: float
    threshold: float
    severity: str
    detected: bool

class FederatedAnomalyDetector:
    """Compare current federated health against an explicit baseline."""
    def detect(self, baseline: FederatedBaseline, current: FederatedHealthSnapshot, threshold: float = 0.10):
        if threshold < 0:
            raise ValueError("threshold must be non-negative")
        pairs = (
            ("qa_pass_rate", baseline.qa_pass_rate, current.qa_pass_rate, "HIGH"),
            ("blocked_rate", baseline.blocked_rate, current.blocked_rate, "HIGH"),
            ("evidence_coverage", baseline.evidence_coverage, current.evidence_coverage, "MEDIUM"),
            ("drift_rate", baseline.drift_rate, current.drift_rate, "HIGH"),
            ("revalidation_rate", baseline.revalidation_rate, current.revalidation_rate, "MEDIUM"),
        )
        results = []
        for metric, expected, observed, severity in pairs:
            delta = observed - expected
            bad = delta <= -threshold if metric in ("qa_pass_rate", "evidence_coverage") else delta >= threshold
            results.append(FederatedAnomaly(metric, expected, observed, delta, threshold, severity if bad else "NONE", bad))
        return tuple(results)
