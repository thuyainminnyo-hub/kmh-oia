"""Bridge approved intelligence decisions into executable commands."""

from dataclasses import dataclass

from .decision_queue import DecisionItem, DecisionQueue
from .live_operating_console import Command, LiveOperatingConsole


@dataclass(frozen=True)
class AppliedDecision:
    decision_id: str
    command_id: str
    objective: str
    expected_output: str


class DecisionCommandBridge:
    """Only approved decisions may create real Command Center work."""

    def apply(
        self,
        queue: DecisionQueue,
        console: LiveOperatingConsole,
        decision_id: str,
        *,
        expected_output: str,
        priority: str = "P2",
    ) -> AppliedDecision:
        if not expected_output.strip():
            raise ValueError("expected_output is required")
        decision = next(
            (item for item in queue._items if item.id == decision_id),
            None,
        )
        if decision is None:
            raise KeyError(decision_id)
        if decision.status != "APPROVED":
            raise ValueError("only approved decisions can become commands")
        command = console.add_command(
            objective=decision.recommended_action,
            priority=priority,
            owner=decision.owner,
            expected_output=expected_output,
            next_action=decision.recommended_action,
            source_decision_id=decision.id,
        )
        return AppliedDecision(
            decision_id=decision.id,
            command_id=command.id,
            objective=command.objective,
            expected_output=command.expected_output,
        )
