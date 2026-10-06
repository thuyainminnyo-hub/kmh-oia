"""Production proof artifacts for OIA runtime capabilities.

This module defines a deterministic readiness/proof model. It does not claim
that production execution has occurred; it records supplied evidence.
"""
from dataclasses import dataclass
from typing import Mapping


PROOF_KEYS = ("identity", "trace", "evidence", "qa", "outcome")


@dataclass(frozen=True)
class ProofArtifact:
    execution_id: str
    identity: Mapping[str, str]
    trace_id: str
    evidence: tuple[str, ...]
    qa_status: str
    outcome: str

    def __post_init__(self) -> None:
        if not self.execution_id.strip():
            raise ValueError("execution_id is required")
        if not self.trace_id.strip():
            raise ValueError("trace_id is required")
        if not self.evidence:
            raise ValueError("evidence is required")
        if self.qa_status.strip().upper() not in {"PASS", "FAIL"}:
            raise ValueError("qa_status must be PASS or FAIL")
        if not self.outcome.strip():
            raise ValueError("outcome is required")
        required_identity = {"account_id", "instance_id", "environment_id", "session_id"}
        if not required_identity.issubset(self.identity):
            raise ValueError("identity must contain account_id, instance_id, environment_id, session_id")
        if any(not str(self.identity[key]).strip() for key in required_identity):
            raise ValueError("identity values are required")

    @property
    def checks(self) -> dict[str, bool]:
        return {
            "identity": all(str(self.identity[key]).strip() for key in
                            ("account_id", "instance_id", "environment_id", "session_id")),
            "trace": bool(self.trace_id.strip()),
            "evidence": bool(self.evidence),
            "qa": self.qa_status.strip().upper() == "PASS",
            "outcome": bool(self.outcome.strip()),
        }

    @property
    def proof_ready(self) -> bool:
        return all(self.checks.values())

    def bundle(self) -> dict[str, object]:
        return {
            "execution_id": self.execution_id,
            "identity": dict(self.identity),
            "trace_id": self.trace_id,
            "evidence": list(self.evidence),
            "qa_status": self.qa_status.strip().upper(),
            "outcome": self.outcome,
            "checks": self.checks,
            "proof_ready": self.proof_ready,
        }


class ProductionProofGate:
    """Evaluate supplied execution evidence without inventing production proof."""

    def evaluate(self, artifact: ProofArtifact) -> bool:
        return artifact.proof_ready

    def require_ready(self, artifact: ProofArtifact) -> None:
        if not self.evaluate(artifact):
            missing = [key for key, value in artifact.checks.items() if not value]
            raise ValueError("production proof incomplete: " + ", ".join(missing))
