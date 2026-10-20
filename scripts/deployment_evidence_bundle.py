"""Build a deployment evidence bundle without pretending unobserved gates passed.

CI metadata is supplied by the workflow that ran the checks. This module validates
its shape and commit/conclusion fields; it does not independently query GitHub.
Target-host evidence is separately supplied and fail-closed validated.
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
REQUIRED_CI_FIELDS = ("name", "url", "head_sha", "conclusion", "is_required_check")


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


def validate_ci_runs(commit_sha: str, ci_runs: list[Any]) -> tuple[list[dict[str, Any]], bool, list[str]]:
    """Normalize CI run rows and require explicit identity, URL, conclusion and SHA."""
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, run in enumerate(ci_runs):
        row_errors: list[str] = []
        if not isinstance(run, dict):
            errors.append(f"CI row {index} must be a JSON object")
            normalized.append({
                "name": "invalid",
                "url": "",
                "head_sha": "",
                "conclusion": "NOT_VERIFIED",
                "matches_bundle_commit": False,
                "is_required_check": True,
                "validation_errors": ["row must be an object"],
            })
            continue

        missing = [key for key in REQUIRED_CI_FIELDS if key not in run]
        for key in missing:
            row_errors.append(f"missing {key}")
        name = run.get("name", "")
        url = run.get("url", "")
        head_sha = run.get("head_sha", "")
        conclusion = run.get("conclusion", "NOT_VERIFIED")
        required_flag = run.get("is_required_check")
        if not isinstance(name, str) or not name.strip():
            row_errors.append("name must be a non-empty string")
        if not isinstance(url, str) or not url.startswith("https://github.com/"):
            row_errors.append("url must be a GitHub HTTPS run URL")
        if not isinstance(head_sha, str) or not head_sha.strip():
            row_errors.append("head_sha must be a non-empty string")
        if not isinstance(conclusion, str) or not conclusion.strip():
            row_errors.append("conclusion must be a non-empty string")
        if not isinstance(required_flag, bool):
            row_errors.append("is_required_check must be a boolean")

        matches = isinstance(head_sha, str) and bool(head_sha) and head_sha == commit_sha
        is_required = required_flag is True
        if is_required and conclusion != "success":
            row_errors.append("required CI check conclusion must be success")
        if is_required and not matches:
            row_errors.append("required CI check head_sha must match bundle commit")
        normalized.append({
            "name": name if isinstance(name, str) else "invalid",
            "url": url if isinstance(url, str) else "",
            "head_sha": head_sha if isinstance(head_sha, str) else "",
            "conclusion": conclusion if isinstance(conclusion, str) else "NOT_VERIFIED",
            "matches_bundle_commit": matches,
            "is_required_check": is_required,
            "validation_errors": row_errors,
        })
        if row_errors:
            errors.extend(f"CI row {index}: {error}" for error in row_errors)

    required_checks = [row for row in normalized if row["is_required_check"]]
    required_green = bool(required_checks) and all(
        not row["validation_errors"]
        and row["conclusion"] == "success"
        and row["matches_bundle_commit"]
        for row in required_checks
    ) and not any(
        row["is_required_check"] and row["validation_errors"]
        for row in normalized
    )
    # Malformed optional rows do not pass as evidence; they also don't gate
    # required checks. Preserve their errors so reviewers can see the issue.
    return normalized, required_green, errors


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
    normalized_runs, required_green, ci_errors = validate_ci_runs(commit_sha, ci_runs)

    gates = [
        {
            "gate": "repository_ci_for_bundle_commit",
            "status": "PASS" if required_green else "NOT_VERIFIED",
            "evidence": normalized_runs,
            "validation_errors": ci_errors,
            "next_action": "Keep exact-SHA required checks green." if required_green else
                "Supply complete CI run metadata (name, GitHub HTTPS URL, exact head SHA, conclusion, and required-check flag) for successful required checks.",
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
        "schema_version": "1.3",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_commit_sha": commit_sha,
        "assessment_scope": "deployment evidence handoff; not self-attestation of deployment",
        "release_decision": overall,
        "gates": gates,
        "limitations": [
            "CI success is not a production deployment.",
            "CI metadata is validated for completeness and exact-SHA consistency but is not independently fetched from the GitHub API by this script.",
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
