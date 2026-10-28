"""Deterministic, side-effect-free state transition policy for the TGiTrailRun pilot.

This module validates proposed transitions only. It does not persist incidents,
authorize actors, send notifications, dispatch responders, or make medical decisions.
Those controls must be enforced by the service boundary before live use.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

IncidentStatus = Literal[
    "REPORTED", "ACKNOWLEDGED", "DISPATCHED", "RESOLVED", "CLOSED"
]

ALLOWED_TRANSITIONS: Final[frozenset[tuple[str, str]]] = frozenset({
    ("REPORTED", "ACKNOWLEDGED"),
    ("ACKNOWLEDGED", "DISPATCHED"),
    ("DISPATCHED", "RESOLVED"),
    ("RESOLVED", "CLOSED"),
})


@dataclass(frozen=True)
class TransitionDecision:
    allowed: bool
    current_status: str
    requested_status: str
    reason_code: str


def validate_transition(current_status: str, requested_status: str) -> TransitionDecision:
    """Return a deterministic decision; never mutates state or performs side effects."""
    known_statuses = {
        "REPORTED", "ACKNOWLEDGED", "DISPATCHED", "RESOLVED", "CLOSED"
    }
    if current_status not in known_statuses or requested_status not in known_statuses:
        return TransitionDecision(
            False, current_status, requested_status, "UNKNOWN_STATUS"
        )
    if current_status == requested_status:
        return TransitionDecision(
            False, current_status, requested_status, "NO_OP_NOT_ALLOWED"
        )
    if (current_status, requested_status) not in ALLOWED_TRANSITIONS:
        return TransitionDecision(
            False, current_status, requested_status, "INVALID_TRANSITION"
        )
    return TransitionDecision(
        True, current_status, requested_status, "TRANSITION_ALLOWED"
    )
