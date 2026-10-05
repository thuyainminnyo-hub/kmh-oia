"""Unified snapshot of a continuous operating-intelligence cycle."""

from dataclasses import dataclass

from .continuous_intelligence_orchestrator import IntelligenceCycle
from .execution_telemetry import SystemHealthSnapshot


@dataclass(frozen=True)
class OperatingCycleSnapshot:
    health: SystemHealthSnapshot
    signal_count: int
    pending_decision_count: int
    decision_ids: tuple[str, ...]


class OperatingCycleMonitor:
    """Expose one deterministic view of health, signals, and governance backlog."""

    def snapshot(self, cycle: IntelligenceCycle) -> OperatingCycleSnapshot:
        decision_ids = tuple(item.decision_id for item in cycle.ingested)
        return OperatingCycleSnapshot(
            health=cycle.snapshot,
            signal_count=len(cycle.signals),
            pending_decision_count=len(decision_ids),
            decision_ids=decision_ids,
        )
