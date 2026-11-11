import unittest
from dataclasses import replace

from src.execution_evidence import (
    AgentEvidenceClaim,
    ExecutionEvidenceChain,
    build_execution_receipt,
    verify_execution_link,
)


class ExecutionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.claim = AgentEvidenceClaim(
            evidence_service="https://evidence.kmh.example",
            policy_pack_digest="a" * 64,
            logical_agent_id="did:web:kmh.example:agents:agent-1",
            assurance_statement_digest="b" * 64,
        )
        self.request = {
            "method": "POST",
            "path": "/tools/payment",
            "body": {"amount": 1200, "currency": "MMK", "recipient": "vendor-7"},
        }
        self.receipt = build_execution_receipt(
            claim=self.claim,
            request=self.request,
            request_id="req-001",
            runtime_agent_id="spiffe://kmh.example/ns/prod/sa/agent-1",
            sequence=1,
            resource="vendor-7",
            tool="payment",
            action="create-payment",
            decision="deny",
            reason_code="human-approval-required",
            occurred_at_epoch=1_800_000_000,
        )

    def verify(self, receipt=None, request=None, **overrides):
        values = dict(
            receipt=receipt or self.receipt,
            actual_request=request or self.request,
            actual_request_id="req-001",
            audit_event_sequence=1,
            expected_logical_agent_id=self.claim.logical_agent_id,
            expected_runtime_agent_id="spiffe://kmh.example/ns/prod/sa/agent-1",
            expected_evidence_service=self.claim.evidence_service,
            expected_policy_pack_digest=self.claim.policy_pack_digest,
        )
        values.update(overrides)
        return verify_execution_link(**values)

    def test_receipt_binds_actual_request_to_identity_policy_and_audit_sequence(self):
        linked = self.verify()
        self.assertIsNotNone(linked)
        self.assertEqual(linked.request_digest, self.receipt.request_digest)
        self.assertEqual(linked.audit_event_sequence, 1)

    def test_request_body_tampering_breaks_link(self):
        altered = {
            **self.request,
            "body": {"amount": 12000, "currency": "MMK", "recipient": "vendor-7"},
        }
        self.assertIsNone(self.verify(request=altered))

    def test_request_id_runtime_identity_policy_and_sequence_are_bound(self):
        self.assertIsNone(self.verify(actual_request_id="req-other"))
        self.assertIsNone(self.verify(expected_runtime_agent_id="spiffe://other"))
        self.assertIsNone(self.verify(expected_policy_pack_digest="c" * 64))
        self.assertIsNone(self.verify(audit_event_sequence=2))


    def test_execution_receipt_chain_is_contiguous_and_verifiable(self):
        chain = ExecutionEvidenceChain()
        first = chain.append(self.receipt)
        second_input = build_execution_receipt(
            claim=self.claim, request=self.request, request_id="req-002",
            runtime_agent_id="runtime-1", sequence=2, resource="vendor-7",
            tool="payment", action="create-payment", decision="allow",
            reason_code="approved", occurred_at_epoch=1_800_000_001,
        )
        second = chain.append(second_input)
        self.assertEqual(second.previous_receipt_hash, first.receipt_digest)
        self.assertTrue(chain.verify())

    def test_execution_receipt_chain_rejects_sequence_gap(self):
        chain = ExecutionEvidenceChain()
        with self.assertRaises(ValueError):
            chain.append(replace(self.receipt, sequence=2))

    def test_execution_receipt_chain_detects_receipt_tampering(self):
        chain = ExecutionEvidenceChain()
        chain.append(self.receipt)
        chain._receipts[0] = replace(chain._receipts[0], decision="allow")
        self.assertFalse(chain.verify())

    def test_claim_requires_valid_policy_digest(self):
        invalid = AgentEvidenceClaim(
            evidence_service="evidence",
            policy_pack_digest="not-a-digest",
            logical_agent_id="agent-1",
        )
        with self.assertRaises(ValueError):
            build_execution_receipt(
                claim=invalid, request=self.request, request_id="r",
                runtime_agent_id="runtime", sequence=1, resource="r",
                tool="read", action="read", decision="allow",
                reason_code="ok", occurred_at_epoch=10,
            )

    def test_output_digest_is_bound_when_output_is_supplied(self):
        with_output = build_execution_receipt(
            claim=self.claim, request=self.request, request_id="req-002",
            runtime_agent_id="runtime-1", sequence=2, resource="r",
            tool="write", action="write", decision="allow",
            reason_code="authorized", occurred_at_epoch=20,
            output=b"created-artifact",
        )
        self.assertIsNotNone(with_output.output_digest)
        self.assertNotEqual(with_output.output_digest, self.receipt.output_digest)


if __name__ == "__main__":
    unittest.main()
