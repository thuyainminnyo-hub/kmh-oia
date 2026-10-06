"""Federated telemetry aggregation for OIA instances."""

from dataclasses import dataclass

@dataclass(frozen=True)
class FederatedHealthSnapshot:
    executions: int
    instances: int
    accounts: int
    qa_pass_rate: float
    blocked_rate: float
    evidence_coverage: float
    drift_rate: float
    revalidation_rate: float

class FederatedTelemetryEngine:
    """Aggregate already-collected telemetry without centralizing runtime state."""
    def snapshot(self, records):
        items = tuple(records)
        total = len(items)
        if total == 0:
            return FederatedHealthSnapshot(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return FederatedHealthSnapshot(
            total,
            len({x.identity.instance_id for x in items}),
            len({x.identity.account_id for x in items}),
            sum(x.telemetry.qa_passed for x in items) / total,
            sum(x.telemetry.blocked for x in items) / total,
            sum(x.telemetry.evidence_count > 0 for x in items) / total,
            sum(x.telemetry.drift_detected for x in items) / total,
            sum(x.telemetry.revalidation_triggered for x in items) / total,
        )
