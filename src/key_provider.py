"""Trusted HMAC key-provider interface and in-memory test implementation.

Production adapters must retrieve keys from an external secret manager/KMS and
expose only explicitly accepted key IDs. Never store production key bytes in
source control, evidence records, or logs.
"""
from dataclasses import dataclass
from typing import Protocol, AbstractSet, Mapping

from src.governance_gate import ReleaseDecision
from src.signed_release_envelope import (
    SignedDecisionEnvelope,
    require_release_allowed_with_keyring,
    sign_decision,
    verify_signed_envelope,
)


class HMACKeyProvider(Protocol):
    """Minimal interface for active signing key and accepted verification keys."""

    def get_key(self, key_id: str) -> bytes | None:
        """Return secret bytes for this key ID, or None if unavailable."""
        ...

    def accepted_key_ids(self) -> AbstractSet[str]:
        """Return key IDs currently accepted for verification."""
        ...

    def active_key_id(self) -> str | None:
        """Return the single key ID currently allowed to sign new decisions."""
        ...


@dataclass(frozen=True)
class InMemoryKeyProvider:
    """Deterministic test provider only; never use for production key material."""

    keys: Mapping[str, bytes]
    accepted_ids: AbstractSet[str]
    active_id: str | None = None

    def get_key(self, key_id: str) -> bytes | None:
        value = self.keys.get(key_id)
        return value if isinstance(value, bytes) else None

    def accepted_key_ids(self) -> AbstractSet[str]:
        return frozenset(self.accepted_ids)

    def active_key_id(self) -> str | None:
        # Backwards-compatible convenience for tests with exactly one accepted key.
        if self.active_id is not None:
            return self.active_id
        if len(self.accepted_ids) == 1:
            return next(iter(self.accepted_ids))
        return None


def _provider_interface_valid(provider: object) -> bool:
    return all(
        callable(getattr(provider, method, None))
        for method in ("get_key", "accepted_key_ids")
    )


def _accepted_keyring(provider: HMACKeyProvider) -> tuple[dict[str, bytes], AbstractSet[str]]:
    accepted = provider.accepted_key_ids()
    if not isinstance(accepted, (set, frozenset)) or any(
        not isinstance(item, str) or not item.strip() for item in accepted
    ):
        raise ValueError("key provider returned invalid accepted key IDs")
    keyring: dict[str, bytes] = {}
    for key_id in accepted:
        key = provider.get_key(key_id)
        if isinstance(key, bytes) and len(key) >= 32:
            keyring[key_id] = key
    return keyring, frozenset(accepted)


def sign_with_provider(
    decision: ReleaseDecision,
    provider: HMACKeyProvider,
) -> SignedDecisionEnvelope:
    """Sign through the provider's active key; refuse an inactive or unavailable key."""
    if not isinstance(decision, ReleaseDecision):
        raise TypeError("decision must be a ReleaseDecision")
    if not _provider_interface_valid(provider) or not callable(
        getattr(provider, "active_key_id", None)
    ):
        raise TypeError("provider does not implement the required HMACKeyProvider interface")
    key_id = provider.active_key_id()
    accepted = provider.accepted_key_ids()
    if not isinstance(key_id, str) or not key_id.strip():
        raise ValueError("key provider has no unambiguous active signing key ID")
    if key_id not in accepted:
        raise ValueError("active signing key ID is not accepted")
    key = provider.get_key(key_id)
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("active signing key is unavailable or invalid")
    return sign_decision(decision, key, key_id=key_id)


def verify_with_provider(signed: object, provider: HMACKeyProvider) -> bool:
    """Verify an envelope only if its key ID is accepted and material is available."""
    if not _provider_interface_valid(provider):
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
    if not isinstance(key, bytes) or len(key) < 32:
        return False
    return verify_signed_envelope(value, key, expected_key_id=key_id)


def require_release_allowed_with_provider(
    signed: object,
    provider: HMACKeyProvider,
) -> ReleaseDecision:
    """Resolve accepted keys from a trusted provider and enforce the signed decision."""
    if not _provider_interface_valid(provider):
        raise TypeError("provider does not implement the required HMACKeyProvider interface")
    keyring, accepted = _accepted_keyring(provider)
    if not keyring:
        raise ValueError("key provider returned no usable accepted keys")
    return require_release_allowed_with_keyring(signed, keyring, accepted)
