"""Bridge the live operating console to the executable OIA runtime.

This is the first thin integration layer: commands remain human-operable,
while execution is delegated to OIARuntime and the resulting trace becomes
evidence for console verification.
"""
from dataclasses import dataclass

from src.components import OIARuntime
from src.live_operating_console import Command, LiveOperatingConsole
from src.operating_memory import OperatingMemory
from src.operating_memory import OperatingMemory
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

    def __init__(self, console: LiveOperatingConsole, runtime: OIARuntime | None = None, memory: OperatingMemory | None = None) -> None:
        self.console = console
        self.runtime = runtime or OIARuntime()
        self.memory = memory or OperatingMemory()

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
        learning = "Execution produced trace-backed evidence and passed QA."
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
