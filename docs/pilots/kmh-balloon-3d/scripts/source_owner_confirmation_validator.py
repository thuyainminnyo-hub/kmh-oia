#!/usr/bin/env python3
"""Reject unsupported BASE/DISPLAYED state promotion in the source register."""
from __future__ import annotations
import csv,sys
from pathlib import Path

ALLOWED={"BASE-UNLOADED","DISPLAYED-ATTACHED","UNKNOWN","NOT_APPLICABLE"}
ACCEPTABLE={"DIRECT_WITNESS","ORIGINAL_CREATOR","TEAM_RECORD","DOCUMENTED_SOURCE"}
REQUIRED=("confirmed_by","relationship_to_source","confirmation_basis","evidence_reference","confirmation_date")

def main():
    if len(sys.argv)!=2:
        print("Usage: source_owner_confirmation_validator.py <register.csv>"); return 2
    try:
        with Path(sys.argv[1]).open(newline="",encoding="utf-8-sig") as f:
            rows=list(csv.DictReader(f))
    except OSError as e:
        print("FAIL:",e); return 2
    errors=[]
    for line,row in enumerate(rows,start=2):
        old=(row.get("current_state") or "").strip()
        new=(row.get("confirmed_state") or "").strip()
        if old not in ALLOWED: errors.append(f"Row {line}: invalid current_state.")
        if new not in ALLOWED: errors.append(f"Row {line}: invalid confirmed_state.")
        if new in {"BASE-UNLOADED","DISPLAYED-ATTACHED"} and old != new:
            if (row.get("confirmation_basis") or "").strip() not in ACCEPTABLE:
                errors.append(f"Row {line}: direct/documented basis required.")
            for key in REQUIRED:
                if not (row.get(key) or "").strip():
                    errors.append(f"Row {line}: promotion missing {key}.")
        if (row.get("confirmation_basis") or "").strip()=="VISUAL_INFERENCE_ONLY" and new!="UNKNOWN":
            errors.append(f"Row {line}: visual inference cannot confirm state.")
    if not rows: errors.append("No image rows.")
    if errors:
        for e in errors: print("FAIL:",e)
        return 1
    print(f"PASS: {len(rows)} source rows have valid state labels.")
    print("PASS: no unsupported state promotion was accepted.")
    print("NOTE: template validation is not source confirmation.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
