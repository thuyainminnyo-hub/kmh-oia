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
REQUIRED_SMOKE_FIELDS = (
    "schema_version",
    "test",
    "db_path",
    "first_process",
    "second_process",
    "result",
)
EXPECTED_SMOKE_TEST = "sqlite_replay_across_independent_os_processes"


def validate_target_evidence(target: dict[str, Any], commit_sha: str) -> tuple[bool, list[str]]:
    """Fail closed unless target evidence matches the complete smoke receipt contract."""
    errors: list[str] = []
    for key in ("environment_id", "host_or_service_id", "database_path"):
        if not isinstance(target.get(key), str) or not target[key].strip():
            errors.append(f"{key} must be a non-empty string")

    if target.get("persistent_volume_confirmed") is not True:
        errors.append("persistent_volume_confirmed must be true")
    if target.get("commit_sha") != commit_sha or not commit_sha:
        errors.append("target commit_sha must match bundle commit_sha")

    tested_at = target.get("smoke_tested_at_utc")
    if not isinstance(tested_at, str) or not tested_at.strip():
        errors.append("smoke_tested_at_utc is required")
    else:
        try:
            parsed = datetime.fromisoformat(tested_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                errors.append("smoke_tested_at_utc must include a timezone")
            elif parsed.utcoffset().total_seconds() != 0:
                errors.append("smoke_tested_at_utc must be UTC")
        except ValueError:
            errors.append("smoke_tested_at_utc must be a valid ISO-8601 datetime")

    report = target.get("smoke_test_report")
    if not isinstance(report, dict):
        errors.append("smoke_test_report must be a JSON object")
    else:
        for key in REQUIRED_SMOKE_FIELDS:
            if key not in report:
                errors.append(f"smoke_test_report missing {key}")
        if report.get("result") != "PASS":
            errors.append("smoke_test_report result must be PASS")
        if report.get("test") != EXPECTED_SMOKE_TEST:
            errors.append(f"smoke_test_report test must be {EXPECTED_SMOKE_TEST}")
        if not isinstance(report.get("first_process"), dict):
            errors.append("smoke_test_report first_process must be an object")
        else:
            first = report["first_process"]
            if first.get("healthy") is not True or first.get("accepted") is not True:
                errors.append("first_process must be healthy and accept the claim")
        if not isinstance(report.get("second_process"), dict):
            errors.append("smoke_test_report second_process must be an object")
        else:
            second = report["second_process"]
            if second.get("healthy") is not True or second.get("accepted") is not False:
                errors.append("second_process must be healthy and reject the duplicate")
            if "replay" not in str(second.get("reason", "")).lower():
                errors.append("second_process reason must identify replay rejection")
        report_db = report.get("db_path")
        if not isinstance(report_db, str) or not report_db:
            errors.append("smoke_test_report db_path must be a non-empty string")
        elif report_db != target.get("database_path"):
            errors.append("smoke_test_report db_path must match database_path")

    return not errors, errors


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
    target_valid, target_errors = validate_target_evidence(target, commit_sha)

    normalized_runs = []
    for run in ci_runs:
        if not isinstance(run, dict):
            normalized_runs.append({
                "name": "invalid",
                "url": "",
                "head_sha": "",
                "conclusion": "NOT_VERIFIED",
                "matches_bundle_commit": False,
                "is_required_check": True,
            })
            continue
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
            "status": "PASS" if target_valid else "NOT_VERIFIED",
            "evidence": {
                key: target.get(key)
                for key in REQUIRED_TARGET_FIELDS
                if key in target
            },
            "missing_fields": missing_target,
            "validation_errors": target_errors,
            "next_action": "Have an operator run the smoke test on the target host, confirm the persistent volume, and record the tested commit." if not target_valid else
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
        "schema_version": "1.2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_commit_sha": commit_sha,
        "assessment_scope": "deployment evidence handoff; not self-attestation of deployment",
        "release_decision": overall,
        "gates": gates,
        "limitations": [
            "CI success is not a production deployment.",
            "Only checks marked is_required_check contribute to repository CI gate.",
            "Operator-provided volume confirmation must correspond to the actual target environment.",
            "Target-host replay passes only when the full smoke receipt matches the claimed database path and commit.",
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
