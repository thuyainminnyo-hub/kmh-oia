import unittest
from types import SimpleNamespace

from src.production_proof import ProofArtifact
from src.real_execution_verifier import RealExecutionVerifier


class RealExecutionVerifierTests(unittest.TestCase):
    def setUp(self):
        self.artifact = ProofArtifact(
            execution_id="exec:1",
            identity={
                "account_id": "acct-a",
                "instance_id": "inst-a",
                "environment_id": "prod-a",
                "session_id": "sess-a",
            },
            trace_id="trace-1",
            evidence=("trace_id=trace-1", "response=ok"),
            qa_status="PASS",
            outcome="ok",
        )
        self.execution = SimpleNamespace(
            response="ok",
            trace_stages=("gateway", "runtime"),
            evidence=(
                "trace_id=trace-1",
                "response=ok",
                "account_id=acct-a",
                "instance_id=inst-a",
                "environment_id=prod-a",
                "session_id=sess-a",
            ),
            qa_status="PASS",
            execution_identity=SimpleNamespace(execution_id="exec:1"),
        )

    def test_matching_execution_is_verified(self):
        result = RealExecutionVerifier().verify(self.artifact, self.execution)
        self.assertTrue(result.verified)
        self.assertTrue(all(result.checks.values()))

    def test_wrong_execution_identity_is_rejected(self):
        execution = SimpleNamespace(**{**vars(self.execution),
            "execution_identity": SimpleNamespace(execution_id="exec:other")})
        result = RealExecutionVerifier().verify(self.artifact, execution)
        self.assertFalse(result.verified)
        self.assertFalse(result.checks["execution_id"])

    def test_wrong_outcome_is_rejected(self):
        execution = SimpleNamespace(**{**vars(self.execution), "response": "different"})
        result = RealExecutionVerifier().verify(self.artifact, execution)
        self.assertFalse(result.verified)
        self.assertFalse(result.checks["outcome"])


if __name__ == "__main__":
    unittest.main()
