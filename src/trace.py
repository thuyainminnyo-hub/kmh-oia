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

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
