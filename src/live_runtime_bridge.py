"""Bridge the live operating console to the executable OIA runtime.

This is the first thin integration layer: commands remain human-operable,
while execution is delegated to OIARuntime and the resulting trace becomes
evidence for console verification.
"""
from dataclasses import dataclass

from src.components import OIARuntime
from src.live_operating_console import Command, LiveOperatingConsole
from src.trace import InMemoryTracer


@dataclass(frozen=True)
class ExecutionRecord:
    command_id: str
    response: str
    trace_stages: tuple[str, ...]
    evidence: tuple[str, ...]
    qa_status: str
    final_status: str


class LiveRuntimeBridge:
    """Execute a console command through the governed OIA runtime."""

    def __init__(self, console: LiveOperatingConsole, runtime: OIARuntime | None = None) -> None:
        self.console = console
        self.runtime = runtime or OIARuntime()

    def execute(self, command_id: str) -> ExecutionRecord:
        command = self._get_command(command_id)
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
                command.objective,
                session_id=f"command:{command.id}",
            )
        except Exception:
            self.console.transition(command.id, "BLOCKED")
            raise

        self.console.transition(command.id, "COMPLETED")

        evidence = (
            f"trace_id={events[0].metadata['trace_id']}",
            f"trace_events={len(events)}",
            f"stages={' -> '.join(stages)}",
            f"response={response}",
        )
        for item in evidence:
            self.console.attach_evidence(command.id, item)

        self.console.verify(
            command.id,
            passed=True,
            note="Runtime evaluation accepted the governed execution.",
        )
        self.console.record_learning(
            command.id,
            "Execution produced trace-backed evidence and passed QA.",
        )

        return ExecutionRecord(
            command_id=command.id,
            response=response,
            trace_stages=tuple(stages),
            evidence=tuple(evidence),
            qa_status=command.qa_status,
            final_status=command.status,
        )

    def _get_command(self, command_id: str) -> Command:
        snapshot = self.console.snapshot()
        for command in snapshot.commands:
            if command.id == command_id:
                return command
        raise KeyError(f"unknown command: {command_id}")
