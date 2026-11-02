#!/usr/bin/env python3
"""Validate the KMH Creative Studio design contract with the Python stdlib."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "design-contract.json"
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_COLORS = {
    "canvas", "surface", "surface_muted", "text_primary", "text_secondary",
    "brand_primary", "brand_on_primary", "accent_gold", "success", "danger",
    "border", "focus",
}
REQUIRED_CONTRAST_PAIRS = {
    ("text_primary", "canvas"),
    ("text_secondary", "canvas"),
    ("brand_on_primary", "brand_primary"),
    ("accent_gold", "canvas"),
    ("success", "surface"),
    ("danger", "surface"),
}


class ContractError(ValueError):
    """Raised when a design contract is incomplete or fails a hard gate."""


def _linear_channel(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    if not isinstance(hex_color, str) or not HEX_RE.fullmatch(hex_color):
        raise ContractError(f"Invalid six-digit HEX color: {hex_color!r}")
    rgb = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    r, g, b = (_linear_channel(value) for value in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(first: str, second: str) -> float:
    lum_a, lum_b = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lum_a + 0.05) / (lum_b + 0.05)


def validate_contract(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("contract_version") != "1.0.0":
        errors.append("contract_version must be 1.0.0 for this validator")
    if data.get("project") != "kmh-creative-intelligence-design-studio":
        errors.append("unexpected project identifier")

    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        return errors + ["tokens must be an object"]
    colors = tokens.get("color")
    if not isinstance(colors, dict):
        return errors + ["tokens.color must be an object"]

    missing = sorted(REQUIRED_COLORS - set(colors))
    if missing:
        errors.append("missing color tokens: " + ", ".join(missing))
    for name, value in colors.items():
        if not isinstance(value, str) or not HEX_RE.fullmatch(value):
            errors.append(f"color token {name!r} must be #RRGGBB")

    spacing = tokens.get("spacing_px")
    if not isinstance(spacing, list) or not spacing or any(type(x) is not int or x <= 0 for x in spacing):
        errors.append("spacing_px must be a non-empty list of positive integers")
    elif spacing != sorted(set(spacing)):
        errors.append("spacing_px must be strictly increasing with no duplicates")

    if tokens.get("touch_target_min_px") != 44:
        errors.append("touch_target_min_px must remain at least 44")

    access = data.get("accessibility")
    if not isinstance(access, dict):
        errors.append("accessibility must be an object")
    else:
        if access.get("respect_reduced_motion") is not True:
            errors.append("respect_reduced_motion must be true")
        if access.get("keyboard_accessible") is not True:
            errors.append("keyboard_accessible must be true")
        if access.get("color_not_only_signal") is not True:
            errors.append("color_not_only_signal must be true")

    pairs = data.get("required_contrast_pairs")
    if not isinstance(pairs, list):
        errors.append("required_contrast_pairs must be a list")
        return errors
    found_pairs: set[tuple[str, str]] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            errors.append("each contrast pair must be an object")
            continue
        fg, bg = pair.get("foreground"), pair.get("background")
        if not isinstance(fg, str) or not isinstance(bg, str):
            errors.append("contrast pair foreground/background must be token names")
            continue
        found_pairs.add((fg, bg))
        if fg not in colors or bg not in colors:
            errors.append(f"contrast pair references unknown token: {fg}/{bg}")
            continue
        try:
            measured = contrast_ratio(colors[fg], colors[bg])
        except ContractError as exc:
            errors.append(str(exc))
            continue
        minimum = pair.get("minimum")
        if not isinstance(minimum, (int, float)) or measured + 1e-9 < minimum:
            errors.append(f"contrast {fg}/{bg} is {measured:.2f}:1; minimum {minimum!r}:1")
    missing_pairs = sorted(REQUIRED_CONTRAST_PAIRS - found_pairs)
    if missing_pairs:
        errors.append("missing required contrast pairs: " + ", ".join(f"{a}/{b}" for a, b in missing_pairs))

    component = data.get("component_requirements")
    if not isinstance(component, dict):
        errors.append("component_requirements must be an object")
    else:
        required_states = {"default", "focus", "pressed", "disabled", "loading", "error"}
        states = component.get("button_states")
        if not isinstance(states, list) or not required_states.issubset(set(states)):
            errors.append("button_states must include default/focus/pressed/disabled/loading/error")
        identity = component.get("character_identity_protected_regions")
        if not isinstance(identity, list) or not {"face", "hair", "skin_tone"}.issubset(set(identity)):
            errors.append("character identity protected regions must include face, hair, and skin_tone")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]).resolve() if args else DEFAULT_CONTRACT
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read design contract: {exc}")
        return 2
    errors = validate_contract(data)
    if errors:
        print("FAIL: design contract validation")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {path.name} — required tokens, accessibility flags, component rules, and contrast checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
