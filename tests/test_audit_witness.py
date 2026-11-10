import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.preservation_ingest import IntakeError
from scripts.audit_witness import (
    IndependentAuditWitness,
    create_signed_checkpoint,
    verify_witness_receipt,
)


class IndependentAuditWitnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "witness.sqlite3"
        self.log_key = Ed25519PrivateKey.generate()
        self.witness_key = Ed25519PrivateKey.generate()
        self.witness = IndependentAuditWitness(
            self.db, witness_id="kmh-independent-witness-01",
            witness_private_key=self.witness_key,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def checkpoint(self, size, root, timestamp):
        return create_signed_checkpoint(
            log_id="kmh-music-audit-log",
            tree_size=size,
            root_hash=root,
            timestamp=timestamp,
            log_signing_key_id="music-log-key-01",
            log_private_key=self.log_key,
        )

    def test_signed_checkpoint_is_pinned_and_receipt_verifies_after_reopen(self):
        root = "11" * 32
        checkpoint = self.checkpoint(1, root, "2026-11-10T00:00:00+00:00")
        accepted = self.witness.accept_checkpoint(
            checkpoint, log_public_key=self.log_key.public_key(),
        )
        verify_witness_receipt(
            accepted["witness_receipt"], self.witness_key.public_key(),
        )
        reopened = IndependentAuditWitness(
            self.db, witness_id="kmh-independent-witness-01",
            witness_private_key=self.witness_key,
        )
        self.assertEqual(reopened.latest("kmh-music-audit-log")["checkpoint"], checkpoint)

    def test_checkpoint_signature_tampering_is_rejected(self):
        checkpoint = self.checkpoint(1, "22" * 32, "2026-11-10T00:00:00+00:00")
        checkpoint["root_hash"] = "33" * 32
        with self.assertRaises(IntakeError):
            self.witness.accept_checkpoint(
                checkpoint, log_public_key=self.log_key.public_key(),
            )

    def test_rollback_and_same_size_equivocation_are_rejected(self):
        first = self.checkpoint(5, "44" * 32, "2026-11-10T00:00:00+00:00")
        self.witness.accept_checkpoint(first, log_public_key=self.log_key.public_key())
        older = self.checkpoint(4, "55" * 32, "2026-11-10T00:01:00+00:00")
        with self.assertRaises(IntakeError):
            self.witness.accept_checkpoint(older, log_public_key=self.log_key.public_key())
        equivocation = self.checkpoint(5, "66" * 32, "2026-11-10T00:02:00+00:00")
        with self.assertRaises(IntakeError):
            self.witness.accept_checkpoint(equivocation, log_public_key=self.log_key.public_key())

    def test_tree_growth_requires_consistency_proof_and_verifier(self):
        first = self.checkpoint(2, "77" * 32, "2026-11-10T00:00:00+00:00")
        self.witness.accept_checkpoint(first, log_public_key=self.log_key.public_key())
        second = self.checkpoint(4, "88" * 32, "2026-11-10T00:01:00+00:00")
        with self.assertRaises(IntakeError):
            self.witness.accept_checkpoint(second, log_public_key=self.log_key.public_key())
        with self.assertRaises(IntakeError):
            self.witness.accept_checkpoint(
                second, log_public_key=self.log_key.public_key(),
                consistency_proof=["proof-node"],
                consistency_verifier=lambda old, new, proof: False,
            )
        accepted = self.witness.accept_checkpoint(
            second, log_public_key=self.log_key.public_key(),
            consistency_proof=["proof-node"],
            consistency_verifier=lambda old, new, proof: (
                old["tree_size"] == 2 and new["tree_size"] == 4 and proof == ["proof-node"]
            ),
        )
        self.assertEqual(accepted["checkpoint"]["tree_size"], 4)

    def test_witness_rows_are_append_only(self):
        checkpoint = self.checkpoint(1, "99" * 32, "2026-11-10T00:00:00+00:00")
        self.witness.accept_checkpoint(checkpoint, log_public_key=self.log_key.public_key())
        connection = sqlite3.connect(self.db)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE witnessed_checkpoints SET root_hash=? WHERE sequence=1", ("aa" * 32,))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM witnessed_checkpoints WHERE sequence=1")
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
