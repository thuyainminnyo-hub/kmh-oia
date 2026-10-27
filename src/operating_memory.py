"""Operating memory for the OIA live execution loop.

Memory records preserve the chain from intent to verified outcome and the
change that should influence the next command.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class OperatingMemoryRecord:
    command_id: str
    timestamp: str
    wanted: str
    did: str
    actual: str
    verified: str
    decision: str
    learned: str
    changed: str
    next_command: str
    confidence: float = 1.0
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperatingMemory:
    """Append-only, local-first memory store with event-level deduplication.

    The lock protects threads sharing this instance. It does not provide
    cross-process or multi-host transactions; use a shared database with a
    unique constraint for that deployment boundary.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._records: list[OperatingMemoryRecord] = []
        self._lock = RLock()
        if self.path and self.path.exists():
            self._load()

    def record(
        self,
        *,
        command_id: str,
        wanted: str,
        did: str,
        actual: str,
        verified: str,
        decision: str,
        learned: str,
        changed: str,
        next_command: str,
        confidence: float = 1.0,
        event_id: str | None = None,
    ) -> OperatingMemoryRecord:
        if not isinstance(command_id, str) or not command_id.strip():
            raise ValueError("command_id is required")
        if event_id is not None and (
            not isinstance(event_id, str) or not event_id.strip()
        ):
            raise ValueError("event_id must be a non-empty string when provided")
        fields = {
            "wanted": wanted,
            "did": did,
            "actual": actual,
            "verified": verified,
            "decision": decision,
            "learned": learned,
            "changed": changed,
            "next_command": next_command,
        }
        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0.0 <= confidence <= 1.0
        ):
            raise ValueError("confidence must be between 0 and 1")

        normalized_event_id = event_id.strip() if event_id is not None else None
        with self._lock:
            if normalized_event_id is not None:
                for existing in self._records:
                    if existing.event_id == normalized_event_id:
                        return existing

            record = OperatingMemoryRecord(
                command_id=command_id.strip(),
                timestamp=datetime.now(timezone.utc).isoformat(),
                **{name: value.strip() for name, value in fields.items()},
                confidence=float(confidence),
                event_id=normalized_event_id,
            )
            self._records.append(record)
            try:
                self._persist()
            except Exception:
                self._records.pop()
                raise
            return record

    def recent(self, limit: int = 20) -> tuple[OperatingMemoryRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._lock:
            return tuple(self._records[-limit:][::-1])

    def search(self, query: str, limit: int = 20) -> tuple[OperatingMemoryRecord, ...]:
        if not query.strip():
            raise ValueError("query is required")
        if limit < 1:
            raise ValueError("limit must be positive")
        needle = query.strip().lower()
        with self._lock:
            matches = [
                record for record in reversed(self._records)
                if needle in json.dumps(record.to_dict(), ensure_ascii=False).lower()
            ]
            return tuple(matches[:limit])

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [r.to_dict() for r in self._records], ensure_ascii=False, indent=2
        )
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.path)

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        records = []
        seen_event_ids = set()
        for item in raw:
            # Backward-compatible with records written before event_id existed.
            item.setdefault("event_id", None)
            record = OperatingMemoryRecord(**item)
            if record.event_id is not None:
                if record.event_id in seen_event_ids:
                    raise ValueError("duplicate event_id found in persisted operating memory")
                seen_event_ids.add(record.event_id)
            records.append(record)
        self._records = records
