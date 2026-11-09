#!/usr/bin/env python3
"""Audit UV readiness of the preserved KMH Geometry v1 GLBs.

Checks file readability, topology and UV/material presence. It does not modify
source assets or create UV coordinates.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import trimesh

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    targets = {
        "body": "geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb",
        "lower_skirt": "geometry/KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb"
    }
    result = {
        "status": "UV_NOT_STARTED",
        "decision": "NOT_READY_FOR_FINAL_UV_MAPPING",
        "assets": {},
        "errors": []
    }
    for label, relative_path in targets.items():
        path = args.project_root / relative_path
        if not path.exists():
            result["errors"].append(f"Missing asset: {path}")
            continue
        mesh = trimesh.load(path, force="mesh")
        uv = getattr(mesh.visual, "uv", None)
        material = getattr(mesh.visual, "material", None)
        result["assets"][label] = {
            "file": relative_path,
            "sha256": sha256(path),
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent),
            "uv_present": uv is not None,
            "material_present": material is not None
        }
        if not mesh.is_watertight or not mesh.is_winding_consistent:
            result["errors"].append(f"{label}: topology baseline failed.")
        if uv is not None or material is not None:
            result["errors"].append(f"{label}: preserved Geometry v1 unexpectedly has UV/material data.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["errors"]:
        print("FAIL:", result["errors"])
        return 1
    print("PASS: both Geometry v1 GLBs are readable; topology checks pass.")
    print("PASS: neither GLB has UV coordinates or a material assignment.")
    print("DECISION: UV NOT READY; source assets were not modified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
