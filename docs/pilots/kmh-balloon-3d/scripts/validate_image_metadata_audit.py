#!/usr/bin/env python3
"""Verify preserved image copies against the KMH metadata audit registry."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_image_metadata_audit.py <registry.json> <package-root>")
        return 2
    registry_path = Path(sys.argv[1])
    package_root = Path(sys.argv[2])
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read registry: {exc}")
        return 2

    errors = []
    records = data.get("records", [])
    for record in records:
        filename = record.get("filename")
        if not filename:
            errors.append("Record missing filename.")
            continue
        source = package_root / "references" / filename
        if not source.is_file():
            errors.append(f"Missing source copy: {filename}")
        elif digest(source) != record.get("sha256"):
            errors.append(f"SHA-256 mismatch: {filename}")

    summary = data.get("summary", {})
    if len(records) != 16:
        errors.append(f"Expected 16 source records, found {len(records)}.")
    if summary.get("exif_present") != 0:
        errors.append("Registry summary no longer matches EXIF audit result.")
    if summary.get("camera_model_available") != 0:
        errors.append("Registry summary no longer matches camera-model audit result.")
    if summary.get("datetime_original_available") != 0:
        errors.append("Registry summary no longer matches timestamp audit result.")
    if summary.get("near_duplicate_screen", {}).get("status") != "WITHDRAWN_NOT_RELIABLE":
        errors.append("Exploratory near-duplicate screen must remain withdrawn.")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: all 16 image copies match their registered SHA-256 hashes.")
    print("PASS: metadata summary is internally consistent (EXIF/camera/time absent).")
    print("PASS: unreliable near-duplicate heuristic remains withdrawn.")
    print("NOTE: file-integrity validation does not establish calibration or photogrammetry readiness.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
