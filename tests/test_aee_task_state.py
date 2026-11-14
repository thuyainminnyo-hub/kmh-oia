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
        values = {
            "seq": seq,
            "prev_hash": prev,
            "record_hash": bytes([seq + 1]) * 32,
            "record_type": record_type,
            "decision": decision,
            "policy_pack_digest": self.policy,
            "config_integrity_digest": self.config,
            "agent_id": "spiffe://example.test/agent/runtime-1",
            "principal": self.principal,
            "task_seq": task_seq,
            "ts": 1_790_000_000_000 + seq,
        }
        values.update(kwargs)
        return AeeExecutionReceipt(**values)

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


    def test_accepts_interleaved_open_tasks(self):
        records = self.chain([
            (0, "task_start", "allow", 0, {}),
            (1, "task_start", "allow", 1, {}),
            (2, "inference", "allow", 0, {}),
            (3, "inference", "allow", 1, {}),
            (4, "task_end", "allow", 0, {}),
            (5, "task_end", "allow", 1, {}),
        ])
        result = validate_aee_receipt_sequence(records)
        self.assertEqual(result.task_count, 2)

    def test_rejects_decreasing_timestamp_across_chain(self):
        first = self.make(0, b"\x00" * 32, "task_start", "allow", 0)
        second = self.make(
            1, first.record_hash, "inference", "allow", 0,
            ts=first.ts - 1,
        )
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence([first, second])

    def test_rejects_boolean_timestamp(self):
        first = self.make(
            0, b"\x00" * 32, "task_start", "allow", 0, ts=True,
        )
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence([first])


    def test_accepts_aee_02_appendix_a_execution_receipt_semantics(self):
        # Values below are transcribed from the published AEE -02 Appendix A
        # execution-receipt examples. This validates semantics and supplied
        # chain linkage only; it does NOT recompute canonical CBOR hashes or
        # verify the embedded COSE agent signature.
        policy = bytes.fromhex(
            "563a0a3a0c09b773b7f07dd66931dc56605cb0e56d53d1da9cdefe6ae4c56f4d"
        )
        config = bytes.fromhex(
            "654e7b4e605a07c8657d5f2c01360d2367022d18a2ee2dfce1a6489e1c6b6781"
        )
        principal = (
            "natural-person:sha256:"
            "355acb442721073848a4b78577b31cd2958587696cf8378ab050011c8a042638"
        )
        request = bytes.fromhex(
            "989a658a232f0329b3372261bdd4d3bec9e31d57094015433bf54fbd2aeca8f5"
        )
        hashes = [
            "1942de9ac9bd019506aa5e551ede9ae92676942d4278816ab458a9deb16548c0",
            "3d3b1f63cb07c710049eed093e439600464a47a36b37175372e1fc734f6d39a9",
            "7df8cc808530b8a02e78f723ddcda32645e14c66dd61b8525279fa94118f9ec9",
            "6724c98d2b78fe984db24ce2d8cb63cc214171928ec4f9ebb09770e3d9196fa7",
        ]
        hashes = [bytes.fromhex(value) for value in hashes]
        zero = b"\x00" * 32
        base = {
            "policy_pack_digest": policy,
            "config_integrity_digest": config,
            "agent_id": "wimse://agents.example.com/agent/billing-assistant",
            "principal": principal,
        }
        records = [
            AeeExecutionReceipt(
                seq=0, prev_hash=zero, record_hash=hashes[0],
                record_type="task_start", decision="allow",
                task_seq=0, ts=1_790_001_000_000, **base,
            ),
            AeeExecutionReceipt(
                seq=1, prev_hash=hashes[0], record_hash=hashes[1],
                record_type="inference", decision="allow",
                task_seq=0, ts=1_790_001_000_120,
                decision_point="model", request_digest=bytes.fromhex(
                    "b1d21340b999c928ffd214aa36db4be63eedce244aa382e47e4d579ed576bc40"
                ),
                response_digest=bytes.fromhex(
                    "022531c9882a5426d13f9af059c17d2f60d0df585b3fe3ae0f016a8a5f5562ca"
                ),
                target="example-model-2026-06", **base,
            ),
            AeeExecutionReceipt(
                seq=2, prev_hash=hashes[1], record_hash=hashes[2],
                record_type="tool_call", decision="confirm",
                task_seq=0, ts=1_790_001_000_350,
                parent_seq=1, decision_point="tool",
                target="send_invoice", request_digest=request,
                egress_host="api.customer.example", **base,
            ),
            AeeExecutionReceipt(
                seq=3, prev_hash=hashes[2], record_hash=hashes[3],
                record_type="tool_call", decision="allow",
                task_seq=0, ts=1_790_001_009_000,
                parent_seq=1, decision_point="tool",
                target="send_invoice", request_digest=request,
                egress_host="api.customer.example", confirm_seq=2, **base,
            ),
        ]
        result = validate_aee_receipt_sequence(records)
        self.assertEqual(result.receipt_count, 4)
        self.assertEqual(result.task_count, 1)
        self.assertEqual(result.confirmed_call_count, 1)
        self.assertEqual(result.final_record_hash, hashes[3])

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


    def test_rejects_nonzero_genesis_hash(self):
        first = self.make(
            0, b"x" * 32, "task_start", "allow", 0,
        )
        with self.assertRaises(AeeTaskValidationError):
            validate_aee_receipt_sequence([first])

if __name__ == "__main__":
    unittest.main()
