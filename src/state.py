"""Minimal in-memory session state for the KMH OIA first runtime slice."""

from dataclasses import dataclass, field


@dataclass
class SessionState:
    values: dict[str, str] = field(default_factory=dict)


class StateStore:
    """Keep isolated state for each session within one runtime process."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        return self._sessions.setdefault(session_id, SessionState())

    def set(self, session_id: str, key: str, value: str) -> None:
        if not key.strip():
            raise ValueError("key must not be empty")
        self.get(session_id).values[key] = value
