"""Trusted-key-provider adapter for HMAC release signing and enforcement.

The provider decides which key IDs are active/accepted. Production implementations
must retrieve key bytes from a secret manager/KMS and enforce IAM. The bundled
in-memory provider is intended only for controlled tests.
"""
from typing import AbstractSet, Mapping

from src.governance_gate import ReleaseDecision
from src.signed_release_envelope import (
    SignedDecisionEnvelope,
    sign_decision,
    verify_with_keyring,
    require_release_allowed_with_keyring,
)
from src.trusted_key_provider import TrustedKeyProvider, KeyProviderUnavailable


class KeyProviderSigningError(RuntimeError):
    """Raised when a trusted key provider cannot safely perform an operation."""


def sign_decision_with_provider(provider: TrustedKeyProvider, decision: ReleaseDecision) -> SignedDecisionEnvelope:
    """Use the provider's active signing key; fail closed if unavailable."""
    try:
        material = provider.get_signing_key()
    except Exception as exc:
        raise KeyProviderSigningError("trusted signing key is unavailable") from exc
    if not material.active_for_signing:
        raise KeyProviderSigningError("provider key is not active for signing")
    try:
        accepted_secret = provider.get_verification_key(material.key_id)
    except Exception as exc:
        raise KeyProviderSigningError("provider accepted-key policy could not be verified") from exc
    if accepted_secret != material.secret:
        raise KeyProviderSigningError("active signing key is not accepted by verification policy")
    try:
        return sign_decision(decision, material.secret, key_id=material.key_id)
    except Exception as exc:
        raise KeyProviderSigningError("release decision signing failed") from exc


def require_provider_signed_release_allowed(
    provider: TrustedKeyProvider,
    signed: SignedDecisionEnvelope | dict,
) -> ReleaseDecision:
    """Resolve the envelope key through provider policy and enforce its decision."""
    try:
        signed_value = signed.to_dict() if isinstance(signed, SignedDecisionEnvelope) else signed
        if not isinstance(signed_value, dict):
            raise KeyProviderSigningError("signed envelope has invalid type")
        key_id = signed_value.get("key_id")
        if not isinstance(key_id, str) or not key_id.strip():
            raise KeyProviderSigningError("signed envelope has no valid key_id")
        key = provider.get_verification_key(key_id)
    except KeyProviderSigningError:
        raise
    except Exception as exc:
        raise KeyProviderSigningError("trusted verification key lookup failed") from exc
    if key is None:
        raise KeyProviderSigningError("key is retired, unknown, or unavailable")
    try:
        # Provider's single key is used here with an explicit key-ID match.
        # The HMAC signature and inner checksum are verified before enforcement.
        from src.signed_release_envelope import require_signed_release_allowed
        return require_signed_release_allowed(signed, key)
    except Exception as exc:
        raise KeyProviderSigningError("signed release was rejected") from exc
