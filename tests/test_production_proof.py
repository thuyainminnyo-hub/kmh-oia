import unittest

from src.production_proof import ProductionProofGate, ProofArtifact


class ProductionProofTests(unittest.TestCase):
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
            outcome="verified outcome",
        )

    def test_complete_bundle_is_proof_ready(self):
        gate = ProductionProofGate()
        self.assertTrue(gate.evaluate(self.artifact))
        self.assertTrue(self.artifact.proof_ready)
        self.assertTrue(all(self.artifact.checks.values()))

    def test_failed_qa_blocks_proof(self):
        artifact = ProofArtifact(
            execution_id=self.artifact.execution_id,
            identity=self.artifact.identity,
            trace_id=self.artifact.trace_id,
            evidence=self.artifact.evidence,
            qa_status="FAIL",
            outcome=self.artifact.outcome,
        )
        self.assertFalse(ProductionProofGate().evaluate(artifact))
        with self.assertRaises(ValueError):
            ProductionProofGate().require_ready(artifact)

    def test_missing_identity_is_rejected(self):
        identity = dict(self.artifact.identity)
        identity.pop("instance_id")
        with self.assertRaises(ValueError):
            ProofArtifact(
                execution_id=self.artifact.execution_id,
                identity=identity,
                trace_id=self.artifact.trace_id,
                evidence=self.artifact.evidence,
                qa_status="PASS",
                outcome=self.artifact.outcome,
            )

    def test_bundle_is_serializable_shape(self):
        bundle = self.artifact.bundle()
        self.assertTrue(bundle["proof_ready"])
        self.assertEqual(bundle["trace_id"], "trace-1")
        self.assertEqual(bundle["identity"]["account_id"], "acct-a")


if __name__ == "__main__":
    unittest.main()
