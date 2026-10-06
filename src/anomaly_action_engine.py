"""Map federated anomaly types to specific governed next actions."""
from dataclasses import dataclass
from .federated_anomaly import FederatedAnomaly
from .next_action_engine import NextAction

@dataclass(frozen=True)
class AnomalyAction:
    anomaly: FederatedAnomaly
    next_action: NextAction

class AnomalyActionEngine:
    def recommend(self, anomaly: FederatedAnomaly) -> AnomalyAction:
        if not anomaly.detected:
            return AnomalyAction(anomaly, NextAction("NONE", 99, "No anomaly action.", "Metric is within baseline tolerance."))
        mapping = {
            "qa_pass_rate": ("Investigate QA degradation across instances.", "Quality performance fell below federated baseline."),
            "blocked_rate": ("Investigate blocked execution across instances.", "Blocked execution increased above federated baseline."),
            "evidence_coverage": ("Restore evidence coverage across instances.", "Evidence coverage fell below federated baseline."),
            "drift_rate": ("Review standard drift across instances.", "Runtime drift increased above federated baseline."),
            "revalidation_rate": ("Review elevated revalidation activity.", "Revalidation activity increased above federated baseline."),
        }
        action, reason = mapping.get(anomaly.metric, ("Review federated anomaly.", "Anomaly metric requires governed investigation."))
        priority = 1 if anomaly.severity == "HIGH" else 3
        return AnomalyAction(anomaly, NextAction("SIGNAL", priority, action, reason))
