"""Append-only JSONL persistence for KMH OIA evidence objects.

This local v1 store provides process-level duplicate protection and read-back.
It is not a multi-process database, distributed lock, or production-grade
storage service. Keep evidence fields free of secrets and unnecessary PII.
"""
from dataclasses import asdict
import json
from pathlib import Path
from threading import RLock

from src.evidence_object import EvidenceObject


class JsonlEvidenceStore:
    """Append evidence records without allowing updates to existing IDs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    evidence = EvidenceObject(**record)
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    raise ValueError(
                        f"invalid evidence record at line {line_number}"
                    ) from exc
                if evidence.evidence_id in self._index:
                    raise ValueError(
                        f"duplicate evidence_id in store: {evidence.evidence_id}"
                    )
                self._index[evidence.evidence_id] = asdict(evidence)

    def append(self, evidence: EvidenceObject) -> None:
        """Append a new object; duplicate IDs are rejected, never overwritten."""
        if not isinstance(evidence, EvidenceObject):
            raise TypeError("evidence must be an EvidenceObject")
        record = asdict(evidence)
        with self._lock:
            if evidence.evidence_id in self._index:
                raise ValueError(f"evidence_id already exists: {evidence.evidence_id}")
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\\n")
                stream.flush()
            self._index[evidence.evidence_id] = record

    def get(self, evidence_id: str) -> EvidenceObject | None:
        """Return a reconstructed record, or None if the ID is unknown."""
        with self._lock:
            record = self._index.get(evidence_id)
            return EvidenceObject(**record) if record is not None else None

    def list_by_trace(self, trace_id: str) -> list[EvidenceObject]:
        """Return records carrying the requested trace ID, in append order."""
        if not isinstance(trace_id, str) or not trace_id.strip():
            raise ValueError("trace_id must be a nonblank string")
        with self._lock:
            return [
                EvidenceObject(**record)
                for record in self._index.values()
                if record.get("trace_id") == trace_id
            ]
