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
    source_action_reason: str | None = None,
    source_decision_id: str | None = None


@dataclass(frozen=True)
class ConsoleSnapshot:
    date: str
    primary_objective: str
    commands: list[Command]
    blockers: tuple[str, ...]
    evidence_pending: int
    qa_pending: int

class LiveOperatingConsole:
    """Small executable command-center state machine."""

    def __init__(self, date: str = "", primary_objective: str = "") -> None:
        self.date = date.strip()
        self.primary_objective = primary_objective.strip()
        self._commands: dict[str, Command] = {}

    def add_command(
        self,
        *args: object,
        objective: str | None = None,
        priority: Priority | None = None,
        owner: str | None = None,
        expected_output: str | None = None,
        next_action: str = "",
        source_action_kind: str | None = None,
        source_action_priority: int | None = None,
        source_action_reason: str | None = None,
        source_decision_id: str | None = None,
    ) -> Command:
        # Preserve compatibility with the earlier positional command API while
        # keeping the current keyword-based API canonical.
        if len(args) == 1 and isinstance(args[0], Command):
            if any(value is not None for value in (objective, priority, owner, expected_output)):
                raise TypeError("command object cannot be combined with command fields")
            command = args[0]
            self._commands[command.id] = command
            return command
        if args:
            # Support the legacy mixed form: id as positional, remaining fields as keywords.
            if len(args) == 1 and all(value is not None for value in (objective, priority, owner, expected_output)):
                command_id = str(args[0])
                command = Command(
                    command_id,
                    objective.strip(),
                    priority,
                    owner.strip(),
                    expected_output.strip(),
                    next_action=next_action.strip(),
                    source_action_kind=source_action_kind,
                    source_action_priority=source_action_priority,
                    source_action_reason=source_action_reason,
                    source_decision_id=source_decision_id,
                )
                self._commands[command.id] = command
                return command
            if len(args) not in {5, 6}:
                raise TypeError("positional add_command expects id, priority, objective, owner, expected_output[, next_action]")
            if any(value is not None for value in (objective, priority, owner, expected_output)):
                raise TypeError("positional command fields cannot be combined with keyword command fields")
            command_id, positional_priority, positional_objective, positional_owner, positional_output = args[:5]
            objective = str(positional_objective)
            priority = positional_priority  # type: ignore[assignment]
            owner = str(positional_owner)
            expected_output = str(positional_output)
            if len(args) == 6:
                next_action = str(args[5])
            command = Command(
                str(command_id),
                objective.strip(),
                priority,  # type: ignore[arg-type]
                owner.strip(),
                expected_output.strip(),
                next_action=next_action.strip(),
                source_action_kind=source_action_kind,
                source_action_priority=source_action_priority,
                source_action_reason=source_action_reason,
                source_decision_id=source_decision_id,
            )
        else:
            if objective is None or priority is None or owner is None or expected_output is None:
                raise TypeError("objective, priority, owner, and expected_output are required")
            for value, name in ((objective, "objective"), (owner, "owner"), (expected_output, "expected_output")):
                if not value.strip():
                    raise ValueError(f"{name} is required")
            command = Command(
                str(uuid4()),
                objective.strip(),
                priority,
                owner.strip(),
                expected_output.strip(),
                next_action=next_action.strip(),
                source_action_kind=source_action_kind,
                source_action_priority=source_action_priority,
                source_action_reason=source_action_reason,
                source_decision_id=source_decision_id,
            )
        self._commands[command.id] = command
        return command

    @property
    def blockers(self) -> tuple[str, ...]:
        return self.snapshot().blockers

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
        commands = list(sorted(self._commands.values(), key=lambda c: (c.priority, c.status, c.id)))
        blockers = tuple(c.objective for c in commands if c.status == "BLOCKED")
        evidence_pending = sum(c.status == "COMPLETED" and not c.evidence for c in commands)
        qa_pending = sum(c.status == "COMPLETED" and bool(c.evidence) for c in commands)
        return ConsoleSnapshot(self.date, self.primary_objective, commands, blockers, evidence_pending, qa_pending)

    def _get(self, command_id: str) -> Command:
        try: return self._commands[command_id]
        except KeyError as exc: raise KeyError(f"unknown command: {command_id}") from exc
