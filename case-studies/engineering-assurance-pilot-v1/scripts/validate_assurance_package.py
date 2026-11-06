"""Fail-closed structural validator for the Engineering Assurance Pilot package."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {
    "architecture", "security", "data", "runtime-reliability",
    "delivery-observability", "ai-agent-engineering",
}
STATUSES = {"NOT_ASSESSED", "PASS", "FAIL", "BLOCKED", "NOT_RUN"}
FINDING_STATUSES = {"CONFIRMED", "NEEDS_VALIDATION", "ACCEPTED_RISK", "REJECTED_FALSE_POSITIVE"}
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNASSESSED"}


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def validate_finding(finding: dict, evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    fid = finding.get("finding_id", "<missing-id>")
    required = ("finding_id", "domain", "title", "status", "severity", "source",
                "evidence_refs", "impact", "recommendation", "review")
    for key in required:
        if key not in finding:
            errors.append(f"finding {fid} missing {key}")
    if finding.get("domain") not in DOMAINS:
        errors.append(f"finding {fid} has invalid domain")
    if finding.get("status") not in FINDING_STATUSES:
        errors.append(f"finding {fid} has invalid status")
    if finding.get("severity") not in SEVERITIES:
        errors.append(f"finding {fid} has invalid severity")
    refs = finding.get("evidence_refs", [])
    if not isinstance(refs, list) or not refs:
        errors.append(f"finding {fid} has no evidence references")
    elif any(ref not in evidence_ids for ref in refs):
        errors.append(f"finding {fid} references unknown evidence")
    if finding.get("status") == "ACCEPTED_RISK" and not finding.get("decision_rationale"):
        errors.append(f"accepted risk {fid} requires rationale")
    if finding.get("status") == "REJECTED_FALSE_POSITIVE" and not finding.get("counter_evidence"):
        errors.append(f"rejected finding {fid} requires counter-evidence")
    review = finding.get("review", {})
    if review.get("status") == "VERIFIED" and not review.get("independent_reviewer"):
        errors.append(f"verified finding {fid} requires independent reviewer")
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    scope = load("contracts/scope-inventory.json")
    ledger = load("artifacts/evidence-ledger.json")
    gate = load("contracts/qa-gate.json")
    finding_schema = load("contracts/finding.schema.json")

    domain_ids = [item.get("id") for item in scope.get("domains", [])]
    if set(domain_ids) != DOMAINS or len(domain_ids) != len(DOMAINS):
        errors.append("scope inventory must contain each required domain exactly once")
    for item in scope.get("domains", []):
        if item.get("status") not in STATUSES:
            errors.append(f"invalid status for domain {item.get('id')}")
    if scope.get("execution_boundary") != "sandbox-only":
        errors.append("execution boundary must remain sandbox-only")
    if gate.get("production_deployment_allowed") is not False:
        errors.append("production deployment must remain disabled")
    if gate.get("default_decision") != "BLOCKED":
        errors.append("default QA decision must fail closed to BLOCKED")
    if set(gate.get("required_domains", [])) != DOMAINS:
        errors.append("QA gate required domains do not match inventory")
    if finding_schema.get("type") != "object" or finding_schema.get("additionalProperties") is not False:
        errors.append("finding schema must be a closed object")

    inspection = ledger.get("repository_inspection", [])
    evidence_ids = {item.get("id") for item in inspection}
    if len(evidence_ids) != len(inspection) or None in evidence_ids:
        errors.append("evidence IDs must be present and unique")
    if ledger.get("assurance_execution", {}).get("status") not in {"NOT_RUN", "PASS", "FAIL", "BLOCKED"}:
        errors.append("invalid assurance execution status")
    if ledger.get("human_approval", {}).get("status") != "NOT_GRANTED":
        errors.append("initial human approval must not be fabricated")
    if ledger.get("independent_verification", {}).get("status") != "NOT_RUN":
        errors.append("initial independent verification must remain NOT_RUN")
    if ledger.get("rollback", {}).get("status") != "PLAN_DEFINED_NOT_EXECUTED":
        errors.append("rollback must be recorded as planned, not executed")

    findings = ledger.get("findings", [])
    finding_ids = [f.get("finding_id") for f in findings]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append("finding IDs must be unique")
    for finding in findings:
        errors.extend(validate_finding(finding, evidence_ids))
    return errors


if __name__ == "__main__":
    issues = validate()
    if issues:
        print("FAIL")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)
    print("PASS: package structure and fail-closed governance invariants")
