"""Tests for the trusted-key-provider interface and rotation policy."""
import unittest

from src.trusted_key_provider import (
    InMemoryTrustedKeyProvider,
    KeyProviderUnavailable,
    verify_key_provider_configuration,
)


KEY_V1 = b"kmh-oia-test-key-v1-minimum-32-bytes"
KEY_V2 = b"kmh-oia-test-key-v2-minimum-32-bytes"
KEY_V3 = b"kmh-oia-test-key-v3-minimum-32-bytes"


class TrustedKeyProviderTests(unittest.TestCase):
    def test_active_and_accepted_key_are_available(self):
        provider = InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1},
            active_key_id="key-v1",
            accepted_key_ids={"key-v1"},
        )
        material = provider.get_signing_key()
        self.assertEqual(material.key_id, "key-v1")
        self.assertEqual(material.secret, KEY_V1)
        self.assertTrue(verify_key_provider_configuration(provider))

    def test_unaccepted_and_retired_keys_are_not_available(self):
        provider = InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1, "key-v2": KEY_V2},
            active_key_id="key-v2",
            accepted_key_ids={"key-v2"},
        )
        self.assertIsNone(provider.get_verification_key("key-v1"))
        self.assertEqual(provider.get_verification_key("key-v2"), KEY_V2)

    def test_rotation_has_explicit_overlap_then_retirement(self):
        provider = InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1},
            active_key_id="key-v1",
            accepted_key_ids={"key-v1"},
        )
        provider.rotate(
            new_key_id="key-v2",
            new_secret=KEY_V2,
            accepted_key_ids={"key-v1", "key-v2"},
        )
        self.assertEqual(provider.get_signing_key().key_id, "key-v2")
        self.assertEqual(provider.get_verification_key("key-v1"), KEY_V1)
        self.assertEqual(provider.get_verification_key("key-v2"), KEY_V2)

        provider.rotate(
            new_key_id="key-v3",
            new_secret=KEY_V3,
            accepted_key_ids={"key-v3"},
        )
        self.assertEqual(provider.get_signing_key().key_id, "key-v3")
        self.assertIsNone(provider.get_verification_key("key-v1"))
        self.assertIsNone(provider.get_verification_key("key-v2"))
        self.assertTrue(verify_key_provider_configuration(provider))

    def test_failed_rotation_is_atomic(self):
        provider = InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1},
            active_key_id="key-v1",
            accepted_key_ids={"key-v1"},
        )
        with self.assertRaisesRegex(ValueError, "accepted_key_ids"):
            provider.rotate(
                new_key_id="key-v2",
                new_secret=KEY_V2,
                accepted_key_ids={"key-v1"},
            )
        self.assertEqual(provider.get_signing_key().key_id, "key-v1")

    def test_unavailable_active_key_fails_closed(self):
        provider = InMemoryTrustedKeyProvider(
            {"key-v1": KEY_V1},
            active_key_id="key-v1",
            accepted_key_ids={"key-v1"},
        )
        provider._keyring.pop("key-v1")
        with self.assertRaises(KeyProviderUnavailable):
            provider.get_signing_key()
        self.assertFalse(verify_key_provider_configuration(provider))

    def test_invalid_initial_policy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "active signing key"):
            InMemoryTrustedKeyProvider(
                {"key-v1": KEY_V1},
                active_key_id="key-missing",
                accepted_key_ids={"key-v1"},
            )
        with self.assertRaisesRegex(ValueError, "at least 32"):
            InMemoryTrustedKeyProvider(
                {"key-v1": b"short"},
                active_key_id="key-v1",
                accepted_key_ids={"key-v1"},
            )


if __name__ == "__main__":
    unittest.main()
