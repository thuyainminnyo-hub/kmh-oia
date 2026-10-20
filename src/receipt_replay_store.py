"""Receipt replay/idempotency store contract.

InMemoryReceiptReplayStore is for tests and one-process development only.
Production multi-worker deployments require an atomic durable implementation.
"""
from dataclasses import dataclass
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class ReplayClaim:
    accepted: bool
    key: str
    reason: str


class ReceiptReplayStore(Protocol):
    def claim(self, provider_name: str, source_record_id: str, content_hash: str) -> ReplayClaim: ...


class InMemoryReceiptReplayStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = Lock()

    def claim(self, provider_name: str, source_record_id: str, content_hash: str) -> ReplayClaim:
        parts = (provider_name.strip(), source_record_id.strip(), content_hash.strip())
        if not all(parts):
            return ReplayClaim(False, "", "Replay key fields are required.")
        key = "|".join(parts)
        with self._lock:
            if key in self._seen:
                return ReplayClaim(False, key, "Receipt replay detected.")
            self._seen.add(key)
        return ReplayClaim(True, key, "Receipt replay key claimed.")
