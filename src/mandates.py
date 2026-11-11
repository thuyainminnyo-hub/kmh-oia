"""Signed task mandate validation at the KMH OIA policy boundary.

Cryptographic primitives are deliberately supplied through a verifier adapter so
production deployments can use an approved Ed25519/JWS or KMS/HSM implementation.
The module does not treat model output as an authority source and ships no
production signing key or insecure default verifier.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TaskMandate:
    mandate_id: str
    issuer: str
    subject_agent_id: str
    actor_workload_id: str
    task_id: str
    audience: str
    scopes: frozenset[str]
    resources: frozenset[str]
    issued_at: int
    not_before: int
    expires_at: int
    nonce: str
    key_id: str
    parent_mandate_id: str | None = None
    delegation_depth: int = 0
    max_delegation_depth: int = 0
    policy_version: str = "1"

    def canonical_payload(self) -> bytes:
        """Return deterministic JSON bytes covered by the detached signature."""
        payload = {
            "mandate_id": self.mandate_id,
            "issuer": self.issuer,
            "subject_agent_id": self.subject_agent_id,
            "actor_workload_id": self.actor_workload_id,
            "task_id": self.task_id,
            "audience": self.audience,
            "scopes": sorted(self.scopes),
            "resources": sorted(self.resources),
            "issued_at": self.issued_at,
            "not_before": self.not_before,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "key_id": self.key_id,
            "parent_mandate_id": self.parent_mandate_id,
            "delegation_depth": self.delegation_depth,
            "max_delegation_depth": self.max_delegation_depth,
            "policy_version": self.policy_version,
        }
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @property
    def payload_digest(self) -> str:
        return hashlib.sha256(self.canonical_payload()).hexdigest()


@dataclass(frozen=True)
class SignedMandate:
    mandate: TaskMandate
    signature: bytes


@dataclass(frozen=True)
class MandateValidation:
    valid: bool
    reason: str


class SignatureVerifier(Protocol):
    """Adapter to a real asymmetric signature verifier and trusted key resolver."""

    def verify(self, *, key_id: str, message: bytes, signature: bytes) -> bool: ...


class NonceStore(Protocol):
    """Atomic one-time nonce claim; implementations must be shared across workers."""

    def claim(self, issuer: str, nonce: str, expires_at: int, now: int) -> bool: ...


class InMemoryNonceStore:
    """Single-process test/local nonce store; not safe as a distributed replay barrier."""

    def __init__(self) -> None:
        self._claimed: set[tuple[str, str]] = set()

    def claim(self, issuer: str, nonce: str, expires_at: int, now: int) -> bool:
        if expires_at <= now:
            return False
        key = (issuer, nonce)
        if key in self._claimed:
            return False
        self._claimed.add(key)
        return True


class MandateValidator:
    def __init__(
        self,
        signature_verifier: SignatureVerifier,
        nonce_store: NonceStore,
        *,
        max_lifetime_seconds: int = 900,
        max_delegation_depth: int = 3,
    ) -> None:
        if max_lifetime_seconds <= 0 or max_delegation_depth < 0:
            raise ValueError("invalid mandate validator limits")
        self.signature_verifier = signature_verifier
        self.nonce_store = nonce_store
        self.max_lifetime_seconds = max_lifetime_seconds
        self.max_delegation_depth = max_delegation_depth

    def validate(
        self,
        signed: SignedMandate,
        *,
        now: int,
        expected_audience: str,
        expected_agent_id: str,
        expected_workload_id: str,
        requested_scope: str,
        requested_resource: str,
        parent: TaskMandate | None = None,
    ) -> MandateValidation:
        mandate = signed.mandate
        required_strings = (
            mandate.mandate_id, mandate.issuer, mandate.subject_agent_id,
            mandate.actor_workload_id, mandate.task_id, mandate.audience,
            mandate.nonce, mandate.key_id, mandate.policy_version,
        )
        if not all(isinstance(value, str) and value.strip() for value in required_strings):
            return MandateValidation(False, "mandate contains empty required fields")
        if not signed.signature:
            return MandateValidation(False, "mandate signature is missing")
        if not self.signature_verifier.verify(
            key_id=mandate.key_id,
            message=mandate.canonical_payload(),
            signature=signed.signature,
        ):
            return MandateValidation(False, "mandate signature verification failed")
        if mandate.audience != expected_audience:
            return MandateValidation(False, "mandate audience mismatch")
        if mandate.subject_agent_id != expected_agent_id:
            return MandateValidation(False, "mandate subject agent mismatch")
        if mandate.actor_workload_id != expected_workload_id:
            return MandateValidation(False, "mandate workload identity mismatch")
        if not (mandate.issued_at <= now and mandate.not_before <= now < mandate.expires_at):
            return MandateValidation(False, "mandate is not currently valid")
        if mandate.expires_at <= mandate.issued_at:
            return MandateValidation(False, "mandate expiry must follow issue time")
        if mandate.expires_at - mandate.issued_at > self.max_lifetime_seconds:
            return MandateValidation(False, "mandate lifetime exceeds configured maximum")
        if not mandate.scopes or not mandate.resources:
            return MandateValidation(False, "mandate must constrain scopes and resources")
        if requested_scope not in mandate.scopes:
            return MandateValidation(False, "requested scope is outside mandate")
        if requested_resource not in mandate.resources:
            return MandateValidation(False, "requested resource is outside mandate")
        if mandate.delegation_depth < 0 or mandate.max_delegation_depth < 0:
            return MandateValidation(False, "delegation depth cannot be negative")
        if mandate.max_delegation_depth > self.max_delegation_depth:
            return MandateValidation(False, "mandate delegation limit exceeds policy")
        if mandate.delegation_depth > mandate.max_delegation_depth:
            return MandateValidation(False, "mandate delegation depth exceeded")
        if parent is None:
            if mandate.parent_mandate_id is not None or mandate.delegation_depth != 0:
                return MandateValidation(False, "root mandate cannot claim a parent")
        else:
            if mandate.parent_mandate_id != parent.mandate_id:
                return MandateValidation(False, "parent mandate link mismatch")
            if mandate.issuer != parent.subject_agent_id:
                return MandateValidation(False, "delegation issuer is not parent subject")
            if mandate.delegation_depth != parent.delegation_depth + 1:
                return MandateValidation(False, "delegation depth is not contiguous")
            if not mandate.scopes.issubset(parent.scopes):
                return MandateValidation(False, "delegated scopes exceed parent authority")
            if not mandate.resources.issubset(parent.resources):
                return MandateValidation(False, "delegated resources exceed parent authority")
            if mandate.expires_at > parent.expires_at:
                return MandateValidation(False, "child mandate outlives parent mandate")
            if mandate.max_delegation_depth > parent.max_delegation_depth:
                return MandateValidation(False, "child delegation limit exceeds parent")
        if not self.nonce_store.claim(mandate.issuer, mandate.nonce, mandate.expires_at, now):
            return MandateValidation(False, "mandate nonce replay or expiry detected")
        return MandateValidation(True, "mandate signature and constraints verified")
