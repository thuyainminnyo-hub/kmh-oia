import unittest

from src.aee_task_state import (
    AeeExecutionReceipt,
    AeeTaskValidationError,
    validate_aee_receipt_sequence,
)


class AeeTaskStateTests(unittest.TestCase):
    policy = b"p" * 32
    config = b"c" * 32
    principal = "principal:demo"

    def make(self, seq, prev, record_type, decision, task_seq, **kwargs):
        return AeeExecutionReceipt(
            seq=seq,
            prev_hash=prev,
            record_hash=bytes([seq + 1]) * 32,
            record_type=record_type,
            decision=decision,
            policy_pack_digest=self.policy,
            config_integrity_digest=self.config,
            agent_id="spiffe://example.test/agent/runtime-1",
            principal=self.principal,
            task_seq=task_seq,
            ts=1_790_000_000_000 + seq,
            **kwargs,
        )

    def chain(self, specifications):
        records = []
        previous = b"\x00" * 32
        for seq, record_type, decision, task_seq, fields in specifications:
            receipt = self.make(seq, previous, record_type, decision, task_seq, **fields)
            records.append(receipt)
            previous = receipt.record_hash
        return records

    def test_accepts_task_inference_tool_and_result(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {"decision_point": "model"}),
            (2, "tool_call", "allow", 0, {
                "parent_seq": 1, "target": "lookup", "request_digest": b"r" * 32,
                "decision_point": "tool",
            }),
            (3, "tool_result", "record", 0, {
                "parent_seq": 2, "response_digest": b"o" * 32,
                "decision_point": "tool",
            }),
            (4, "task_end", "allow", 0, {}),
        ])
        result = validate_aee_receipt_sequence(records)
        self.assertEqual(result.receipt_count, 5)
        self.assertEqual(result.task_count, 1)
        self.assertEqual(result.tool_result_count, 1)

    def test_accepts_confirm_then_allow_outcome_then_result(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
            (2, "tool_call", "confirm", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"r" * 32,
            }),
            (3, "tool_call", "allow", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"r" * 32, "confirm_seq": 2,
            }),
            (4, "tool_result", "record", 0, {
                "parent_seq": 3, "response_digest": b"o" * 32,
            }),
            (5, "task_end", "allow", 0, {}),
        ])
        result = validate_aee_receipt_sequence(records)
        self.assertEqual(result.confirmed_call_count, 1)

    def test_rejects_task_end_with_pending_confirmation(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
            (2, "tool_call", "confirm", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"r" * 32,
            }),
            (3, "task_end", "allow", 0, {}),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_rejects_tool_result_before_allow_outcome(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
            (2, "tool_call", "confirm", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"r" * 32,
            }),
            (3, "tool_result", "record", 0, {
                "parent_seq": 2, "response_digest": b"o" * 32,
            }),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_rejects_confirmation_outcome_for_different_request(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
            (2, "tool_call", "confirm", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"r" * 32,
            }),
            (3, "tool_call", "allow", 0, {
                "parent_seq": 1, "target": "transfer",
                "request_digest": b"x" * 32, "confirm_seq": 2,
            }),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_rejects_wrong_parent_type(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "tool_call", "allow", 0, {
                "parent_seq": 0, "target": "lookup",
                "request_digest": b"r" * 32,
            }),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_rejects_principal_change_within_task(self):
        first = self.make(0, b"\x00" * 32, "task_start", "allow", 0)
        second = self.make(
            1, first.record_hash, "inference", "allow", 0,
            principal="principal:other",
        )
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence([first, second])

    def test_accepts_admission_then_task_started_from_admission(self):
        admission = self.make(
            0, b"\x00" * 32, "admission", "allow", 0,
            decision_point="ingress",
        )
        task_start = self.make(
            1, admission.record_hash, "task_start", "allow", 1,
            parent_seq=0,
        )
        result = validate_aee_receipt_sequence([admission, task_start])
        self.assertEqual(result.admission_count, 1)
        self.assertEqual(result.task_count, 1)


    def test_rejects_confirm_decision_outside_tool_call(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "confirm", 0, {}),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_egress_requires_lowercase_a_label_without_port(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
            (2, "egress", "allow", 0, {
                "parent_seq": 1, "egress_host": "Example.com",
            }),
        ])
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence(records)

    def test_rejects_broken_hash_chain(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "inference", "allow", 0, {}),
        ])
        broken = self.make(
            1, b"x" * 32, "inference", "allow", 0,
        )
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence([records[0], broken])


if __name__ == "__main__":
    unittest.main()
