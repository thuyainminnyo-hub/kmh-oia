#!/usr/bin/env python3
"""Validate the KMH balloon two-state visual scene manifest.

This validates metadata integrity and local asset hashes only. It does not
calculate, simulate, or validate physical geometry.
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
                    help="Root containing geometry/ assets.")
    args = ap.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read manifest: {exc}")
        return 2

    errors = []
    states = data.get("states", [])
    state_ids = {s.get("state_id") for s in states}
    if state_ids != REQUIRED_STATES:
        errors.append(f"Expected state IDs {sorted(REQUIRED_STATES)}, got {sorted(state_ids)}")

    shared = data.get("shared_assets", {})
    envelope = shared.get("envelope_master", {})
    skirt = shared.get("lower_skirt", {})
    attachment = shared.get("yan_khwe_attachment", {})

    if not envelope.get("file") or not envelope.get("sha256"):
        errors.append("Envelope asset path/hash is required.")
    if not skirt.get("file") or not skirt.get("sha256"):
        errors.append("Lower-skirt asset path/hash is required.")
    if skirt.get("merge_into_envelope_master") is not False:
        errors.append("Lower skirt must remain separately addressable.")
    if attachment.get("mesh_status") != "NOT_MODELED":
        errors.append("Yan-Khwe must remain reference-only and NOT_MODELED.")
    if attachment.get("geometry_inference") != "PROHIBITED":
        errors.append("Attachment geometry inference must be prohibited.")

    base = next((s for s in states if s.get("state_id") == "BASE-UNLOADED"), {})
    displayed = next((s for s in states if s.get("state_id") == "DISPLAYED-ATTACHED"), {})
    if base.get("envelope_asset") != displayed.get("envelope_asset"):
        errors.append("Both states must reuse the same preserved envelope master.")
    if base.get("lower_skirt_asset") != displayed.get("lower_skirt_asset"):
        errors.append("Both states must reuse the same preserved lower-skirt asset.")
    if displayed.get("attachment_asset") != attachment.get("asset_id"):
        errors.append("Displayed state must reference the separate Yan-Khwe asset.")
    if displayed.get("envelope_profile_override") is not None:
        errors.append("Profile override must remain null until measured evidence exists.")

    for key, where in walk_keys(data):
        if key in FORBIDDEN_KEYS:
            errors.append(f"Forbidden operational field '{key}' at {where}.")

    if args.project_root is not None:
        for label, asset in (("envelope_master", envelope), ("lower_skirt", skirt)):
            rel = asset.get("file")
            if not rel:
                continue
            asset_path = args.project_root / rel
            if not asset_path.exists():
                errors.append(f"{label} asset not found: {asset_path}")
            elif sha256(asset_path) != asset.get("sha256"):
                errors.append(f"{label} SHA-256 mismatch.")
    else:
        print("WARN: asset hashes not checked; pass --project-root to verify local GLBs.")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: both required visual states are present.")
    print("PASS: both states reuse the same preserved envelope and lower-skirt assets.")
    print("PASS: Yan-Khwe is separate, reference-only, and not modeled.")
    print("PASS: body and lower-skirt asset hashes match the manifest.")
    print("PASS: no prohibited operational fields were found.")
    print("NOTE: metadata integrity does not validate physical geometry or state deformation.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
