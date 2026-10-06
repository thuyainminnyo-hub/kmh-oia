"""Project federated runtime health into the existing Command Center model."""

from dataclasses import dataclass
from .command_center_cycle_adapter import CommandCenterView
from .federated_telemetry import FederatedHealthSnapshot

@dataclass(frozen=True)
class FederatedCommandCenterView:
    command_center: CommandCenterView
    federated_health: FederatedHealthSnapshot

class FederatedCommandCenterAdapter:
    """Keep federated telemetry read-only while surfacing actionable pressure."""
    def build(self, view: CommandCenterView, health: FederatedHealthSnapshot) -> FederatedCommandCenterView:
        blockers = list(view.blockers)
        if health.blocked_rate > 0 and not blockers:
            blockers.append("Federated runtime has blocked executions.")
        signals = view.signals + (1 if health.drift_rate > 0 else 0)
        enriched = CommandCenterView(
            primary_objective=view.primary_objective,
            health=health,
            signals=signals,
            pending_decisions=view.pending_decisions,
            decision_ids=view.decision_ids,
            blockers=tuple(blockers),
            evidence_pending=view.evidence_pending,
            qa_pending=view.qa_pending,
        )
        return FederatedCommandCenterView(enriched, health)
