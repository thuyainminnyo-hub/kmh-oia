"""Deterministic helpers for the KMH OIA Karmic Tail case-study pilot.

This module supports symbolic self-reflection only. It does not infer a user's
personality, diagnose a condition, or predict relationship outcomes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "karmic_tail_true_partner_registry.json"
)
EXPECTED_CARD_IDS = set(range(1, 23))
REQUIRED_CARD_FIELDS = {
    "id",
    "name",
    "pattern_key",
    "interpretation",
    "reflection_question",
    "suggested_action",
    "evidence_status",
    "qa_rules",
}


class RegistryValidationError(ValueError):
    """Raised when the canonical registry is incomplete or inconsistent."""


def load_registry(path: str | Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load and validate the canonical registry JSON."""
    with Path(path).open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    validate_registry(registry)
    return registry


def validate_registry(registry: dict[str, Any]) -> None:
    """Validate required metadata, unique IDs, and all 22 card records."""
    if not isinstance(registry, dict):
        raise RegistryValidationError("Registry root must be a JSON object.")

    for key in ("case_id", "schema_version", "registry_version", "archetypes", "output_policy"):
        if key not in registry:
            raise RegistryValidationError(f"Missing registry field: {key}")

    cards = registry["archetypes"]
    if not isinstance(cards, list):
        raise RegistryValidationError("'archetypes' must be a list.")

    ids: list[int] = []
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise RegistryValidationError(f"Card at index {index} must be an object.")
        missing = REQUIRED_CARD_FIELDS - set(card)
        if missing:
            raise RegistryValidationError(
                f"Card at index {index} is missing fields: {', '.join(sorted(missing))}"
            )
        card_id = card["id"]
        if isinstance(card_id, bool) or not isinstance(card_id, int):
            raise RegistryValidationError(f"Card ID must be an integer: {card_id!r}")
        ids.append(card_id)
        for field in ("name", "pattern_key", "interpretation", "reflection_question", "suggested_action"):
            if not isinstance(card[field], str) or not card[field].strip():
                raise RegistryValidationError(
                    f"Card {card_id} has an empty or invalid '{field}' field."
                )
        if not isinstance(card["qa_rules"], list) or not card["qa_rules"]:
            raise RegistryValidationError(f"Card {card_id} must have at least one QA rule.")

    if len(ids) != len(set(ids)):
        raise RegistryValidationError("Duplicate card IDs detected.")
    if set(ids) != EXPECTED_CARD_IDS:
        missing = sorted(EXPECTED_CARD_IDS - set(ids))
        unexpected = sorted(set(ids) - EXPECTED_CARD_IDS)
        raise RegistryValidationError(
            f"Card IDs must be exactly 1–22; missing={missing}, unexpected={unexpected}."
        )

    policy = registry["output_policy"]
    required_policy = {
        "require_uncertainty_language",
        "require_actionable_reflection",
        "prohibit_guaranteed_predictions",
        "require_user_confirmation_for_personal_patterns",
        "prohibit_unsupported_diagnosis",
    }
    if not isinstance(policy, dict) or not required_policy.issubset(policy):
        raise RegistryValidationError("Output policy is missing required safeguards.")
    if not all(policy[key] is True for key in required_policy):
        raise RegistryValidationError("All required output safeguards must be enabled.")


def evaluate_pattern(card: dict[str, Any], user_confirmation: str) -> dict[str, str]:
    """Return a conservative status based on explicit user confirmation.

    Accepted confirmation values: 'confirmed', 'not_applicable', 'unsure'.
    A card alone never verifies a personal pattern.
    """
    if not isinstance(card, dict) or not REQUIRED_CARD_FIELDS.issubset(card):
        return {"status": "REJECTED", "reason": "Invalid or incomplete pattern definition."}

    if user_confirmation == "not_applicable":
        return {
            "status": "NOT_CONFIRMED",
            "reason": "The user does not identify with this pattern.",
            "next_action": "Respect the response and explore another pattern only if useful.",
        }
    if user_confirmation == "confirmed":
        return {
            "status": "USER_CONFIRMED",
            "reason": "The user recognizes the described pattern in their own experience.",
            "next_action": "Offer the optional practical action without treating the card as proof.",
        }
    if user_confirmation == "unsure":
        return {
            "status": "HYPOTHESIS",
            "reason": "The personal pattern remains uncertain.",
            "next_action": "Ask a neutral reflection question; do not assert the pattern as fact.",
        }
    return {
        "status": "REJECTED",
        "reason": "Unsupported confirmation value.",
    }


def get_card(card_id: int, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a card by canonical ID or raise KeyError for an unknown ID."""
    current = registry if registry is not None else load_registry()
    validate_registry(current)
    for card in current["archetypes"]:
        if card["id"] == card_id:
            return card
    raise KeyError(f"Unknown Karmic Tail card ID: {card_id}")
