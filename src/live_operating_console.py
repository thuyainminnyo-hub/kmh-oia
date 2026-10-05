"""Live operating console for the KMH OIA runtime.

The console is intentionally deterministic and local-first. It turns the
operating loop into explicit daily state without replacing the runtime's
execution, security, evidence, or evaluation boundaries.
"""
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

Priority = Literal["P1", "P2", "P3", "WAITING"]
Status = Literal[
    "INBOX", "QUALIFIED", "READY", "ACTIVE", "BLOCKED",
    "COMPLETED", "VERIFIED", "LEARNED", "CLOSED", "REWORK",
]


@dataclass
class Command:
    id: str
    objective: str
    priority: Priority
    owner: str
    expected_output: str
    status: Status = "INBOX"
    next_action: str = ""
    evidence: list[str] = field(default_factory=list)
    qa_status: str = "PENDING"
    learning: str = ""
    source_action_kind: str | None = None
    source_action_priority: int | None = None
    source_action_reason: str | None = None


@dataclass(frozen=True)
class ConsoleSnapshot:
    date: str
    primary_objective: str
    commands: tuple[Command, ...]
    blockers: tuple[str, ...]
    evidence_pending: int
    qa_pending: int

class LiveOperatingConsole:
    """Small executable command-center state machine."""

    def __init__(self, *, date: str, primary_objective: str = "") -> None:
        if not date.strip():
            raise ValueError("date is required")
        self.date = date.strip()
        self.primary_objective = primary_objective.strip()
        self._commands: dict[str, Command] = {}

    def add_command(self, *, objective: str, priority: Priority, owner: str, expected_output: str, next_action: str = "", source_action_kind: str | None = None, source_action_priority: int | None = None, source_action_reason: str | None = None) -> Command:
        for value, name in ((objective, "objective"), (owner, "owner"), (expected_output, "expected_output")):
            if not value.strip():
                raise ValueError(f"{name} is required")
        command = Command(str(uuid4()), objective.strip(), priority, owner.strip(), expected_output.strip(), next_action=next_action.strip(), source_action_kind=source_action_kind, source_action_priority=source_action_priority, source_action_reason=source_action_reason)
        self._commands[command.id] = command
        return command

    def transition(self, command_id: str, status: Status) -> Command:
        command = self._get(command_id)
        allowed = {"INBOX":{"QUALIFIED"},"QUALIFIED":{"READY","WAITING"},"READY":{"ACTIVE"},"ACTIVE":{"BLOCKED","COMPLETED"},"BLOCKED":{"ACTIVE"},"COMPLETED":{"VERIFIED","REWORK"},"REWORK":{"ACTIVE"},"VERIFIED":{"LEARNED","CLOSED"},"WAITING":{"READY"},"CLOSED":set()}
        if status not in allowed[command.status]:
            raise ValueError(f"invalid transition: {command.status} -> {status}")
        command.status = status
        return command

    def attach_evidence(self, command_id: str, evidence: str) -> Command:
        if not evidence.strip(): raise ValueError("evidence is required")
        command = self._get(command_id)
        if command.status not in {"COMPLETED","REWORK","ACTIVE"}: raise ValueError("evidence can only be attached to active work")
        command.evidence.append(evidence.strip())
        return command

    def verify(self, command_id: str, *, passed: bool, note: str = "") -> Command:
        command = self._get(command_id)
        if command.status != "COMPLETED": raise ValueError("only completed commands can be verified")
        if not command.evidence: raise ValueError("verification requires evidence")
        command.qa_status = "PASS" if passed else "FAIL"
        command.status = "VERIFIED" if passed else "REWORK"
        if note.strip(): command.learning = note.strip()
        return command

    def record_learning(self, command_id: str, learning: str) -> Command:
        command = self._get(command_id)
        if command.status != "VERIFIED": raise ValueError("learning requires verified work")
        if not learning.strip(): raise ValueError("learning is required")
        command.learning = learning.strip()
        command.status = "LEARNED"
        return command

    def snapshot(self) -> ConsoleSnapshot:
        commands = tuple(sorted(self._commands.values(), key=lambda c: (c.priority, c.status, c.id)))
        blockers = tuple(c.objective for c in commands if c.status == "BLOCKED")
        evidence_pending = sum(c.status == "COMPLETED" and not c.evidence for c in commands)
        qa_pending = sum(c.status == "COMPLETED" and bool(c.evidence) for c in commands)
        return ConsoleSnapshot(self.date, self.primary_objective, commands, blockers, evidence_pending, qa_pending)

    def _get(self, command_id: str) -> Command:
        try: return self._commands[command_id]
        except KeyError as exc: raise KeyError(f"unknown command: {command_id}") from exc
