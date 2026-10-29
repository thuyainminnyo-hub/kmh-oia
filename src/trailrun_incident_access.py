"""Explicit role/action policy for the TGiTrailRun pilot.

This module is a policy helper, not authentication. Callers must establish
identity from a trusted authentication layer and enforce resource/runner scope
before using these decisions. Unknown roles and actions are denied by default.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason_code: str


# Deliberately narrow pilot permissions. No role can autonomously perform rescue.
_ROLE_ACTIONS = {
    "checkpoint_volunteer": frozenset({"incident:create", "incident:read"}),
    "race_control": frozenset({
        "incident:create", "incident:read", "audit:read",
        "incident:transition:ACKNOWLEDGED",
        "incident:transition:DISPATCHED",
        "incident:transition:CLOSED",
    }),
    "medical_lead": frozenset({
        "incident:read", "audit:read",
        "incident:transition:ACKNOWLEDGED",
        "incident:transition:RESOLVED",
    }),
}


def authorize(role: str, action: str) -> AccessDecision:
    """Return allow/deny for a known role and action; default deny."""
    if not isinstance(role, str) or not isinstance(action, str):
        return AccessDecision(False, "INVALID_PRINCIPAL_OR_ACTION")
    if role not in _ROLE_ACTIONS:
        return AccessDecision(False, "UNKNOWN_ROLE")
    if action not in _ROLE_ACTIONS[role]:
        return AccessDecision(False, "ACTION_NOT_PERMITTED")
    return AccessDecision(True, "ACTION_PERMITTED")


def authorize_transition(role: str, requested_status: str) -> AccessDecision:
    """Authorize a transition target; state-machine validity is checked separately."""
    if not isinstance(requested_status, str):
        return AccessDecision(False, "INVALID_PRINCIPAL_OR_ACTION")
    return authorize(role, f"incident:transition:{requested_status}")
