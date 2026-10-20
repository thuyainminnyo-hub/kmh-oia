"""Machine-readable release readiness assessment for KMH OIA evidence runtime.

This report is intentionally conservative: repository checks cannot mark live
deployment, real provider authenticity, external business outcomes, or shared
multi-host storage as verified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Literal

GateStatus = Literal["PASS", "HOLD", "NOT_VERIFIED"]


@dataclass(frozen=True)
class ReadinessGate:
    gate: str
    status: GateStatus
    evidence: str
    next_action: str


def build_readiness_snapshot(root: Path | str = ".") -> dict[str, object]:
    """Return current repository-observable readiness; never infer live success."""
    base = Path(root)
    required = (
        "src/production_evidence_runtime.py",
        "src/receipt_replay_store.py",
        "src/trusted_source_receipt.py",
        "scripts/deployment_preflight.py",
        "docs/runbooks/production-evidence-runtime.md",
    )
    missing = [path for path in required if not (base / path).is_file()]
    gates = [
        ReadinessGate(
            "repository_contracts",
            "PASS" if not missing else "HOLD",
            "Required runtime, replay, verifier, preflight and runbook files exist."
            if not missing else "Missing required files: " + ", ".join(missing),
            "Keep contract tests green." if not missing else "Restore missing files, then re-run validation.",
        ),
        ReadinessGate(
            "durable_single_host_replay",
            "PASS" if not missing else "HOLD",
            "Repository includes SQLite replay store and production factory; automated tests cover replay after runtime recreation.",
            "Run a real OS-process restart test on the target host.",
        ),
        ReadinessGate(
            "live_deployment",
            "NOT_VERIFIED",
            "Repository files and CI cannot prove that a live deployment exists or is healthy.",
            "Deploy using persistent storage and capture health/startup/restart receipts.",
        ),
        ReadinessGate(
            "real_provider_authenticity_and_attribution",
            "NOT_VERIFIED",
            "The repository defines a generic adapter contract; fake-adapter tests are not real provider verification.",
            "Implement and review one provider-specific authenticity and execution-attribution adapter.",
        ),
        ReadinessGate(
            "external_business_outcome",
            "HOLD",
            "No verified provider-backed outcome receipt is part of this repository snapshot.",
            "Keep EXEC-SUN-TRAVEL-005 on HOLD until source-linked external evidence is independently checked.",
        ),
        ReadinessGate(
            "multi_host_replay",
            "NOT_VERIFIED",
            "SQLite replay guard is scoped to one local/shared-file host environment.",
            "Implement a shared transactional store and concurrency test before multi-host use.",
        ),
    ]
    summary = "HOLD" if any(g.status == "HOLD" for g in gates) else (
        "READY_FOR_REVIEW" if all(g.status == "PASS" for g in gates) else "NOT_VERIFIED"
    )
    return {
        "schema_version": "1.0",
        "assessment_scope": "repository-observable release readiness; not proof of production deployment",
        "release_decision": summary,
        "required_files_missing": missing,
        "gates": [asdict(gate) for gate in gates],
        "limitations": [
            "CI PASS is not live deployment verification.",
            "Fake adapters do not authenticate a real external provider.",
            "No external outcome evidence means outcome status is unknown, not necessarily negative.",
        ],
    }


def main() -> int:
    snapshot = build_readiness_snapshot()
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    # This report produces a HOLD exit status when release blockers exist.
    return 0 if snapshot["release_decision"] == "READY_FOR_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
