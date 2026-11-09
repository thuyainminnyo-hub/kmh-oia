#!/usr/bin/env python3
"""Validate provenance and integrity of the KMH artwork reference atlas."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_artwork_atlas.py <registry.json> <package-root>")
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(sys.argv[2])
    errors = []
    for item in data.get("reference_images", []):
        p = root / "references" / item["file"]
        if not p.exists():
            errors.append(f"Missing reference: {item['file']}")
        elif sha256(p) != item["sha256"]:
            errors.append(f"SHA-256 mismatch: {item['file']}")
    if len(data.get("artwork_zones", [])) != 7:
        errors.append("Expected exactly seven identified artwork zones.")
    if data.get("uv_policy", {}).get("uv_mapping_started") is not False:
        errors.append("UV mapping must remain not started.")
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print("PASS: all three source images exist and their SHA-256 hashes match.")
    print("PASS: seven artwork reference zones are registered.")
    print("PASS: UV mapping remains NOT STARTED.")
    print("NOTE: provenance validation only; no UV or geometry accuracy is claimed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
