"""Turn execution health metrics into actionable operating signals."""

from dataclasses import dataclass
from .execution_telemetry import SystemHealthSnapshot


SignalKind = str


@dataclass(frozen=True)
class IntelligenceSignal:
    kind: SignalKind
    severity: str
    metric: str
    value: float
    threshold: float
    message: str
    recommended_action: str


class TelemetrySignalEngine:
    """Deterministic first-line signal detection for operating health."""

    def __init__(
        self,
        *,
        min_qa_pass_rate: float = 0.80,
        max_blocked_rate: float = 0.20,
        max_rework_rate: float = 0.20,
        min_evidence_coverage: float = 0.95,
        max_drift_rate: float = 0.10,
    ) -> None:
        thresholds = (
            min_qa_pass_rate,
            max_blocked_rate,
            max_rework_rate,
            min_evidence_coverage,
            max_drift_rate,
        )
        if any(not 0.0 <= value <= 1.0 for value in thresholds):
            raise ValueError("thresholds must be between 0 and 1")
        self.min_qa_pass_rate = min_qa_pass_rate
        self.max_blocked_rate = max_blocked_rate
        self.max_rework_rate = max_rework_rate
        self.min_evidence_coverage = min_evidence_coverage
        self.max_drift_rate = max_drift_rate

    def analyze(self, snapshot: SystemHealthSnapshot) -> list[IntelligenceSignal]:
        if snapshot.executions == 0:
            return []

        signals: list[IntelligenceSignal] = []

        def add(kind, severity, metric, value, threshold, message, action):
            signals.append(IntelligenceSignal(kind, severity, metric, value, threshold, message, action))

        if snapshot.qa_pass_rate < self.min_qa_pass_rate:
            add("QUALITY_RISK", "HIGH", "qa_pass_rate", snapshot.qa_pass_rate,
                self.min_qa_pass_rate, "QA pass rate is below the operating threshold.",
                "Review failed executions and identify the dominant defect pattern.")

        if snapshot.blocked_rate > self.max_blocked_rate:
            add("FLOW_RISK", "HIGH", "blocked_rate", snapshot.blocked_rate,
                self.max_blocked_rate, "Blocked execution rate is above the operating threshold.",
                "Inspect blockers and remove the highest-leverage execution constraint.")

        if snapshot.rework_rate > self.max_rework_rate:
            add("REWORK_RISK", "MEDIUM", "rework_rate", snapshot.rework_rate,
                self.max_rework_rate, "Rework rate is above the operating threshold.",
                "Find the recurring rework cause and propose a process improvement.")

        if snapshot.evidence_coverage < self.min_evidence_coverage:
            add("EVIDENCE_GAP", "HIGH", "evidence_coverage", snapshot.evidence_coverage,
                self.min_evidence_coverage, "Evidence coverage is below the required level.",
                "Enforce evidence capture before considering work complete.")

        if snapshot.drift_rate > self.max_drift_rate:
            add("STANDARD_DRIFT", "HIGH", "drift_rate", snapshot.drift_rate,
                self.max_drift_rate, "Observed standard drift is above the operating threshold.",
                "Trigger standard revalidation and review whether the active rule remains valid.")

        return signals
