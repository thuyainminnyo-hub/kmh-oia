#!/usr/bin/env python3
"""Validate the schema-level integrity of a KMH capture-set manifest."""
from __future__ import annotations
import json, sys
from pathlib import Path

ALLOWED_STATES = {"BASE-UNLOADED", "DISPLAYED-ATTACHED", "UNKNOWN"}

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_capture_set_manifest.py <manifest.json>")
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("FAIL:", exc)
        return 2
    errors = []
    state = data.get("visual_state", {}).get("state_id")
    if state not in ALLOWED_STATES:
        errors.append(f"Invalid visual_state.state_id: {state}")
    images = data.get("images", [])
    if not images:
        errors.append("At least one image record is required.")
    for idx, item in enumerate(images):
        if item.get("state_id", "UNKNOWN") not in ALLOWED_STATES:
            errors.append(f"images[{idx}] has an invalid state_id.")
        if not item.get("filename"):
            errors.append(f"images[{idx}] is missing filename.")
        if item.get("physical_orientation_confirmed") is not True and item.get("view_group") in {"LEFT_OBLIQUE", "RIGHT_OBLIQUE"}:
            errors.append(f"images[{idx}] labels physical left/right without orientation confirmation.")
    auth = data.get("reconstruction_authorization", {})
    if auth.get("colmap") != "NOT_AUTHORIZED_UNTIL_CAPTURE_QA_PASS":
        errors.append("COLMAP must remain blocked until capture QA passes.")
    if auth.get("tripo_paid_generation") != "REQUIRES_SEPARATE_EXPLICIT_APPROVAL":
        errors.append("Tripo paid generation must require separate explicit approval.")
    if auth.get("geometry_v2") != "HOLD":
        errors.append("Geometry v2 must remain HOLD.")
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print("PASS: state labels and image records are structurally valid.")
    print("PASS: left/right orientation guard is present.")
    print("PASS: COLMAP, paid Tripo, and Geometry v2 gates remain enforced.")
    print("NOTE: template validation does not certify capture quality or physical measurements.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
