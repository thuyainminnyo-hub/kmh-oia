import hashlib
import unittest

from src.receipt_verification import (
    CcfInclusionReceiptVerifier,
    ReceiptVerificationError,
)


class FakeCodec:
    def __init__(self, receipt, proofs):
        self.receipt = receipt
        self.proofs = proofs

    def decode_receipt(self, receipt_bytes):
        return self.receipt

    def decode_inclusion_proof(self, proof_bytes):
        return self.proofs[proof_bytes]

    def validate_inclusion_proof(self, proof):
        return proof.get("valid", False)

    def compute_inclusion_root(self, proof):
        return proof["root"]


class FakeCoseVerifier:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def __call__(self, receipt_bytes, *, detached_payload, trusted_key_set, expected_service_id):
        self.calls.append((receipt_bytes, detached_payload, trusted_key_set, expected_service_id))
        return self.result


class CcfInclusionReceiptVerifierTests(unittest.TestCase):
    def setUp(self):
        self.statement = b"candidate-signed-statement"
        self.digest = hashlib.sha256(self.statement).digest()
        self.root = b"merkle-root"
        self.proofs = {
            b"proof-1": {"valid": True, "leaf": {"data-hash": self.digest}, "root": self.root},
            b"proof-2": {"valid": True, "leaf": {"data-hash": self.digest}, "root": self.root},
        }
        self.receipt = {
            "payload": None,
            "unprotected_header": {396: {-1: [b"proof-1", b"proof-2"]}},
        }
        self.cose = FakeCoseVerifier()
        self.verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(self.receipt, self.proofs),
            cose_verifier=self.cose,
            trusted_key_set={"kid": "trusted-ts-key"},
            expected_service_id="https://transparency.example",
        )

    def test_verifies_detached_signature_over_computed_root(self):
        result = self.verifier.verify(
            signed_statement=self.statement, receipt_bytes=b"cose-receipt"
        )
        self.assertEqual(result.statement_digest, self.digest)
        self.assertEqual(result.merkle_root, self.root)
        self.assertEqual(result.proof_count, 2)
        self.assertEqual(self.cose.calls[0][1], self.root)
        self.assertEqual(self.cose.calls[0][3], "https://transparency.example")

    def test_rejects_proof_for_different_signed_statement(self):
        bad = {"valid": True, "leaf": {"data-hash": b"x" * 32}, "root": self.root}
        verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(self.receipt, {b"proof-1": bad, b"proof-2": bad}),
            cose_verifier=self.cose, trusted_key_set={"kid": "k"},
            expected_service_id="https://transparency.example",
        )
        with self.assertRaises(ReceiptVerificationError):
            verifier.verify(signed_statement=self.statement, receipt_bytes=b"receipt")

    def test_rejects_proofs_with_different_roots(self):
        inconsistent = dict(self.proofs)
        inconsistent[b"proof-2"] = {
            "valid": True, "leaf": {"data-hash": self.digest}, "root": b"other-root"
        }
        verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(self.receipt, inconsistent),
            cose_verifier=self.cose, trusted_key_set={"kid": "k"},
            expected_service_id="https://transparency.example",
        )
        with self.assertRaises(ReceiptVerificationError):
            verifier.verify(signed_statement=self.statement, receipt_bytes=b"receipt")

    def test_rejects_invalid_cose_signature_or_service_identity(self):
        verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(self.receipt, self.proofs),
            cose_verifier=FakeCoseVerifier(False), trusted_key_set={"kid": "k"},
            expected_service_id="https://untrusted.example",
        )
        with self.assertRaises(ReceiptVerificationError):
            verifier.verify(signed_statement=self.statement, receipt_bytes=b"receipt")

    def test_rejects_embedded_payload_and_missing_proofs(self):
        embedded = {"payload": b"not-detached", "unprotected_header": {396: {-1: [b"proof-1"]}}}
        verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(embedded, self.proofs), cose_verifier=self.cose,
            trusted_key_set={"kid": "k"}, expected_service_id="https://ts.example",
        )
        with self.assertRaises(ReceiptVerificationError):
            verifier.verify(signed_statement=self.statement, receipt_bytes=b"receipt")
        empty = {"payload": None, "unprotected_header": {396: {-1: []}}}
        verifier = CcfInclusionReceiptVerifier(
            codec=FakeCodec(empty, self.proofs), cose_verifier=self.cose,
            trusted_key_set={"kid": "k"}, expected_service_id="https://ts.example",
        )
        with self.assertRaises(ReceiptVerificationError):
            verifier.verify(signed_statement=self.statement, receipt_bytes=b"receipt")

    def test_requires_candidate_statement_and_trusted_key_set(self):
        with self.assertRaises(ReceiptVerificationError):
            self.verifier.verify(signed_statement=b"", receipt_bytes=b"receipt")
        with self.assertRaises(ValueError):
            CcfInclusionReceiptVerifier(
                codec=FakeCodec(self.receipt, self.proofs),
                cose_verifier=self.cose, trusted_key_set=None,
                expected_service_id="https://ts.example",
            )


if __name__ == "__main__":
    unittest.main()
