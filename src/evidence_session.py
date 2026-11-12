"""Session/task lifecycle evidence state machine for the local KMH pilot.

Inspired by the November 2026 SCITT Agent Execution Evidence Internet-Draft.
This is not a wire-compatible profile implementation and does not sign/register
receipts. It enforces local sequencing invariants before a production evidence
service is connected.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionEvent:
    sequence: int
    task_id: str
    event_type: str
    target: str | None = None
    parent_sequence: int | None = None
    request_digest: str | None = None
    decision: str | None = None
    resolves_sequence: int | None = None
    reason: str | None = None


class EvidenceSessionLedger:
    """Fail-closed task and decision sequencing with confirmation correlation."""

    def __init__(self) -> None:
        self._events: list[SessionEvent] = []
        self._active_task: str | None = None
        self._pending: dict[int, SessionEvent] = {}
        self._decisions: dict[int, SessionEvent] = {}

    @property
    def events(self) -> tuple[SessionEvent, ...]:
        return tuple(self._events)

    @property
    def active_task(self) -> str | None:
        return self._active_task

    def _append(self, event: SessionEvent) -> SessionEvent:
        if event.sequence != len(self._events) + 1:
            raise ValueError("event sequence must be contiguous")
        self._events.append(event)
        return event

    def start_task(self, task_id: str) -> SessionEvent:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task ID is required")
        if self._active_task is not None:
            raise ValueError("another task is already active")
        self._active_task = task_id
        return self._append(SessionEvent(
            sequence=len(self._events) + 1,
            task_id=task_id,
            event_type="task_start",
        ))

    def record_decision(
        self, *, target: str, request_digest: str,
        decision: str, parent_sequence: int | None = None,
    ) -> SessionEvent:
        task_id = self._require_active_task()
        if decision not in {"allow", "confirm", "block"}:
            raise ValueError("decision must be allow, confirm, or block")
        if not target.strip() or not self._is_digest(request_digest):
            raise ValueError("target and SHA-256 request digest are required")
        if parent_sequence is not None:
            parent = self._event_at(parent_sequence)
            if parent.task_id != task_id:
                raise ValueError("parent event belongs to another task")
            if parent.event_type not in {"task_start", "decision", "confirm_outcome"}:
                raise ValueError("invalid causal parent event")
        event = self._append(SessionEvent(
            sequence=len(self._events) + 1,
            task_id=task_id,
            event_type="decision",
            target=target,
            parent_sequence=parent_sequence,
            request_digest=request_digest,
            decision=decision,
        ))
        self._decisions[event.sequence] = event
        if decision == "confirm":
            self._pending[event.sequence] = event
        return event

    def resolve_confirmation(
        self, *, confirm_sequence: int, decision: str,
        target: str, request_digest: str,
    ) -> SessionEvent:
        task_id = self._require_active_task()
        if decision not in {"allow", "block"}:
            raise ValueError("confirmation outcome must be allow or block")
        original = self._pending.get(confirm_sequence)
        if original is None:
            raise ValueError("confirmation is unknown, already resolved, or not pending")
        if original.task_id != task_id:
            raise ValueError("confirmation belongs to another task")
        if (original.target != target or original.request_digest != request_digest):
            raise ValueError("confirmation outcome does not match original action")
        event = self._append(SessionEvent(
            sequence=len(self._events) + 1,
            task_id=task_id,
            event_type="confirm_outcome",
            target=target,
            parent_sequence=original.parent_sequence,
            request_digest=request_digest,
            decision=decision,
            resolves_sequence=confirm_sequence,
        ))
        self._pending.pop(confirm_sequence)
        self._decisions[event.sequence] = event
        return event

    def record_tool_result(
        self, *, decision_sequence: int, target: str,
        request_digest: str, output_digest: str,
    ) -> SessionEvent:
        task_id = self._require_active_task()
        decision_event = self._decisions.get(decision_sequence)
        if decision_event is None or decision_event.task_id != task_id:
            raise ValueError("no decision exists for this task")
        if decision_event.decision != "allow":
            raise ValueError("tool result requires an allow decision")
        if decision_event.target != target or decision_event.request_digest != request_digest:
            raise ValueError("tool result does not match authorized action")
        if not self._is_digest(output_digest):
            raise ValueError("output digest must be SHA-256")
        return self._append(SessionEvent(
            sequence=len(self._events) + 1,
            task_id=task_id,
            event_type="tool_result",
            target=target,
            parent_sequence=decision_sequence,
            request_digest=request_digest,
            decision="completed",
            reason=output_digest,
        ))

    def end_task(self) -> tuple[SessionEvent, ...]:
        task_id = self._require_active_task()
        auto_blocks = []
        for confirm_sequence, original in sorted(tuple(self._pending.items())):
            event = self._append(SessionEvent(
                sequence=len(self._events) + 1,
                task_id=task_id,
                event_type="confirm_outcome",
                target=original.target,
                parent_sequence=original.parent_sequence,
                request_digest=original.request_digest,
                decision="block",
                resolves_sequence=confirm_sequence,
                reason="task_closed_with_pending_confirmation",
            ))
            self._pending.pop(confirm_sequence)
            self._decisions[event.sequence] = event
            auto_blocks.append(event)
        self._append(SessionEvent(
            sequence=len(self._events) + 1,
            task_id=task_id,
            event_type="task_end",
        ))
        self._active_task = None
        return tuple(auto_blocks)

    def _require_active_task(self) -> str:
        if self._active_task is None:
            raise ValueError("no active task")
        return self._active_task

    def _event_at(self, sequence: int) -> SessionEvent:
        if sequence < 1 or sequence > len(self._events):
            raise ValueError("causal parent sequence does not exist")
        return self._events[sequence - 1]

    @staticmethod
    def _is_digest(value: str) -> bool:
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            int(value, 16)
        except ValueError:
            return False
        return True
