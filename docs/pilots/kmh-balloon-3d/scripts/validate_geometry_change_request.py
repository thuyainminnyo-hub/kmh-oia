#!/usr/bin/env python3
"""Evaluate evidence completeness for a KMH geometry change request.

The validator never edits geometry, approves a PR, merges, or deploys.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_STATES = {"BASE-UNLOADED", "DISPLAYED-ATTACHED"}
PASS = {"PASS", "PASSED", "APPROVED"}
REQUIRED_QA = {
    "mesh_integrity", "dimension_residuals", "silhouette_comparison",
    "state_consistency", "source_provenance"
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("request", type=Path)
    ap.add_argument("--asset-root", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    try:
        data = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read change request: {exc}")
        return 2

    blockers = []
    if data.get("target_state") not in ALLOWED_STATES:
        blockers.append("Target state must be confirmed BASE-UNLOADED or DISPLAYED-ATTACHED.")

    baseline = data.get("baseline", {})
    proposed = data.get("proposed_assets", {})
    for name in ("body_file", "body_sha256", "lower_skirt_file", "lower_skirt_sha256"):
        if not baseline.get(name):
            blockers.append(f"Baseline field missing: {name}.")
    for name in ("body_file", "body_sha256", "lower_skirt_file", "lower_skirt_sha256"):
        if not proposed.get(name):
            blockers.append(f"Proposed asset field missing: {name}.")

    evidence = data.get("supporting_evidence", {})
    for field in ("source_confirmation_record", "capture_set_manifest",
                  "camera_calibration_record", "scale_control_record", "measurement_record"):
        if not evidence.get(field):
            blockers.append(f"Supporting evidence missing: {field}.")
    if evidence.get("state_attribution_confirmed") is not True:
        blockers.append("State attribution has not been confirmed.")
    if evidence.get("independent_measurement_verified") is not True:
        blockers.append("Independent measurement verification is incomplete.")
    if not evidence.get("source_image_hashes"):
        blockers.append("Source image hashes are missing.")

    qa = data.get("qa_results", {})
    for field in REQUIRED_QA:
        if qa.get(field) not in PASS:
            blockers.append(f"QA result not passed: {field}.")
    if qa.get("limitations_recorded") is not True:
        blockers.append("Limitations have not been recorded.")

    approvals = data.get("approvals", {})
    for role in ("technical_reviewer", "project_owner"):
        item = approvals.get(role, {})
        if item.get("decision") != "APPROVED":
            blockers.append(f"{role} approval is missing.")
        for field in ("name_or_role", "date", "evidence_reference"):
            if not item.get(field):
                blockers.append(f"{role} approval missing {field}.")

    release = data.get("release", {})
    if release.get("authorized") is not True:
        blockers.append("Explicit release authorization is false.")
    if release.get("merge_approval") != "APPROVED":
        blockers.append("Merge approval is missing.")
    if release.get("production_approval") not in {"APPROVED", "NOT_IN_SCOPE"}:
        blockers.append("Production approval is missing or not explicitly out of scope.")

    guard = data.get("scope_guard", {})
    if guard.get("non_operational_visual_geometry_only") is not True:
        blockers.append("Non-operational visual-only scope guard is not enabled.")
    if guard.get("pyrotechnic_operational_calculation_included") is not False:
        blockers.append("Pyrotechnic operational calculations must be excluded.")
    if guard.get("attachment_mechanics_inferred") is not False:
        blockers.append("Attachment mechanics must not be inferred.")

    file_checks = []
    if args.asset_root is not None:
        for label, path_key, hash_key in [
            ("baseline body", "body_file", "body_sha256"),
            ("baseline lower skirt", "lower_skirt_file", "lower_skirt_sha256")
        ]:
            relative = baseline.get(path_key)
            if not relative:
                continue
            path = args.asset_root / relative
            if not path.is_file():
                blockers.append(f"{label} file missing from asset root.")
            else:
                actual = sha256(path)
                matches = actual == baseline.get(hash_key)
                file_checks.append({"asset":label,"sha256":actual,"matches":matches})
                if not matches:
                    blockers.append(f"{label} hash does not match locked baseline.")

    report = {
        "change_request_id": data.get("change_request_id"),
        "target_state": data.get("target_state"),
        "decision": "BLOCKED_HOLD" if blockers else "ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "baseline_file_checks": file_checks,
        "note": "Evidence completeness only; this validator never approves, edits, merges, or deploys geometry."
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"DECISION: {report['decision']}")
    print(f"BLOCKERS: {len(blockers)}")
    for blocker in blockers:
        print(f"- {blocker}")
    if file_checks:
        print(f"BASELINE FILE HASH CHECKS: {sum(x['matches'] for x in file_checks)}/{len(file_checks)} match")
    print("NOTE: no geometry was modified.")
    return 0 if not blockers else 1

if __name__ == "__main__":
    raise SystemExit(main())
