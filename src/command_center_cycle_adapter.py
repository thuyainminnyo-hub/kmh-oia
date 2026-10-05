"""Adapt operating-cycle state into a Command Center view."""

from dataclasses import dataclass

from .decision_queue import DecisionQueue
from .operating_cycle_monitor import OperatingCycleSnapshot
from .live_operating_console import ConsoleSnapshot


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
        console: ConsoleSnapshot,
    ) -> CommandCenterView:
        return CommandCenterView(
            primary_objective=console.primary_objective,
            health=cycle.health,
            signals=cycle.signal_count,
            pending_decisions=cycle.pending_decision_count,
            decision_ids=cycle.decision_ids,
            blockers=console.blockers,
            evidence_pending=console.evidence_pending,
            qa_pending=console.qa_pending,
        )
