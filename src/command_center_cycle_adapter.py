"""Adapt operating-cycle state into a Command Center view."""

from dataclasses import dataclass

from .decision_queue import DecisionQueue
from .operating_cycle_monitor import OperatingCycleSnapshot
from .live_operating_console import ConsoleSnapshot, LiveOperatingConsole


@dataclass(frozen=True)
class CommandCenterView:
    primary_objective: str
    health: object
    signals: int
    pending_decisions: int
    decision_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    evidence_pending: int
    qa_pending: int


class CommandCenterCycleAdapter:
    """Create an operational Command Center view without changing execution state."""

    def build(
        self,
        cycle: OperatingCycleSnapshot,
        console: LiveOperatingConsole | ConsoleSnapshot,
    ) -> CommandCenterView:
        snapshot = console.snapshot() if isinstance(console, LiveOperatingConsole) else console
        return CommandCenterView(
            primary_objective=snapshot.primary_objective,
            health=cycle.health,
            signals=cycle.signal_count,
            pending_decisions=cycle.pending_decision_count,
            decision_ids=cycle.decision_ids,
            blockers=snapshot.blockers,
            evidence_pending=snapshot.evidence_pending,
            qa_pending=snapshot.qa_pending,
        )
