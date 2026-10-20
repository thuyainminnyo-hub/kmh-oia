"""Build a deployment evidence bundle without pretending unobserved gates passed.

The bundle is a handoff checklist: repository/CI facts supplied by the operator
are recorded separately from evidence collected on the target host. It never
queries GitHub or a deployment environment itself; callers must supply verified
run metadata and actual smoke-test JSON.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TARGET_FIELDS = (
    "environment_id",
    "host_or_service_id",
    "persistent_volume_confirmed",
    "database_path",
    "smoke_test_report",
    "smoke_tested_at_utc",
    "commit_sha",
)


def build_bundle(
    *,
    commit_sha: str,
    ci_runs: list[dict[str, Any]],
    target_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a conservative JSON deployment evidence bundle."""
    target = target_evidence or {}
    missing_target = [
        field for field in REQUIRED_TARGET_FIELDS
        if field not in target or target[field] in (None, "")
    ]

    smoke_report = target.get("smoke_test_report")
    smoke_pass = isinstance(smoke_report, dict) and smoke_report.get("result") == "PASS"
    volume_confirmed = target.get("persistent_volume_confirmed") is True
    same_commit = bool(target.get("commit_sha")) and target.get("commit_sha") == commit_sha
    target_gate_pass = (
        not missing_target
        and smoke_pass
        and volume_confirmed
        and same_commit
    )

    normalized_runs = []
    for run in ci_runs:
        head_sha = run.get("head_sha", "")
        conclusion = run.get("conclusion", "NOT_VERIFIED")
        normalized_runs.append({
            "name": run.get("name", "unknown"),
            "url": run.get("url", ""),
            "head_sha": head_sha,
            "conclusion": conclusion,
            "matches_bundle_commit": head_sha == commit_sha,
            "is_required_check": run.get("is_required_check", True) is True,
        })
    required_checks = [
        row for row in normalized_runs if row["is_required_check"]
    ]
    required_green = bool(required_checks) and all(
        row["conclusion"] == "success" and row["matches_bundle_commit"]
        for row in required_checks
    )

    gates = [
        {
            "gate": "repository_ci_for_bundle_commit",
            "status": "PASS" if required_green else "NOT_VERIFIED",
            "evidence": normalized_runs,
            "next_action": "Keep exact-SHA required checks green." if required_green else
                "Supply successful required CI runs for this exact commit SHA.",
        },
        {
            "gate": "target_host_persistent_storage_and_process_replay",
            "status": "PASS" if target_gate_pass else "NOT_VERIFIED",
            "evidence": {
                key: target.get(key)
                for key in REQUIRED_TARGET_FIELDS
                if key in target
            },
            "missing_fields": missing_target,
            "next_action": "Have an operator run the smoke test on the target host, confirm the persistent volume, and record the tested commit." if not target_gate_pass else
                "Keep the captured target-host receipt with the release record.",
        },
        {
            "gate": "real_provider_authenticity_and_execution_attribution",
            "status": "NOT_VERIFIED",
            "evidence": "This bundle does not authenticate a provider-specific receipt.",
            "next_action": "Integrate a reviewed provider-specific adapter and capture a real signed/authenticated source receipt.",
        },
        {
            "gate": "external_business_outcome",
            "status": "HOLD",
            "evidence": "No independently verified external outcome receipt was supplied to this bundle.",
            "next_action": "Keep EXEC-SUN-TRAVEL-005 on HOLD until source record, execution attribution, and verification evidence are reviewed.",
        },
        {
            "gate": "multi_host_replay",
            "status": "NOT_VERIFIED",
            "evidence": "SQLite local-file smoke tests do not demonstrate multi-host atomic replay protection.",
            "next_action": "Use a shared transactional store with a cross-host duplicate-claim concurrency test before multi-host deployment.",
        },
    ]
    overall = "HOLD" if any(gate["status"] == "HOLD" for gate in gates) else (
        "READY_FOR_REVIEW" if all(gate["status"] == "PASS" for gate in gates) else "NOT_VERIFIED"
    )
    return {
        "schema_version": "1.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_commit_sha": commit_sha,
        "assessment_scope": "deployment evidence handoff; not self-attestation of deployment",
        "release_decision": overall,
        "gates": gates,
        "limitations": [
            "CI success is not a production deployment.",
            "Only checks marked is_required_check contribute to repository CI gate.",
            "Operator-provided volume confirmation must correspond to the actual target environment.",
            "A local SQLite process-boundary test does not prove multi-host behavior.",
            "No outcome receipt supplied means outcome is unverified, not proven negative.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--ci-runs", type=Path, required=True, help="JSON array of CI run metadata")
    parser.add_argument("--target-evidence", type=Path, help="Optional operator-collected target evidence JSON")
    parser.add_argument("--output", type=Path, default=Path("deployment-evidence-bundle.json"))
    args = parser.parse_args()

    try:
        runs = json.loads(args.ci_runs.read_text(encoding="utf-8"))
        if not isinstance(runs, list):
            raise ValueError("--ci-runs must contain a JSON array")
        target = (
            json.loads(args.target_evidence.read_text(encoding="utf-8"))
            if args.target_evidence else {}
        )
        if not isinstance(target, dict):
            raise ValueError("--target-evidence must contain a JSON object")
        bundle = build_bundle(commit_sha=args.commit_sha, ci_runs=runs, target_evidence=target)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"bundle generation failed: {type(exc).__name__}: {exc}")
        return 1

    print(json.dumps({
        "output": str(args.output),
        "release_decision": bundle["release_decision"],
        "ci_status": bundle["gates"][0]["status"],
        "target_host_status": bundle["gates"][1]["status"],
        "outcome_status": bundle["gates"][3]["status"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
