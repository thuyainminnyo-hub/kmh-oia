"""Structured, privacy-aware observability boundary for KMH OIA runtime events.

Trace metadata is treated as untrusted input. The in-memory implementation
redacts known sensitive fields and common secret/PII patterns before retention.
It is a local test/runtime primitive, not a production telemetry exporter.
"""
from dataclasses import dataclass, field
import re
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
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id must be a non-empty string")
        return cls(
            request_id=str(uuid4()),
            session_id=session_id,
            workflow_id=str(uuid4()),
            task_id=str(uuid4()),
            agent_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def as_metadata(self) -> dict[str, str]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    status: str
    metadata: dict[str, str] = field(default_factory=dict)
    error_category: str | None = None
    duration_ms: int | None = None


class Tracer(Protocol):
    """Boundary for recording runtime lifecycle events."""

    def emit(self, event: TraceEvent) -> None: ...


class TraceRedactor:
    """Redact sensitive metadata keys and common secret/PII value patterns."""

    REDACTED = "[REDACTED]"
    SENSITIVE_KEY_PARTS = (
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "authorization", "cookie", "credential", "private_key",
    )
    VALUE_PATTERNS = (
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*[^\s,;]+"),
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    )

    def redact(self, metadata: dict[str, str]) -> dict[str, str]:
        if not isinstance(metadata, dict):
            raise ValueError("trace metadata must be a dictionary")
        if len(metadata) > 64:
            raise ValueError("trace metadata exceeds 64 fields")
        safe: dict[str, str] = {}
        for key, value in metadata.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("trace metadata keys must be non-empty strings")
            if not isinstance(value, str):
                raise ValueError("trace metadata values must be strings")
            if len(key) > 80 or len(value) > 2_000:
                raise ValueError("trace metadata field exceeds size limit")
            normalized_key = key.lower().replace("-", "_")
            if any(part in normalized_key for part in self.SENSITIVE_KEY_PARTS):
                safe[key] = self.REDACTED
                continue
            redacted = value
            for pattern in self.VALUE_PATTERNS:
                redacted = pattern.sub(self.REDACTED, redacted)
            safe[key] = redacted
        return safe


class InMemoryTracer:
    """Deterministic tracer that retains ordered, redacted events."""

    REQUIRED_CONTEXT_KEYS = (
        "request_id", "session_id", "workflow_id",
        "task_id", "agent_id", "trace_id",
    )
    TERMINAL_STATUSES = {
        "ok", "validation", "authorization", "recovery", "internal",
        "error", "denied", "timeout",
    }

    def __init__(self, redactor: TraceRedactor | None = None) -> None:
        self.events: list[TraceEvent] = []
        self._redactor = redactor or TraceRedactor()

    def emit(self, event: TraceEvent) -> None:
        if not isinstance(event, TraceEvent):
            raise ValueError("event must be a TraceEvent")
        if not isinstance(event.stage, str) or not event.stage.strip():
            raise ValueError("trace stage must not be empty")
        if not isinstance(event.status, str) or not event.status.strip():
            raise ValueError("trace status must not be empty")
        if event.error_category is not None and (
            not isinstance(event.error_category, str) or not event.error_category.strip()
        ):
            raise ValueError("error_category must be a non-empty string when provided")
        if event.duration_ms is not None and (
            isinstance(event.duration_ms, bool)
            or not isinstance(event.duration_ms, int)
            or event.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative integer")
        safe_metadata = self._redactor.redact(event.metadata)
        missing = [
            key for key in self.REQUIRED_CONTEXT_KEYS
            if key not in safe_metadata or not safe_metadata[key].strip()
        ]
        if missing:
            raise ValueError(
                "trace metadata missing required context: " + ", ".join(missing)
            )
        self.events.append(TraceEvent(
            stage=event.stage,
            status=event.status,
            metadata=safe_metadata,
            error_category=event.error_category,
            duration_ms=event.duration_ms,
        ))

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
        if self.events[-1].status not in self.TERMINAL_STATUSES:
            raise ValueError("trace final status is invalid")
