"""Independent verification of runtime proof records.

This verifier checks consistency and completeness of supplied runtime artifacts.
It does not claim external infrastructure or production reality beyond the
evidence carried by the execution record.
"""
from dataclasses import dataclass
from typing import Mapping

from src.production_proof import ProductionProofGate, ProofArtifact


@dataclass(frozen=True)
class VerificationResult:
    execution_id: str
    verified: bool
    checks: Mapping[str, bool]
    reason: str


class RealExecutionVerificationEngine:
    """Turn an execution record into a verifiable proof decision."""

    def __init__(self, proof_gate: ProductionProofGate | None = None) -> None:
        self.proof_gate = proof_gate or ProductionProofGate()

    def verify(self, record) -> VerificationResult:
        identity_context = getattr(record, "execution_identity", None)
        execution_id = self._execution_id(record, identity_context)
        trace_stages = tuple(getattr(record, "trace_stages", ()))
        evidence = tuple(getattr(record, "evidence", ()))
        qa_status = str(getattr(record, "qa_status", "")).strip().upper()
        outcome = str(getattr(record, "response", "")).strip()

        identity = {}
        if identity_context is not None:
            identity = identity_context.identity.provenance()

        checks = {
            "identity": self._identity_complete(identity),
            "trace": bool(trace_stages) and self._evidence_contains(evidence, "trace_id="),
            "evidence": bool(evidence),
            "qa": qa_status == "PASS",
            "outcome": bool(outcome),
        }

        if all(checks.values()):
            artifact = ProofArtifact(
                execution_id=execution_id,
                identity=identity,
                trace_id=self._trace_id(evidence),
                evidence=evidence,
                qa_status=qa_status,
                outcome=outcome,
            )
            verified = self.proof_gate.evaluate(artifact)
        else:
            verified = False

        reason = (
            "execution proof verified"
            if verified
            else "execution proof incomplete or failed verification"
        )
        return VerificationResult(execution_id, verified, checks, reason)

    @staticmethod
    def _execution_id(record, identity_context) -> str:
        if identity_context is not None:
            return identity_context.execution_id
        loop = getattr(record, "operating_loop", None)
        if loop is not None:
            return loop.execution_id
        raise ValueError("execution identity or operating loop is required")

    @staticmethod
    def _identity_complete(identity: Mapping[str, str]) -> bool:
        required = ("account_id", "instance_id", "environment_id", "session_id")
        return all(str(identity.get(key, "")).strip() for key in required)

    @staticmethod
    def _evidence_contains(evidence: tuple[str, ...], prefix: str) -> bool:
        return any(item.startswith(prefix) and item[len(prefix):].strip() for item in evidence)

    @staticmethod
    def _trace_id(evidence: tuple[str, ...]) -> str:
        for item in evidence:
            if item.startswith("trace_id="):
                value = item.split("=", 1)[1].strip()
                if value:
                    return value
        raise ValueError("trace_id evidence is required")
