#!/usr/bin/env python3
"""Validate a KMH state-separated capture manifest; never processes images."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ALLOWED_STATES = {"BASE-UNLOADED", "DISPLAYED-ATTACHED", "UNKNOWN"}
ALLOWED_COVERAGE = {"CAPTURED", "NOT_CAPTURED", "NOT_SAFE/NOT_PERMITTED", "NOT_REVIEWED"}

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--originals-dir",type=Path,default=None)
    ap.add_argument("--require-images",action="store_true")
    args=ap.parse_args()
    try:
        data=json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:
        print("FAIL: cannot load manifest:",e); return 2
    errors=[]
    state=data.get("visual_state",{}).get("state_id")
    if state not in ALLOWED_STATES:
        errors.append(f"Invalid set state: {state}")
    images=data.get("images",[])
    if args.require_images and not images:
        errors.append("No image records supplied.")
    if images and state=="UNKNOWN":
        errors.append("UNKNOWN-state set cannot be authorized for state-specific reconstruction.")
    seen=set()
    for i,img in enumerate(images):
        fn=img.get("filename")
        if not fn:
            errors.append(f"images[{i}] missing filename."); continue
        if fn in seen:
            errors.append(f"Duplicate filename: {fn}")
        seen.add(fn)
        if img.get("state_id",state)!=state:
            errors.append(f"{fn}: image state differs from capture-set state.")
        if img.get("sha256") is None:
            errors.append(f"{fn}: SHA-256 missing.")
        if args.originals_dir is not None:
            p=args.originals_dir/fn
            if not p.exists():
                errors.append(f"{fn}: original file missing.")
            elif sha256(p)!=img.get("sha256"):
                errors.append(f"{fn}: SHA-256 mismatch.")
    for k,v in data.get("coverage",{}).items():
        if v not in ALLOWED_COVERAGE:
            errors.append(f"Coverage {k} has invalid value {v}.")
    auth=data.get("authorization",{})
    if auth.get("colmap")!="BLOCKED":
        if state=="UNKNOWN" or not images:
            errors.append("COLMAP cannot be authorized for UNKNOWN or empty capture sets.")
    if auth.get("tripo_paid_generation")!="REQUIRES_SEPARATE_EXPLICIT_APPROVAL":
        errors.append("Tripo paid generation must require separate explicit approval.")
    if auth.get("geometry_v2")!="HOLD":
        errors.append("Geometry v2 must remain HOLD in the intake manifest.")
    if errors:
        for e in errors: print("FAIL:",e)
        return 1
    print("PASS: manifest structure and single-state consistency checks passed.")
    if args.originals_dir is not None:
        print("PASS: original image hash verification completed.")
    elif images:
        print("WARN: hashes recorded but source files were not checked; provide --originals-dir.")
    else:
        print("NOTE: empty template validation only; no capture is claimed.")
    print("PASS: COLMAP/Geometry v2/Tripo approval gates remain enforced.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
