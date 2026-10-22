"""Tests for canonical tenant identifier syntax validation."""
import unittest

from src.tenant_identity import is_canonical_tenant_id


class CanonicalTenantIdTests(unittest.TestCase):
    def test_accepts_lowercase_uuid4_with_tenant_prefix(self):
        self.assertTrue(
            is_canonical_tenant_id("tn_f47ac10b-58cc-4372-a567-0e02b2c3d479")
        )

    def test_rejects_missing_or_wrong_prefix(self):
        self.assertFalse(is_canonical_tenant_id("f47ac10b-58cc-4372-a567-0e02b2c3d479"))
        self.assertFalse(is_canonical_tenant_id("tenant_f47ac10b-58cc-4372-a567-0e02b2c3d479"))

    def test_rejects_uppercase_uuid(self):
        self.assertFalse(
            is_canonical_tenant_id("tn_F47AC10B-58CC-4372-A567-0E02B2C3D479")
        )

    def test_rejects_non_uuid4_identifier(self):
        # UUID version nibble is 1, not 4.
        self.assertFalse(
            is_canonical_tenant_id("tn_f47ac10b-58cc-1372-a567-0e02b2c3d479")
        )

    def test_rejects_non_rfc4122_variant(self):
        # The variant nibble must be 8, 9, a, or b.
        self.assertFalse(
            is_canonical_tenant_id("tn_f47ac10b-58cc-4372-7567-0e02b2c3d479")
        )

    def test_rejects_malformed_uuid(self):
        self.assertFalse(is_canonical_tenant_id("tn_not-a-uuid"))
        self.assertFalse(is_canonical_tenant_id("tn_f47ac10b58cc4372a5670e02b2c3d479"))
        self.assertFalse(is_canonical_tenant_id("tn_"))

    def test_rejects_non_string_values(self):
        for value in (None, 42, b"tn_f47ac10b-58cc-4372-a567-0e02b2c3d479", [], {}):
            with self.subTest(value=value):
                self.assertFalse(is_canonical_tenant_id(value))


if __name__ == "__main__":
    unittest.main()
