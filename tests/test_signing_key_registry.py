import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.preservation_ingest import (
    IntakeError,
    build_signing_key_registry_entry,
)
from scripts.signing_key_registry import DurableSigningKeyRegistry


class DurableSigningKeyRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "keys.sqlite3"
        self.registry = DurableSigningKeyRegistry(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def make_entry(self, key_id, *, created="2026-11-10T00:00:00+00:00",
                   activate="2026-11-10T00:01:00+00:00"):
        return build_signing_key_registry_entry(
            key_id, Ed25519PrivateKey.generate().public_key(),
            created_at=created, activate_at=activate,
        )

    def activate(self, key_id):
        return self.registry.transition(
            key_id, target_state="active",
            at="2026-11-10T00:01:00+00:00", reason="initial activation",
        )

    def test_registration_persists_across_registry_instances_and_audit_verifies(self):
        entry = self.make_entry("durable-key-01")
        self.registry.register(entry)
        reopened = DurableSigningKeyRegistry(self.db)
        self.assertEqual(reopened.get_entry("durable-key-01")["state"], "pre_active")
        self.assertTrue(reopened.verify_audit_chain())
        self.assertEqual(len(reopened.audit_events()), 1)

    def test_rotation_is_atomic_and_persists_replacement_and_retirement(self):
        self.registry.register(self.make_entry("durable-key-02"))
        self.activate("durable-key-02")
        replacement = self.make_entry(
            "durable-key-03", created="2026-11-10T01:00:00+00:00",
            activate="2026-11-10T01:01:00+00:00",
        )
        self.registry.rotate(
            "durable-key-02", replacement,
            at="2026-11-10T01:01:00+00:00", reason="scheduled rotation",
        )
        self.assertEqual(self.registry.get_entry("durable-key-02")["state"], "retired")
        self.assertEqual(self.registry.get_entry("durable-key-03")["state"], "active")
        self.assertEqual(self.registry.get_entry("durable-key-02")["replacement_key_id"], "durable-key-03")
        self.assertTrue(self.registry.verify_audit_chain())

    def test_failed_rotation_rolls_back_new_key_and_audit_events(self):
        self.registry.register(self.make_entry("durable-key-04"))
        self.activate("durable-key-04")
        before = len(self.registry.audit_events())
        replacement = self.make_entry(
            "durable-key-05", created="2026-11-10T01:00:00+00:00",
            activate="2026-11-10T02:00:00+00:00",
        )
        with self.assertRaises(IntakeError):
            self.registry.rotate(
                "durable-key-04", replacement,
                at="2026-11-10T01:30:00+00:00", reason="test early activation",
            )
        with self.assertRaises(IntakeError):
            self.registry.get_entry("durable-key-05")
        self.assertEqual(self.registry.get_entry("durable-key-04")["state"], "active")
        self.assertEqual(len(self.registry.audit_events()), before)
        self.assertTrue(self.registry.verify_audit_chain())

    def test_audit_events_are_append_only_and_hash_chain_detects_tampering(self):
        self.registry.register(self.make_entry("durable-key-06"))
        connection = sqlite3.connect(self.db)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE key_audit_events SET event_json='{}' WHERE sequence=1")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM key_audit_events WHERE sequence=1")
        finally:
            connection.close()
        self.assertTrue(self.registry.verify_audit_chain())

    def test_compromise_is_durable_and_blocks_execution_key_listing(self):
        self.registry.register(self.make_entry("durable-key-07"))
        self.activate("durable-key-07")
        self.assertIn("durable-key-07", self.registry.public_keys_for_execution(at="2026-11-10T00:02:00+00:00"))
        self.registry.compromise(
            "durable-key-07", at="2026-11-10T00:03:00+00:00",
            reason="suspected private key exposure",
        )
        self.assertNotIn("durable-key-07", self.registry.public_keys_for_execution(at="2026-11-10T00:04:00+00:00"))
        self.assertEqual(self.registry.get_entry("durable-key-07")["state"], "compromised")
        self.assertTrue(self.registry.verify_audit_chain())


if __name__ == "__main__":
    unittest.main()
