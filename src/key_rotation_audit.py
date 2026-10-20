"""Append-only hash-chained audit records for signing-key rotation events.

This is a local integrity-evident prototype. A hash chain can expose edits to
existing records but cannot prevent an attacker with write access from
rewriting the entire file. Production must forward entries to protected,
access-controlled, independently retained audit storage.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
from threading import RLock
from typing import Literal
import uuid


RotationAction = Literal["KEY_ACTIVATED", "KEY_DEPRECATED", "KEY_RETIRED"]
_GENESIS = "0" * 64
_LOCK = RLock()


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass(frozen=True)
class KeyRotationEvent:
    event_id: str
    action: RotationAction
    key_id: str
    actor_id: str
    reason: str
    accepted_key_ids: tuple[str, ...]
    previous_active_key_id: str | None
    occurred_at: str

    @classmethod
    def create(
        cls,
        action: RotationAction,
        key_id: str,
        actor_id: str,
        reason: str,
        accepted_key_ids: set[str] | tuple[str, ...],
        previous_active_key_id: str | None = None,
    ) -> "KeyRotationEvent":
        if action not in ("KEY_ACTIVATED", "KEY_DEPRECATED", "KEY_RETIRED"):
            raise ValueError("unsupported key rotation action")
        for field_name, value in (("key_id", key_id), ("actor_id", actor_id), ("reason", reason)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a nonblank string")
        if previous_active_key_id is not None and (
            not isinstance(previous_active_key_id, str) or not previous_active_key_id.strip()
        ):
            raise ValueError("previous_active_key_id must be nonblank when supplied")
        if not isinstance(accepted_key_ids, (set, tuple, list)):
            raise TypeError("accepted_key_ids must be a set, tuple, or list")
        if any(not isinstance(item, str) or not item.strip() for item in accepted_key_ids):
            raise ValueError("accepted_key_ids must contain only nonblank key IDs")
        if len(set(accepted_key_ids)) != len(accepted_key_ids):
            raise ValueError("accepted_key_ids must not contain duplicates")
        return cls(
            event_id=f"key-rotation:{uuid.uuid4()}",
            action=action,
            key_id=key_id.strip(),
            actor_id=actor_id.strip(),
            reason=reason.strip(),
            accepted_key_ids=tuple(sorted(accepted_key_ids)),
            previous_active_key_id=previous_active_key_id.strip() if previous_active_key_id else None,
            occurred_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

    def to_dict(self) -> dict:
        result = asdict(self)
        result["accepted_key_ids"] = list(self.accepted_key_ids)
        return result


def _entry_hash(sequence: int, event: dict, previous_hash: str) -> str:
    return hashlib.sha256(_canonical_bytes({
        "sequence": sequence,
        "event": event,
        "previous_hash": previous_hash,
    })).hexdigest()


def _load_verified(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    previous_hash = _GENESIS
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                sequence = item["sequence"]
                event = item["event"]
                linked_previous = item["previous_hash"]
                linked_hash = item["entry_hash"]
                if sequence != len(entries) + 1 or not isinstance(event, dict):
                    raise ValueError("invalid sequence or event")
                event_id = event.get("event_id")
                if not isinstance(event_id, str) or not event_id:
                    raise ValueError("missing event ID")
                if event_id in seen_ids:
                    raise ValueError("duplicate event ID")
                if linked_previous != previous_hash:
                    raise ValueError("broken previous hash")
                calculated = _entry_hash(sequence, event, linked_previous)
                if not isinstance(linked_hash, str) or not hmac.compare_digest(linked_hash, calculated):
                    raise ValueError("entry hash mismatch")
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid or tampered key-rotation audit at line {line_number}") from exc
            entries.append(item)
            seen_ids.add(event_id)
            previous_hash = linked_hash
    return entries


def append_rotation_event(event: KeyRotationEvent, path: str | Path) -> dict:
    """Append an event after verifying the existing chain and fsync the local file."""
    if not isinstance(event, KeyRotationEvent):
        raise TypeError("event must be a KeyRotationEvent")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        entries = _load_verified(destination)
        if any(item["event"]["event_id"] == event.event_id for item in entries):
            raise ValueError(f"duplicate key rotation event ID: {event.event_id}")
        previous_hash = entries[-1]["entry_hash"] if entries else _GENESIS
        sequence = len(entries) + 1
        event_data = event.to_dict()
        entry = {
            "sequence": sequence,
            "event": event_data,
            "previous_hash": previous_hash,
            "entry_hash": _entry_hash(sequence, event_data, previous_hash),
        }
        with destination.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return entry


def verify_rotation_audit(path: str | Path) -> bool:
    """Verify sequence, event IDs, previous hashes, and every entry digest."""
    try:
        _load_verified(Path(path))
    except (OSError, ValueError):
        return False
    return True
