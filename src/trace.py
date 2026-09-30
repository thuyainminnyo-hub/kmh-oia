"""Structured observability boundary for KMH OIA runtime events."""

from dataclasses import dataclass, field
from typing import Protocol


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
