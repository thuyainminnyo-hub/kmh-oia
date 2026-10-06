"""Verification of production proof against an actual runtime execution record."""

from dataclasses import dataclass

from src.production_proof import ProofArtifact


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    checks: dict[str, bool]
    reason: str


class RealExecutionVerifier:
    """Compare a supplied proof artifact with an actual ExecutionRecord."""

    def verify(self, artifact: ProofArtifact, execution) -> VerificationResult:
        evidence = tuple(execution.evidence)
        identity = artifact.identity
        checks = {
            "execution_id": (
                execution.execution_identity is not None
                and execution.execution_identity.execution_id == artifact.execution_id
            ),
            "identity": all(
                f"{key}={identity[key]}" in evidence
                for key in ("account_id", "instance_id", "environment_id", "session_id")
            ),
            "trace": f"trace_id={artifact.trace_id}" in evidence
            and artifact.trace_id in execution.trace_stages
            or f"trace_id={artifact.trace_id}" in evidence,
            "evidence": bool(evidence) and all(item in evidence for item in artifact.evidence),
            "qa": execution.qa_status.strip().upper() == "PASS"
            and artifact.qa_status.strip().upper() == "PASS",
            "outcome": execution.response == artifact.outcome,
        }
        verified = all(checks.values())
        reason = "actual execution matches proof artifact" if verified else (
            "proof mismatch: " + ", ".join(key for key, value in checks.items() if not value)
        )
        return VerificationResult(verified, checks, reason)
