"""Bridge the live operating console to the executable OIA runtime."""
from dataclasses import dataclass

from src.components import OIARuntime
from src.live_operating_console import Command, LiveOperatingConsole
from src.operating_memory import OperatingMemory
from src.trace import InMemoryTracer
from src.standard_control_plane import StandardControlPlane, StandardControlResult
from src.standardization_engine import OperatingStandard
from src.active_standard_resolver import ActiveStandardResolver
from src.standard_runtime_bridge import StandardRuntimeBridge
from src.runtime_revalidation_pipeline import RuntimeRevalidationPipeline, AutomaticRevalidationResult
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.operating_loop_record import OperatingLoopRecord
from uuid import uuid4


@dataclass(frozen=True)
class ExecutionRecord:
    command_id: str
    response: str
    trace_stages: tuple[str, ...]
    evidence: tuple[str, ...]
    qa_status: str
    final_status: str
    standard_feedback: StandardControlResult | None = None
    standard_id: str | None = None
    revalidation: AutomaticRevalidationResult | None = None
    telemetry: ExecutionTelemetry | None = None
    source_decision_id: str | None = None
    operating_loop: OperatingLoopRecord | None = None


class LiveRuntimeBridge:
    """Execute console commands through the governed OIA runtime."""

    def __init__(
        self,
        console: LiveOperatingConsole,
        runtime: OIARuntime | None = None,
        memory: OperatingMemory | None = None,
        control_plane: StandardControlPlane | None = None,
        standard_resolver: ActiveStandardResolver | None = None,
        standard_runtime_bridge: StandardRuntimeBridge | None = None,
        revalidation_pipeline: RuntimeRevalidationPipeline | None = None,
        telemetry_collector: ExecutionTelemetryCollector | None = None,
    ) -> None:
        self.console = console
        self.runtime = runtime or OIARuntime()
        self.memory = memory or OperatingMemory()
        self.control_plane = control_plane or StandardControlPlane()
        self.standard_resolver = standard_resolver or ActiveStandardResolver(
            self.control_plane.registry
        )
        self.standard_runtime_bridge = standard_runtime_bridge or StandardRuntimeBridge(
            self.control_plane
        )
        self.revalidation_pipeline = revalidation_pipeline or RuntimeRevalidationPipeline(
            self.control_plane
        )
        self.telemetry_collector = telemetry_collector or ExecutionTelemetryCollector()

    def execute(
        self,
        command_id: str,
        *,
        standard: OperatingStandard | None = None,
        applied_rule: str | None = None,
        source_adaptation_id: str | None = None,
        observed_effect: float | None = None,
        outcome_positive: bool | None = None,
    ) -> ExecutionRecord:
        command = self._get_command(command_id)
        selected_standard = standard
        if selected_standard is None and source_adaptation_id is not None:
            selected_standard = self.standard_resolver.resolve(source_adaptation_id).standard

        if selected_standard is not None:
            if applied_rule is None:
                raise ValueError("applied_rule is required when a standard is supplied")
            self.standard_runtime_bridge.authorize(
                selected_standard, command.id, applied_rule=applied_rule
            )

        if command.status == "INBOX":
            self.console.transition(command.id, "QUALIFIED")
        if command.status == "QUALIFIED":
            self.console.transition(command.id, "READY")
        if command.status == "READY":
            self.console.transition(command.id, "ACTIVE")
        if command.status != "ACTIVE":
            raise ValueError(f"command is not executable from {command.status}")

        tracer = InMemoryTracer()
        self.runtime.tracer = tracer
        try:
            response, stages, events = self.runtime.execute_detailed(
                command.objective, session_id=f"command:{command.id}"
            )
        except Exception:
            self.console.transition(command.id, "BLOCKED")
            raise

        self.console.transition(command.id, "COMPLETED")
        trace_id = events[0].metadata["trace_id"]
        evidence = (
            f"trace_id={trace_id}",
            f"trace_events={len(events)}",
            f"stages={' -> '.join(stages)}",
            f"response={response}",
            f"source_action_kind={command.source_action_kind or ''}",
            f"source_action_priority={command.source_action_priority if command.source_action_priority is not None else ''}",
            f"source_action_reason={command.source_action_reason or ''}",
        )
        for item in evidence:
            self.console.attach_evidence(command.id, item)

        self.console.verify(
            command.id,
            passed=True,
            note="Runtime evaluation accepted the governed execution.",
        )

        standard_feedback = None
        revalidation = None
        if selected_standard is not None:
            standard_feedback = self.control_plane.observe(
                selected_standard,
                command.id,
                applied_rule=applied_rule or "",
                evidence_id=trace_id,
            )
            if observed_effect is not None and outcome_positive is not None:
                revalidation = self.revalidation_pipeline.process(
                    selected_standard,
                    command.id,
                    applied_rule=applied_rule or "",
                    evidence_id=trace_id,
                    observed_effect=observed_effect,
                    outcome_positive=outcome_positive,
                )

        learning = "Runtime observation recorded: governed execution passed QA with trace evidence."
        telemetry = ExecutionTelemetry(
            command_id=command.id,
            qa_passed=command.qa_status == "PASS",
            blocked=False,
            rework=command.status == "REWORK",
            evidence_count=len(command.evidence),
            standard_compliant=(
                standard_feedback.compliance.compliant
                if standard_feedback is not None else None
            ),
            drift_detected=(
                standard_feedback.drift.drifted
                if standard_feedback is not None and standard_feedback.drift is not None else False
            ),
            revalidation_triggered=(
                revalidation is not None and revalidation.control_result.trigger is not None
            ),
            revalidation_verdict=(
                revalidation.control_result.revalidation.revalidation.verdict
                if revalidation is not None
                and revalidation.control_result.revalidation is not None
                else None
            ),
        )
        self.telemetry_collector.record(telemetry)
        self.console.record_learning(command.id, learning)
        self.memory.record(
            command_id=command.id,
            wanted=command.expected_output,
            did=command.objective,
            actual=response,
            verified="Runtime trace and evaluation passed QA.",
            decision="Accept governed execution.",
            learned=learning,
            changed="Carry evidence-first verification into the next command.",
            next_command=command.next_action or "Select the next highest-leverage command.",
        )

        return ExecutionRecord(
            command.id,
            response,
            tuple(stages),
            tuple(evidence),
            command.qa_status,
            command.status,
            standard_feedback,
            selected_standard.id if selected_standard else None,
            revalidation,
            telemetry,
            command.source_decision_id,
        )

    def _get_command(self, command_id: str) -> Command:
        for command in self.console.snapshot().commands:
            if command.id == command_id:
                return command
        raise KeyError(f"unknown command: {command_id}")
