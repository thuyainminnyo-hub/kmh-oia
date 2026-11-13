"""Trusted-key-provider boundary for signing and verifying release decisions.

This module defines a minimal interface. The in-memory implementation is for
controlled tests only. Production implementations must retrieve secrets from a
secret manager/KMS, enforce IAM, audit key access, and never log key material.
"""
from dataclasses import dataclass
from typing import Mapping, Protocol, AbstractSet


@dataclass(frozen=True)
class KeyMaterial:
    key_id: str
    secret: bytes
    active_for_signing: bool


class TrustedKeyProvider(Protocol):
    """Minimal interface expected from a trusted secret-manager adapter."""

    def get_signing_key(self) -> KeyMaterial:
        """Return the currently active key material for signing."""
        ...

    def get_verification_key(self, key_id: str) -> bytes | None:
        """Return accepted key material for verification, otherwise None."""
        ...


class KeyProviderUnavailable(RuntimeError):
    """Raised when a key provider cannot supply required trusted key material."""


class InMemoryTrustedKeyProvider:
    """Test-only key provider. Do not use for production secrets."""

    def __init__(
        self,
        keyring: Mapping[str, bytes],
        active_key_id: str,
        accepted_key_ids: AbstractSet[str],
    ) -> None:
        self._keyring = dict(keyring)
        self._active_key_id = active_key_id
        self._accepted_key_ids = set(accepted_key_ids)
        self._validate_policy()

    def _validate_policy(self) -> None:
        if not isinstance(self._active_key_id, str) or not self._active_key_id.strip():
            raise ValueError("active_key_id must be nonblank")
        if self._active_key_id not in self._keyring:
            raise ValueError("active signing key is unavailable")
        if self._active_key_id not in self._accepted_key_ids:
            raise ValueError("active signing key must be accepted for verification")
        for key_id in self._accepted_key_ids:
            secret = self._keyring.get(key_id)
            if not isinstance(key_id, str) or not key_id.strip():
                raise ValueError("accepted key IDs must be nonblank")
            if not isinstance(secret, bytes) or len(secret) < 32:
                raise ValueError(f"accepted key {key_id!r} is unavailable or too short")

    def get_signing_key(self) -> KeyMaterial:
        secret = self._keyring.get(self._active_key_id)
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise KeyProviderUnavailable("active signing key is unavailable")
        return KeyMaterial(
            key_id=self._active_key_id,
            secret=secret,
            active_for_signing=True,
        )

    def get_verification_key(self, key_id: str) -> bytes | None:
        if not isinstance(key_id, str) or key_id not in self._accepted_key_ids:
            return None
        secret = self._keyring.get(key_id)
        if not isinstance(secret, bytes) or len(secret) < 32:
            return None
        return secret

    def rotate(
        self,
        *,
        new_key_id: str,
        new_secret: bytes,
        accepted_key_ids: AbstractSet[str],
    ) -> None:
        """Change active key and accepted verification IDs as one policy update."""
        if not isinstance(new_key_id, str) or not new_key_id.strip():
            raise ValueError("new_key_id must be nonblank")
        if not isinstance(new_secret, bytes) or len(new_secret) < 32:
            raise ValueError("new signing key must be bytes with at least 32 bytes")
        new_keyring = dict(self._keyring)
        new_keyring[new_key_id] = new_secret
        new_accepted = set(accepted_key_ids)
        if new_key_id not in new_accepted:
            raise ValueError("new active key must be included in accepted_key_ids")
        previous_keyring = self._keyring
        previous_active = self._active_key_id
        previous_accepted = self._accepted_key_ids
        self._keyring = new_keyring
        self._active_key_id = new_key_id
        self._accepted_key_ids = new_accepted
        try:
            self._validate_policy()
        except Exception:
            self._keyring = previous_keyring
            self._active_key_id = previous_active
            self._accepted_key_ids = previous_accepted
            raise


def verify_key_provider_configuration(provider: TrustedKeyProvider) -> bool:
    """Check provider contracts and fail closed when active key retrieval fails."""
    try:
        material = provider.get_signing_key()
        if not isinstance(material, KeyMaterial):
            return False
        if not material.active_for_signing or not material.key_id.strip():
            return False
        if not isinstance(material.secret, bytes) or len(material.secret) < 32:
            return False
        return provider.get_verification_key(material.key_id) == material.secret
    except Exception:
        return False
