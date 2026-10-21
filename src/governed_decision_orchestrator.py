"""Orchestrate approved decisions through runtime and trusted learning admission."""

from dataclasses import dataclass

from .decision_command_bridge import AppliedDecision, DecisionCommandBridge
from .decision_queue import DecisionQueue
from .live_operating_console import LiveOperatingConsole
from .live_runtime_bridge import ExecutionRecord, LiveRuntimeBridge
from .trusted_decision_learning_service import (
    TrustedDecisionLearningResult,
    TrustedDecisionLearningService,
)


@dataclass(frozen=True)
class GovernedExecution:
    applied_decision: AppliedDecision
    execution: ExecutionRecord
    learning_feedback: TrustedDecisionLearningResult | None = None


class GovernedDecisionOrchestrator:
    """Execute only approved decisions and optionally route verified outcomes to learning."""

    def __init__(
        self,
        queue: DecisionQueue,
        console: LiveOperatingConsole,
        runtime_bridge: LiveRuntimeBridge | None = None,
        command_bridge: DecisionCommandBridge | None = None,
        learning_service: TrustedDecisionLearningService | None = None,
    ) -> None:
        self.queue = queue
        self.console = console
        self.command_bridge = command_bridge or DecisionCommandBridge()
        self.runtime_bridge = runtime_bridge or LiveRuntimeBridge(console)
        self.learning_service = learning_service

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
        learning_evidence_id: str | None = None,
        learning_policy_version: str | None = None,
        learning_next_command: str | None = None,
        source_record_id: str = "",
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
        # A receipt ID is only a lookup hint. The runtime verifier must fetch,
        # authenticate, freshness-check and attribute the actual provider receipt.
        request_learning = bool(
            self.learning_service is not None
            and source_record_id.strip()
            and learning_evidence_id
            and learning_policy_version
            and learning_next_command
        )
        execution = self.runtime_bridge.execute(
            applied.command_id,
            standard=standard,
            applied_rule=applied_rule,
            source_adaptation_id=source_adaptation_id,
            # The caller-supplied outcome signal must not influence runtime
            # revalidation when this execution is entering the trusted learning path.
            observed_effect=None if request_learning else observed_effect,
            outcome_positive=None if request_learning else outcome_positive,
            source_record_id=source_record_id if request_learning else "",
            verification_status="OUTCOME_LINKED" if request_learning else "OBSERVED",
            outcome_linked=request_learning,
        )

        learning_feedback = None
        if request_learning and self.learning_service is not None:
            learning_feedback = self.learning_service.capture_execution(
                decision,
                execution,
                evidence_id=learning_evidence_id or "",
                policy_version=learning_policy_version or "",
                next_command=learning_next_command or "",
            )
        return GovernedExecution(applied, execution, learning_feedback)
