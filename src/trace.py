"""Structured observability boundary for KMH OIA runtime events."""

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class ExecutionContext:
    """Consistent identifiers carried across one runtime execution."""

    request_id: str
    session_id: str
    workflow_id: str
    task_id: str
    agent_id: str
    trace_id: str

    @classmethod
    def create(cls, session_id: str) -> "ExecutionContext":
        return cls(
            request_id=str(uuid4()),
            session_id=session_id,
            workflow_id=str(uuid4()),
            task_id=str(uuid4()),
            agent_id=str(uuid4()),
            trace_id=str(uuid4()),
        )


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    status: str
    metadata: dict[str, str] = field(default_factory=dict)


class Tracer(Protocol):
    """Boundary for recording runtime lifecycle events."""

    def emit(self, event: TraceEvent) -> None: ...


class InMemoryTracer:
    """Deterministic tracer that retains an ordered event list."""

    REQUIRED_CONTEXT_KEYS = (
        "request_id", "session_id", "workflow_id",
        "task_id", "agent_id", "trace_id",
    )

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        if not event.stage.strip():
            raise ValueError("trace stage must not be empty")
        if not event.status.strip():
            raise ValueError("trace status must not be empty")
        missing = [key for key in self.REQUIRED_CONTEXT_KEYS if key not in event.metadata]
        if missing:
            raise ValueError(
                "trace metadata missing required context: " + ", ".join(missing)
            )
        self.events.append(event)

    def validate_integrity(self) -> None:
        """Validate context continuity and terminal status for a trace."""
        if not self.events:
            raise ValueError("trace must contain at least one event")
        baseline = {
            key: self.events[0].metadata[key]
            for key in self.REQUIRED_CONTEXT_KEYS
        }
        for event in self.events:
            current = {
                key: event.metadata[key]
                for key in self.REQUIRED_CONTEXT_KEYS
            }
            if current != baseline:
                raise ValueError("trace execution context is inconsistent")
        if self.events[-1].status not in {
            "ok", "validation", "authorization", "recovery", "internal"
        }:
            raise ValueError("trace final status is invalid")
