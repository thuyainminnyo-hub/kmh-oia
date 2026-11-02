"""Synthetic fixture used only to test Graphify source traceability."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignToken:
    token_name: str
    approved: bool


def is_approved_token(token: DesignToken) -> bool:
    """Return true only for a named token explicitly approved by review."""
    return bool(token.token_name.strip()) and token.approved


def protects_character_identity(region_names: tuple[str, ...]) -> bool:
    """Check that the synthetic protected-region set is complete."""
    required = {"face", "hair", "skin_tone"}
    return required.issubset(set(region_names))
