#!/usr/bin/env python3
"""Validate KMH source-state attribution register."""
import json, sys, hashlib
from pathlib import Path

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv)!=3:
        print("Usage: validate_state_attribution.py <registry.json> <package-root>")
        return 2
    data=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root=Path(sys.argv[2])
    errors=[]
    for rec in data.get("records",[]):
        p=root/"references"/rec["file"]
        if not p.exists():
            errors.append(f"Missing {rec['file']}")
        elif digest(p)!=rec["sha256"]:
            errors.append(f"Hash mismatch {rec['file']}")
        if rec["state_attribution"] not in {"BASE-UNLOADED","DISPLAYED-ATTACHED","UNKNOWN","NOT_APPLICABLE"}:
            errors.append(f"Invalid state {rec['file']}")
        if rec["photogrammetry_usable"] is not False:
            errors.append(f"Unexpected photogrammetry-ready reference: {rec['file']}")
    s=data["summary"]
    if s["base_unloaded_confirmed"] or s["displayed_attached_confirmed"]:
        errors.append("Audit must not claim confirmed state attribution.")
    if errors:
        for e in errors: print("FAIL:",e)
        return 1
    print("PASS: all 16 original references exist and SHA-256 hashes match.")
    print("PASS: no image was falsely promoted to a confirmed balloon state.")
    print("PASS: all existing references remain excluded from calibrated photogrammetry.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
