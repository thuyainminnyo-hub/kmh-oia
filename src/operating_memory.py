"""Operating memory for the OIA live execution loop.

Memory records preserve the chain from intent to verified outcome and the
change that should influence the next command.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperatingMemory:
    """Append-only, local-first memory store."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._records: list[OperatingMemoryRecord] = []
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
    ) -> OperatingMemoryRecord:
        if not command_id.strip():
            raise ValueError("command_id is required")
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
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        record = OperatingMemoryRecord(
            command_id=command_id.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            **{name: value.strip() for name, value in fields.items()},
            confidence=confidence,
        )
        self._records.append(record)
        self._persist()
        return record

    def recent(self, limit: int = 20) -> tuple[OperatingMemoryRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return tuple(self._records[-limit:][::-1])

    def search(self, query: str, limit: int = 20) -> tuple[OperatingMemoryRecord, ...]:
        if not query.strip():
            raise ValueError("query is required")
        needle = query.strip().lower()
        matches = [
            record for record in reversed(self._records)
            if needle in json.dumps(record.to_dict(), ensure_ascii=False).lower()
        ]
        return tuple(matches[:limit])

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([r.to_dict() for r in self._records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._records = [OperatingMemoryRecord(**item) for item in raw]
