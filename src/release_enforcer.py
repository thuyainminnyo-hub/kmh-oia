"""Integration adapter that turns a trusted release decision into an enforceable gate.

This helper intentionally fails closed. It does not deploy anything; the caller
must invoke it immediately before the protected action and abort if it raises.
"""
from dataclasses import dataclass

from src.governance_gate import ReleaseDecision


@dataclass(frozen=True)
class ReleaseBlocked(RuntimeError):
    decision_id: str
    reason: str

    def __str__(self) -> str:
        return f"release blocked ({self.decision_id}): {self.reason}"


def require_release_allowed(decision: ReleaseDecision) -> None:
    """Raise unless a valid ALLOW decision is supplied.

    The caller must load the decision from trusted storage and ensure it has not
    been tampered with. A locally constructed ALLOW object is not proof of
    approval; the production adapter must authenticate its provenance.
    """
    if not isinstance(decision, ReleaseDecision):
        raise TypeError("decision must be a ReleaseDecision")
    if decision.status != "ALLOW":
        raise ReleaseBlocked(decision.decision_id, decision.reason)
    if not decision.checks or not all(
        isinstance(check, dict) and check.get("passed") is True
        for check in decision.checks
    ):
        raise ReleaseBlocked(decision.decision_id, "decision checks are missing or not all passing")
