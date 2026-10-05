"""Orchestrate approved intelligence decisions through Command Center and runtime."""

from dataclasses import dataclass

from .decision_command_bridge import AppliedDecision, DecisionCommandBridge
from .decision_queue import DecisionQueue
from .live_operating_console import LiveOperatingConsole
from .live_runtime_bridge import ExecutionRecord, LiveRuntimeBridge


@dataclass(frozen=True)
class GovernedExecution:
    applied_decision: AppliedDecision
    execution: ExecutionRecord


class GovernedDecisionOrchestrator:
    """Execute only decisions that have explicitly crossed governance approval."""

    def __init__(
        self,
        queue: DecisionQueue,
        console: LiveOperatingConsole,
        runtime_bridge: LiveRuntimeBridge | None = None,
        command_bridge: DecisionCommandBridge | None = None,
    ) -> None:
        self.queue = queue
        self.console = console
        self.command_bridge = command_bridge or DecisionCommandBridge()
        self.runtime_bridge = runtime_bridge or LiveRuntimeBridge(console)

    def execute_approved(
        self,
        decision_id: str,
        *,
        expected_output: str,
        priority: str = "P2",
        standard=None,
        applied_rule: str | None = None,
        source_adaptation_id: str | None = None,
        observed_effect: float | None = None,
        outcome_positive: bool | None = None,
    ) -> GovernedExecution:
        decision = next(
            (item for item in self.queue._items if item.id == decision_id),
            None,
        )
        if decision is None:
            raise KeyError(decision_id)
        if decision.status != "APPROVED":
            raise PermissionError("only approved decisions can reach runtime")

        applied = self.command_bridge.apply(
            self.queue,
            self.console,
            decision_id,
            expected_output=expected_output,
            priority=priority,
        )
        execution = self.runtime_bridge.execute(
            applied.command_id,
            standard=standard,
            applied_rule=applied_rule,
            source_adaptation_id=source_adaptation_id,
            observed_effect=observed_effect,
            outcome_positive=outcome_positive,
        )
        return GovernedExecution(applied, execution)
