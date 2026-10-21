"""Trusted HMAC key-provider interface and in-memory test implementation.

Production implementations should retrieve key bytes from an external secret
manager/KMS and expose only explicitly accepted key IDs. This module deliberately
does not read secrets from source files or define any production credentials.
"""
from dataclasses import dataclass
from typing import Protocol, AbstractSet, Mapping


class HMACKeyProvider(Protocol):
    """Minimal interface for key IDs, accepted IDs, and key retrieval."""

    def get_key(self, key_id: str) -> bytes | None:
        """Return secret bytes for the requested key ID, or None if unavailable."""
        ...

    def accepted_key_ids(self) -> AbstractSet[str]:
        """Return key IDs currently accepted for verification."""
        ...


@dataclass(frozen=True)
class InMemoryKeyProvider:
    """Deterministic provider for unit tests only; never use for production keys."""

    keys: Mapping[str, bytes]
    accepted_ids: AbstractSet[str]

    def get_key(self, key_id: str) -> bytes | None:
        value = self.keys.get(key_id)
        return value if isinstance(value, bytes) else None

    def accepted_key_ids(self) -> AbstractSet[str]:
        return frozenset(self.accepted_ids)


def verify_with_provider(signed: object, provider: HMACKeyProvider) -> bool:
    """Resolve the envelope's key via the provider, enforcing provider allowlist."""
    from src.signed_release_envelope import verify_signed_envelope

    if not isinstance(provider, HMACKeyProvider):
        # Runtime-checkable is intentionally not required: support duck-typed
        # provider adapters while validating both required methods explicitly.
        if not callable(getattr(provider, "get_key", None)) or not callable(
            getattr(provider, "accepted_key_ids", None)
        ):
            return False
    if hasattr(signed, "to_dict"):
        value = signed.to_dict()
    elif isinstance(signed, dict):
        value = signed
    else:
        return False
    key_id = value.get("key_id")
    if not isinstance(key_id, str) or key_id not in provider.accepted_key_ids():
        return False
    key = provider.get_key(key_id)
    if not isinstance(key, bytes):
        return False
    return verify_signed_envelope(value, key, expected_key_id=key_id)
