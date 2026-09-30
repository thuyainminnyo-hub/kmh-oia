"""Deterministic memory boundary for KMH OIA integration."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MemoryEntry:
    key: str
    value: str


class MemorySnapshot(Protocol):
    """Opaque snapshot representing one session's recoverable memory."""

    pass


class MemoryStore(Protocol):
    """Boundary for retrieving, updating, and restoring session memory."""

    def retrieve(self, session_id: str) -> list[MemoryEntry]: ...

    def update(self, session_id: str, key: str, value: str) -> None: ...

    def snapshot(self, session_id: str) -> list[MemoryEntry]: ...

    def restore(self, session_id: str, snapshot: list[MemoryEntry]) -> None: ...


class InMemoryMemoryStore:
    """Small deterministic session memory used by the integrated runtime."""

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, str]] = {}

    def retrieve(self, session_id: str) -> list[MemoryEntry]:
        return [MemoryEntry(key, value) for key, value in self._entries.get(session_id, {}).items()]

    def update(self, session_id: str, key: str, value: str) -> None:
        self._validate(session_id, key)
        self._entries.setdefault(session_id, {})[key] = value

    def snapshot(self, session_id: str) -> list[MemoryEntry]:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        return self.retrieve(session_id)

    def restore(self, session_id: str, snapshot: list[MemoryEntry]) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        self._entries[session_id] = {entry.key: entry.value for entry in snapshot}

    @staticmethod
    def _validate(session_id: str, key: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        if not key.strip():
            raise ValueError("key must not be empty")
