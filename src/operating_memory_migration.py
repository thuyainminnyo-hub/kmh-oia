"""Non-destructive staging migration helpers for legacy operating-memory JSON."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any
from src.learning_admission_repository import SQLiteLearningAdmissionRepository
from src.operating_memory import OperatingMemoryRecord

class MemoryMigrationError(ValueError):
    """Raised when migration input or target is unsafe."""

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def record_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def load_memory_snapshot(source_path: str | Path) -> tuple[list[OperatingMemoryRecord], str]:
    path = Path(source_path)
    raw = path.read_bytes()
    try:
        values = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MemoryMigrationError("Legacy memory JSON is unreadable.") from exc
    if not isinstance(values, list):
        raise MemoryMigrationError("Legacy memory root must be a JSON list.")
    records = []
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise MemoryMigrationError(f"Record {index} must be an object.")
        try:
            records.append(OperatingMemoryRecord(**value))
        except (TypeError, ValueError) as exc:
            raise MemoryMigrationError(f"Record {index} has an invalid schema.") from exc
    return records, hashlib.sha256(raw).hexdigest()

def import_memory_snapshot(source_path: str | Path, target: SQLiteLearningAdmissionRepository) -> dict[str, Any]:
    """Import into an empty staging DB; never modify the source file."""
    source = Path(source_path)
    records, file_hash = load_memory_snapshot(source)
    empty = {"learning_admissions": 0, "learning_records": 0, "adaptation_proposals": 0, "admission_audit_events": 0}
    if target.counts() != empty:
        raise MemoryMigrationError("Target must be an empty staging repository.")
    hashes = []
    for index, record in enumerate(records):
        payload = record.to_dict()
        digest = record_hash(payload)
        key = f"legacy-import:{index}:{digest}"
        target.commit(
            admission_key=key, fingerprint="sha256:" + digest,
            learning_record=payload, adaptation_proposal=None,
            audit_event={"event_id": f"legacy-import-audit:{index}:{digest}", "admission_key": key,
                         "kind": "LEGACY_MEMORY_IMPORTED", "source_file_sha256": file_hash,
                         "source_record_index": index, "source_record_sha256": digest},
            result={"admitted": True, "migration": True, "source_file_sha256": file_hash,
                    "source_record_index": index, "source_record_sha256": digest},
        )
        hashes.append(digest)
    counts = target.counts()
    if counts["learning_records"] != len(records):
        raise MemoryMigrationError("Staging record count does not match source.")
    return {"source_file_sha256": file_hash, "source_record_count": len(records),
            "source_record_hashes": hashes, "target_counts": counts, "reconciled": True}

def export_memory_snapshot(target: SQLiteLearningAdmissionRepository, destination_path: str | Path) -> dict[str, Any]:
    """Export only legacy-import records, refusing to overwrite an existing backup."""
    destination = Path(destination_path)
    with target._connect() as connection:
        rows = connection.execute(
            "SELECT r.record_json FROM learning_admissions a "
            "JOIN learning_records r USING(admission_key) "
            "JOIN admission_audit_events e USING(admission_key) "
            "WHERE json_extract(e.event_json, '$.kind') = 'LEGACY_MEMORY_IMPORTED' "
            "ORDER BY json_extract(e.event_json, '$.source_record_index')"
        ).fetchall()
    values = [OperatingMemoryRecord(**json.loads(row["record_json"])).to_dict() for row in rows]
    try:
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(values, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise MemoryMigrationError("Destination exists; refusing to overwrite backup.") from exc
    return {"exported_record_count": len(values), "exported_record_hashes": [record_hash(v) for v in values]}
