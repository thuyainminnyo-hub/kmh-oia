"""Ed25519 trust primitives with explicit key lifecycle controls.

Private keys are supplied by the caller and must be held by a secret manager/HSM.
This module intentionally does not persist private key material.
"""
from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class VerifiedAssertion:
    subject: str
    roles: tuple[str, ...]
    issuer: str
    audience: str
    key_id: str
    issued_at: int
    expires_at: int


class Ed25519TrustAuthority:
    """Signs assertions with one active private key; verifies via a public key ring."""

    def __init__(self, *, issuer: str, audience: str,
                 verification_keys: Mapping[str, bytes],
                 active_key_id: str | None = None,
                 active_private_key: Ed25519PrivateKey | None = None,
                 revoked_key_ids: set[str] | None = None) -> None:
        if not issuer or not audience or not verification_keys:
            raise ValueError("issuer, audience and at least one verification key are required")
        self.issuer, self.audience = issuer, audience
        self._public_keys = {
            key_id: Ed25519PublicKey.from_public_bytes(raw)
            for key_id, raw in verification_keys.items()
        }
        self._revoked = set(revoked_key_ids or ())
        self._active_key_id = active_key_id
        self._private_key = active_private_key
        if (active_key_id is None) != (active_private_key is None):
            raise ValueError("active key ID and private key must be supplied together")
        if active_key_id is not None and active_key_id not in self._public_keys:
            raise ValueError("active key must also exist in the verification key ring")
        if self._revoked.intersection({active_key_id} if active_key_id else set()):
            raise ValueError("a revoked key cannot be active")

    @staticmethod
    def generate_key_pair() -> tuple[Ed25519PrivateKey, bytes]:
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return private, public

    def rotate_signing_key(self, *, key_id: str, private_key: Ed25519PrivateKey,
                           public_key: bytes) -> None:
        if not key_id or key_id in self._revoked:
            raise ValueError("new key ID is empty or revoked")
        derived = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if derived != public_key:
            raise ValueError("private and public key do not match")
        self._public_keys[key_id] = Ed25519PublicKey.from_public_bytes(public_key)
        self._active_key_id, self._private_key = key_id, private_key

    def revoke_key(self, key_id: str) -> None:
        if key_id not in self._public_keys:
            raise ValueError("unknown key ID")
        self._revoked.add(key_id)
        if self._active_key_id == key_id:
            self._active_key_id = None
            self._private_key = None

    def issue(self, *, subject: str, roles: list[str], ttl_seconds: int = 300,
              now: int | None = None) -> str:
        if self._private_key is None or self._active_key_id is None:
            raise RuntimeError("no active signing key")
        if not subject or not roles or any(not isinstance(r, str) or not r for r in roles):
            raise ValueError("subject and non-empty roles are required")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 900:
            raise ValueError("ttl_seconds must be between 1 and 900")
        issued = int(time.time()) if now is None else now
        payload = {"iss": self.issuer, "aud": self.audience, "sub": subject,
                   "roles": sorted(set(roles)), "iat": issued, "exp": issued + ttl_seconds,
                   "kid": self._active_key_id}
        encoded = _canonical(payload)
        return _b64(encoded) + "." + _b64(self._private_key.sign(encoded))

    def verify(self, token: str, *, required_role: str, now: int | None = None) -> VerifiedAssertion:
        try:
            encoded_part, signature_part = token.split(".", 1)
            encoded, signature = _unb64(encoded_part), _unb64(signature_part)
            payload = json.loads(encoded)
            if not isinstance(payload, dict) or _canonical(payload) != encoded:
                raise ValueError("non-canonical assertion")
            key_id = payload["kid"]
            public_key = self._public_keys[key_id]
            if key_id in self._revoked:
                raise ValueError("signing key is revoked")
            public_key.verify(signature, encoded)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, InvalidSignature) as exc:
            raise ValueError("invalid Ed25519 reviewer assertion") from exc
        current = int(time.time()) if now is None else now
        if payload.get("iss") != self.issuer or payload.get("aud") != self.audience:
            raise ValueError("issuer or audience mismatch")
        issued, expires = payload.get("iat"), payload.get("exp")
        if (isinstance(issued, bool) or not isinstance(issued, int)
                or isinstance(expires, bool) or not isinstance(expires, int)
                or issued > current or expires <= current or expires - issued > 900):
            raise ValueError("assertion expired or outside validity window")
        roles, subject = payload.get("roles"), payload.get("sub")
        if not isinstance(roles, list) or required_role not in roles:
            raise ValueError("reviewer lacks required role")
        if not isinstance(subject, str) or not subject:
            raise ValueError("invalid reviewer subject")
        return VerifiedAssertion(subject, tuple(roles), self.issuer, self.audience,
                                 key_id, issued, expires)

    def sign_checkpoint(self, checkpoint: dict) -> tuple[str, str]:
        if self._private_key is None or self._active_key_id is None:
            raise RuntimeError("no active signing key")
        payload = dict(checkpoint, key_id=self._active_key_id)
        return self._active_key_id, _b64(self._private_key.sign(_canonical(payload)))

    def verify_checkpoint(self, checkpoint: dict, *, key_id: str, signature: str) -> bool:
        if key_id in self._revoked or key_id not in self._public_keys:
            return False
        payload = dict(checkpoint, key_id=key_id)
        try:
            self._public_keys[key_id].verify(_unb64(signature), _canonical(payload))
            return True
        except (ValueError, InvalidSignature):
            return False
