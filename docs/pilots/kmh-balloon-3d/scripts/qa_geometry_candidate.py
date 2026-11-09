#!/usr/bin/env python3
"""Non-operational structural QA for KMH visual-geometry GLB candidates."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import trimesh

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def inspect_glb(path: Path) -> dict:
    r={"path":str(path),"exists":path.is_file(),"sha256":None,"file_bytes":None,
       "mesh_count":0,"meshes":[],"errors":[],"structural_status":"FAIL"}
    if not path.is_file():
        r["errors"].append("FILE_NOT_FOUND"); return r
    r["file_bytes"]=path.stat().st_size; r["sha256"]=sha256(path)
    if r["file_bytes"]<20:
        r["errors"].append("FILE_TOO_SMALL"); return r
    try: scene=trimesh.load(path,force="scene",process=False)
    except Exception as exc:
        r["errors"].append("GLB_LOAD_ERROR:"+str(exc)[:240]); return r
    for name,mesh in scene.geometry.items():
        if not isinstance(mesh,trimesh.Trimesh):
            r["errors"].append("NON_TRIANGLE_GEOMETRY:"+str(name)); continue
        v,f=mesh.vertices,mesh.faces
        finite=bool(len(v)) and bool(np.isfinite(v).all())
        valid=bool(len(f)) and int(f.min())>=0 and int(f.max())<len(v)
        item={"name":str(name),"vertices":int(len(v)),"faces":int(len(f)),
              "finite_vertices":finite,"valid_face_indices":valid,
              "watertight":bool(mesh.is_watertight),
              "winding_consistent":bool(mesh.is_winding_consistent),
              "bounds_normalized_units":mesh.bounds.tolist() if len(v) else None,
              "extents_normalized_units":mesh.extents.tolist() if len(v) else None}
        r["meshes"].append(item)
        if not finite:r["errors"].append("NONFINITE_OR_EMPTY_VERTICES:"+str(name))
        if not valid:r["errors"].append("INVALID_OR_EMPTY_FACES:"+str(name))
        if not item["watertight"]:r["errors"].append("NOT_WATERTIGHT:"+str(name))
        if not item["winding_consistent"]:r["errors"].append("INCONSISTENT_WINDING:"+str(name))
    r["mesh_count"]=len(r["meshes"])
    r["structural_status"]="PASS" if r["mesh_count"] and not r["errors"] else "FAIL"
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--body",type=Path,required=True)
    p.add_argument("--lower-skirt",type=Path,required=True)
    p.add_argument("--state",choices=["BASE-UNLOADED","DISPLAYED-ATTACHED","UNKNOWN"],default="UNKNOWN")
    p.add_argument("--source-manifest",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    body,skirt=inspect_glb(a.body),inspect_glb(a.lower_skirt)
    source=None; source_status="NOT_PROVIDED"
    if a.source_manifest:
        try: source=json.loads(a.source_manifest.read_text(encoding="utf-8")); source_status="PRESENT_UNREVIEWED"
        except Exception as exc: source={"error":str(exc)[:240]}; source_status="INVALID"
    blockers=[]
    if body["structural_status"]!="PASS":blockers.append("BODY_MESH_STRUCTURAL_QA_FAILED")
    if skirt["structural_status"]!="PASS":blockers.append("LOWER_SKIRT_MESH_STRUCTURAL_QA_FAILED")
    if a.state=="UNKNOWN":blockers.append("VISUAL_STATE_NOT_CONFIRMED")
    if source_status=="INVALID":blockers.append("SOURCE_MANIFEST_INVALID")
    report={"project":"KMH Myanmar Balloon 3D Intelligence","asset_id":"KMH-BAL-001",
      "qa_version":"1.0","scope":"NON_OPERATIONAL_VISUAL_GEOMETRY_STRUCTURAL_QA_ONLY",
      "state":a.state,"body":body,"lower_skirt":skirt,"source_manifest_status":source_status,
      "source_manifest":source,"decision":"STRUCTURAL_QA_PASS_REQUIRES_EVIDENCE_REVIEW" if not blockers else "BLOCKED_HOLD",
      "blockers":blockers,"limitations":[
        "Mesh topology checks do not establish physical dimensions or scale.",
        "Mesh topology checks do not establish visual fidelity or source provenance.",
        "No camera calibration, photogrammetry, state comparison, or physical measurement is performed.",
        "Normalized coordinates are not physical units.",
        "This tool does not authorize geometry promotion, merge, production, or operational use."
      ],"promotion_authorized":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("DECISION:",report["decision"])
    print("BODY:",body["structural_status"],"meshes=",body["mesh_count"])
    print("LOWER_SKIRT:",skirt["structural_status"],"meshes=",skirt["mesh_count"])
    print("PROMOTION_AUTHORIZED: false")
    return 0 if not blockers else 1
if __name__=="__main__": raise SystemExit(main())
