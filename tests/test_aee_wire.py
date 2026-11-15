import hashlib
import unittest

from src.aee_wire import (
    AeeWireError,
    ZERO_HASH,
    deterministic_cbor_encode,
    execution_receipt_record_hash,
    strict_deterministic_cbor_decode,
    verify_execution_receipt_chain,
)


class StrictCborTests(unittest.TestCase):
    def test_round_trips_supported_values(self):
        value = {1: 5, 2: 0, 3: ZERO_HASH, 4: 1, 6: 1, 7: "agent"}
        encoded = deterministic_cbor_encode(value)
        self.assertEqual(strict_deterministic_cbor_decode(encoded), value)

    def test_deterministic_map_order_is_length_then_lexicographic(self):
        value = {1000: "long", 1: "short", 24: "middle"}
        encoded = deterministic_cbor_encode(value)
        self.assertEqual(strict_deterministic_cbor_decode(encoded), value)
        self.assertEqual(encoded, bytes.fromhex("a3016573686f72741818666d6964646c651903e8646c6f6e67"))

    def test_rejects_duplicate_map_keys_before_dict_collapse(self):
        with self.assertRaisesRegex(AeeWireError, "duplicate"):
            strict_deterministic_cbor_decode(bytes.fromhex("a201010102"))

    def test_rejects_non_deterministic_key_order(self):
        with self.assertRaises(AeeWireError):
            strict_deterministic_cbor_decode(bytes.fromhex("a202000100"))

    def test_rejects_non_minimal_integer(self):
        with self.assertRaisesRegex(AeeWireError, "non-minimal"):
            strict_deterministic_cbor_decode(bytes.fromhex("1817"))

    def test_rejects_indefinite_length(self):
        with self.assertRaisesRegex(AeeWireError, "indefinite"):
            strict_deterministic_cbor_decode(bytes.fromhex("9f01ff"))

    def test_rejects_invalid_utf8(self):
        with self.assertRaisesRegex(AeeWireError, "UTF-8"):
            strict_deterministic_cbor_decode(bytes.fromhex("61ff"))

    def test_rejects_float_and_tag_in_this_profile_subset(self):
        with self.assertRaises(AeeWireError):
            strict_deterministic_cbor_decode(bytes.fromhex("f93c00"))
        with self.assertRaises(AeeWireError):
            strict_deterministic_cbor_decode(bytes.fromhex("c001"))

    def test_rejects_trailing_bytes(self):
        with self.assertRaisesRegex(AeeWireError, "trailing"):
            strict_deterministic_cbor_decode(bytes.fromhex("0102"))


class AeeReceiptHashTests(unittest.TestCase):
    def receipt(self, seq, prev_hash):
        return {1: 5, 2: seq, 3: prev_hash, 4: 1, 6: 1, 7: b"p" * 32}

    def test_hash_is_computed_from_canonical_receipt_payload(self):
        receipt = self.receipt(0, ZERO_HASH)
        expected = hashlib.sha256(deterministic_cbor_encode(receipt)).digest()
        self.assertEqual(execution_receipt_record_hash(receipt), expected)

    def test_chain_recomputes_links_and_sequence(self):
        first = self.receipt(0, ZERO_HASH)
        first_hash = execution_receipt_record_hash(first)
        second = self.receipt(1, first_hash)
        hashes = verify_execution_receipt_chain([first, second])
        self.assertEqual(hashes, (first_hash, execution_receipt_record_hash(second)))

    def test_rejects_tampered_predecessor_hash(self):
        with self.assertRaisesRegex(AeeWireError, "prev_hash"):
            verify_execution_receipt_chain([
                self.receipt(0, ZERO_HASH),
                self.receipt(1, b"x" * 32),
            ])

    def test_rejects_sequence_gap(self):
        with self.assertRaisesRegex(AeeWireError, "seq"):
            verify_execution_receipt_chain([self.receipt(1, ZERO_HASH)])

    def test_rejects_wrong_statement_type_and_bad_digest(self):
        bad_type = self.receipt(0, ZERO_HASH)
        bad_type[1] = 6
        with self.assertRaises(AeeWireError):
            execution_receipt_record_hash(bad_type)
        bad_hash = self.receipt(0, b"short")
        with self.assertRaises(AeeWireError):
            execution_receipt_record_hash(bad_hash)


if __name__ == "__main__":
    unittest.main()
