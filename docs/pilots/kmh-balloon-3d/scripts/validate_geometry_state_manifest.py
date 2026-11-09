#!/usr/bin/env python3
"""Validate the KMH balloon two-state visual scene manifest.

This validates metadata integrity only. It does not calculate or simulate physics.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_STATES = {"BASE-UNLOADED", "DISPLAYED-ATTACHED"}
FORBIDDEN_KEYS = {
    "ignition_sequence", "burn_rate", "heat_output", "fuel_quantity",
    "firing_timing", "launch_optimization", "operational_load_calculation"
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def walk_keys(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, f"{path}.{k}"
            yield from walk_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--project-root", type=Path, default=None,
                    help="Root containing geometry/ assets. Defaults to manifest parent.")
    args = ap.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read manifest: {exc}")
        return 2

    errors = []
    state_ids = {s.get("state_id") for s in data.get("states", [])}
    if state_ids != REQUIRED_STATES:
        errors.append(f"Expected state IDs {sorted(REQUIRED_STATES)}, got {sorted(state_ids)}")

    shared = data.get("shared_assets", {})
    envelope = shared.get("envelope_master", {})
    attachment = shared.get("yan_khwe_attachment", {})
    if not envelope.get("file"):
        errors.append("Missing envelope master file.")
    if attachment.get("mesh_status") != "NOT_MODELED":
        errors.append("Yan-Khwe attachment must remain reference-only and NOT_MODELED.")
    if attachment.get("geometry_inference") != "PROHIBITED":
        errors.append("Attachment geometry inference must be explicitly prohibited.")

    base = next((s for s in data.get("states", []) if s.get("state_id") == "BASE-UNLOADED"), {})
    displayed = next((s for s in data.get("states", []) if s.get("state_id") == "DISPLAYED-ATTACHED"), {})
    if base.get("envelope_asset") != displayed.get("envelope_asset"):
        errors.append("Both states must reuse the same preserved envelope master until evidence supports overrides.")
    if displayed.get("attachment_asset") != attachment.get("asset_id"):
        errors.append("Displayed state must reference the separate attachment asset.")
    if displayed.get("envelope_profile_override") is not None:
        errors.append("State-specific profile override must remain null until measured evidence exists.")

    for key, where in walk_keys(data):
        if key in FORBIDDEN_KEYS:
            errors.append(f"Forbidden operational field '{key}' at {where}.")

    if args.project_root is not None:
        mesh_file = args.project_root / envelope["file"]
        if not mesh_file.exists():
            errors.append(f"Envelope mesh not found at {mesh_file}.")
        else:
            observed_sha = sha256(mesh_file)
            if observed_sha != envelope.get("sha256"):
                errors.append("Envelope mesh SHA-256 does not match manifest.")
    else:
        print("WARN: asset file hash not checked; pass --project-root to verify the local GLB.")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    print("PASS: state manifest structure and asset invariants are valid.")
    print("PASS: base and displayed states reuse the same preserved envelope mesh.")
    print("PASS: Yan-Khwe remains a separate reference-only, non-modeled asset.")
    print("PASS: no forbidden operational fields were found.")
    print("NOTE: this is metadata validation only; it does not validate physical geometry.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
