"""Session state stores for the KMH OIA runtime."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Protocol


@dataclass
class SessionState:
    values: dict[str, str] = field(default_factory=dict)


class StateStoreContract(Protocol):
    """State boundary with snapshot/restore support for recovery."""

    def get(self, session_id: str) -> SessionState: ...

    def set(self, session_id: str, key: str, value: str) -> None: ...

    def snapshot(self, session_id: str) -> dict[str, str]: ...

    def restore(self, session_id: str, snapshot: dict[str, str]) -> None: ...


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

    def snapshot(self, session_id: str) -> dict[str, str]:
        return dict(self.get(session_id).values)

    def restore(self, session_id: str, snapshot: dict[str, str]) -> None:
        self.get(session_id).values = dict(snapshot)


class JsonFileStateStore(StateStore):
    """Persist session state to a local JSON file across process restarts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._sessions: dict[str, SessionState] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("state file must contain a JSON object")
        self._sessions = {
            session_id: SessionState(dict(values))
            for session_id, values in payload.items()
            if isinstance(session_id, str) and isinstance(values, dict)
        }

    def set(self, session_id: str, key: str, value: str) -> None:
        super().set(session_id, key, value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {
            session_id: state.values
            for session_id, state in self._sessions.items()
        }
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.path)
