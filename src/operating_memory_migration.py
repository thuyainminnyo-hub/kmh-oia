"""Non-destructive, resumable staging migration helpers for legacy memory JSON."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Callable
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

def _existing_imports(target: SQLiteLearningAdmissionRepository, source_hash: str, records: list[OperatingMemoryRecord]) -> set[int]:
    """Validate all existing target rows as a consistent subset of this exact source."""
    with target._connect() as connection:
        rows = connection.execute(
            "SELECT a.admission_key, a.fingerprint, r.record_json, e.event_json "
            "FROM learning_admissions a "
            "LEFT JOIN learning_records r USING(admission_key) "
            "LEFT JOIN admission_audit_events e USING(admission_key)"
        ).fetchall()
        proposals = int(connection.execute("SELECT COUNT(*) FROM adaptation_proposals").fetchone()[0])
    if proposals:
        raise MemoryMigrationError("Staging target contains adaptation proposals; refusing to resume.")
    indices: set[int] = set()
    for row in rows:
        try:
            event = json.loads(row["event_json"]) if row["event_json"] else {}
            record = json.loads(row["record_json"]) if row["record_json"] else {}
            index = int(event["source_record_index"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise MemoryMigrationError("Target contains rows that are not a valid resumable migration subset.") from exc
        if event.get("kind") != "LEGACY_MEMORY_IMPORTED" or event.get("source_file_sha256") != source_hash:
            raise MemoryMigrationError("Target rows belong to another source or workflow; refusing resume.")
        if index < 0 or index >= len(records) or index in indices:
            raise MemoryMigrationError("Target contains an invalid or duplicate source record index.")
        expected = records[index].to_dict()
        digest = record_hash(expected)
        expected_key = f"legacy-import:{index}:{digest}"
        if row["admission_key"] != expected_key or row["fingerprint"] != "sha256:" + digest:
            raise MemoryMigrationError("Existing migration key/fingerprint does not match the source snapshot.")
        if record != expected or event.get("source_record_sha256") != digest:
            raise MemoryMigrationError("Existing migrated record hash does not match the source snapshot.")
        indices.add(index)
    counts = target.counts()
    expected_counts = len(indices)
    if any(counts[name] != expected_counts for name in ("learning_admissions", "learning_records", "admission_audit_events")):
        raise MemoryMigrationError("Target row counts are inconsistent; refusing resume.")
    return indices

def import_memory_snapshot(
    source_path: str | Path,
    target: SQLiteLearningAdmissionRepository,
    *,
    after_record: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    """Import/resume into a staging DB, only for the exact same source snapshot.

    Each record commit is atomic. If interrupted, rerun against the same unchanged
    source and target: already verified rows are skipped and missing rows are added.
    This is resumable, not a single whole-batch transaction.
    """
    records, file_hash = load_memory_snapshot(source_path)
    completed = _existing_imports(target, file_hash, records)
    hashes = [record_hash(record.to_dict()) for record in records]
    resumed_count = len(completed)
    for index, record in enumerate(records):
        if index in completed:
            continue
        payload = record.to_dict()
        digest = hashes[index]
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
        if after_record:
            after_record(index)
    verified = _existing_imports(target, file_hash, records)
    counts = target.counts()
    if verified != set(range(len(records))) or counts["learning_records"] != len(records):
        raise MemoryMigrationError("Final staging count/hash reconciliation failed.")
    return {"source_file_sha256": file_hash, "source_record_count": len(records),
            "source_record_hashes": hashes, "target_counts": counts,
            "resumed_existing_count": resumed_count, "reconciled": True}

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
