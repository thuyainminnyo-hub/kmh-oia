"""AEE -02 Appendix A.4 reference-vector regression tests.

Vectors are transcribed from the draft's published diagnostic notation.
The COSE_Sign1 value in receipt key 15 is carried as the encoded byte string
specified by the draft; cryptographic COSE verification is outside this file.
"""
import unittest

from src.aee_wire import (
    ZERO_HASH,
    execution_receipt_record_hash,
    verify_execution_receipt_chain,
)


AGENT = "wimse://agents.example.com/agent/billing-assistant"
PACK = bytes.fromhex("563a0a3a0c09b773b7f07dd66931dc56605cb0e56d53d1da9cdefe6ae4c56f4d")
CONFIG = bytes.fromhex("654e7b4e605a07c8657d5f2c01360d2367022d18a2ee2dfce1a6489e1c6b6781")
PRINCIPAL = bytes.fromhex("355acb442721073848a4b78577b31cd2958587696cf8378ab050011c8a042638")
PROMPT = bytes.fromhex("b1d21340b999c928ffd214aa36db4be63eedce244aa382e47e4d579ed576bc40")
COMPLETION = bytes.fromhex("022531c9882a5426d13f9af059c17d2f60d0df585b3fe3ae0f016a8a5f5562ca")
TOOL_INPUT = bytes.fromhex("989a658a232f0329b3372261bdd4d3bec9e31d57094015433bf54fbd2aeca8f5")
CALL_DIGEST = bytes.fromhex("544d017602d3f2c25b263dc8b8a7c124a27f447f9820363ba99793d5baeda60f")
AGENT_SIG_COSE = bytes.fromhex(
    "d284589aa4012703781e6170706c69636174696f6e2f6165652d73746174656d656e742b63626f72"
    "04481325b850c28719160fa201783277696d73653a2f2f6167656e74732e6578616d706c652e636f"
    "6d2f6167656e742f62696c6c696e672d617373697374616e7402783277696d73653a2f2f6167656e"
    "74732e6578616d706c652e636f6d2f6167656e742f62696c6c696e672d617373697374616e74a0f6"
    "58409bac10cd49f8fcaba3f43a2b1a201dcc96e88e2813290c9a9067a67010c8ba99d1475d48145"
    "85530b4c8ba1ec47db757be4fb12a99dcd752e934f49e6a0bd902"
)


def receipts():
    r0 = {
        1: 5, 2: 0, 3: ZERO_HASH, 4: 1, 6: 1,
        7: [-16, PACK], 8: [-16, CONFIG], 9: AGENT,
        10: {1: 1, 2: PRINCIPAL}, 11: 0,
        14: 1790001000000,
    }
    h0 = bytes.fromhex("1942de9ac9bd019506aa5e551ede9ae92676942d4278816ab458a9deb16548c0")
    r1 = {
        1: 5, 2: 1, 3: h0, 4: 3, 6: 1,
        7: [-16, PACK], 8: [-16, CONFIG], 9: AGENT,
        10: {1: 1, 2: PRINCIPAL}, 11: 0,
        14: 1790001000120, 18: 1, 16: "example-model-2026-06",
        12: [-16, PROMPT], 13: [-16, COMPLETION],
    }
    h1 = bytes.fromhex("3d3b1f63cb07c710049eed093e439600464a47a36b37175372e1fc734f6d39a9")
    r2 = {
        1: 5, 2: 2, 3: h1, 4: 4, 6: 3,
        7: [-16, PACK], 8: [-16, CONFIG], 9: AGENT,
        10: {1: 1, 2: PRINCIPAL}, 11: 0,
        14: 1790001000350, 5: 1, 18: 2, 16: "send_invoice",
        12: [-16, TOOL_INPUT], 17: "api.customer.example",
        15: AGENT_SIG_COSE,
    }
    h2 = bytes.fromhex("7df8cc808530b8a02e78f723ddcda32645e14c66dd61b8525279fa94118f9ec9")
    r3 = {
        1: 5, 2: 3, 3: h2, 4: 4, 6: 1,
        7: [-16, PACK], 8: [-16, CONFIG], 9: AGENT,
        10: {1: 1, 2: PRINCIPAL}, 11: 0,
        14: 1790001009000, 5: 1, 18: 2, 16: "send_invoice",
        12: [-16, TOOL_INPUT], 17: "api.customer.example",
        19: 2, 23: [AGENT],
        24: bytes.fromhex("1c8ec66d31e2260b8ebe9e7c602773d0b7b8803689e8a935c3d7d22002cd813d"),
        25: "txn-0001", 29: CALL_DIGEST,
    }
    expected = (
        h0,
        h1,
        h2,
        bytes.fromhex("6724c98d2b78fe984db24ce2d8cb63cc214171928ec4f9ebb09770e3d9196fa7"),
    )
    return [r0, r1, r2, r3], expected


class AeeAppendixAReferenceVectorTests(unittest.TestCase):
    def test_all_four_reference_record_hashes_match(self):
        records, expected = receipts()
        actual = tuple(execution_receipt_record_hash(record) for record in records)
        self.assertEqual(actual, expected)

    def test_reference_chain_links_match_all_four_records(self):
        records, expected = receipts()
        self.assertEqual(verify_execution_receipt_chain(records), expected)

    def test_key_15_is_included_in_record_hash(self):
        records, expected = receipts()
        signed = records[2]
        without_agent_sig = dict(signed)
        del without_agent_sig[15]
        self.assertEqual(execution_receipt_record_hash(signed), expected[2])
        self.assertNotEqual(
            execution_receipt_record_hash(without_agent_sig), expected[2]
        )


if __name__ == "__main__":
    unittest.main()
