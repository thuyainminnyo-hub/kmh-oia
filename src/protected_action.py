"""Protected-action executor that does not run unless signed release passes.

This is a controlled prototype of the final call boundary. The actual action
callback is invoked only after the trusted key provider has verified signature,
accepted key policy, and an ALLOW decision. Production still needs to load key
material from KMS/secret manager and run this guard in the real deployment job.
"""
from typing import Callable, TypeVar

from src.governance_gate import ReleaseDecision
from src.key_provider_signing import require_provider_signed_release_allowed
from src.signed_release_envelope import SignedDecisionEnvelope
from src.trusted_key_provider import TrustedKeyProvider

T = TypeVar("T")


class ProtectedActionBlocked(RuntimeError):
    """Raised when a protected action is blocked before the action callback."""


def execute_protected_action(
    provider: TrustedKeyProvider,
    signed_decision: SignedDecisionEnvelope | dict,
    action: Callable[[], T],
) -> tuple[ReleaseDecision, T]:
    """Verify signed release first; invoke action only when decision is ALLOW."""
    if not callable(action):
        raise TypeError("action must be callable")
    try:
        decision = require_provider_signed_release_allowed(provider, signed_decision)
    except Exception as exc:
        raise ProtectedActionBlocked("release verification failed; protected action not executed") from exc
    # All decision checks are enforced by the signed-release path before this line.
    result = action()
    return decision, result
