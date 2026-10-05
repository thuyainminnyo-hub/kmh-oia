import unittest

from src.active_standard_resolver import ActiveStandardResolver
from src.runtime_standard_auto_authorizer import RuntimeStandardAutoAuthorizer
from src.standardization_engine import OperatingStandard


class RuntimeStandardAutoAuthorizerTests(unittest.TestCase):
    def test_selects_active_version_and_authorizes(self):
        resolver = ActiveStandardResolver()
        resolver.register(OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE"))
        resolver.register(OperatingStandard("std:a:v2", "a", "Old rule", "Old", 2, "RETIRED"))
        result = RuntimeStandardAutoAuthorizer(resolver).authorize(
            "a", "cmd:1", applied_rule="Require evidence"
        )
        self.assertEqual(result.standard_id, "std:a:v1")
        self.assertTrue(result.check.allowed)

    def test_missing_active_version_blocks_authorization(self):
        resolver = ActiveStandardResolver()
        with self.assertRaises(LookupError):
            RuntimeStandardAutoAuthorizer(resolver).authorize(
                "missing", "cmd:2", applied_rule="Anything"
            )

    def test_wrong_rule_is_rejected_after_auto_selection(self):
        resolver = ActiveStandardResolver()
        resolver.register(OperatingStandard("std:a:v1", "a", "Require evidence", "Quality", 1, "ACTIVE"))
        with self.assertRaises(PermissionError):
            RuntimeStandardAutoAuthorizer(resolver).authorize(
                "a", "cmd:3", applied_rule="Skip evidence"
            )


if __name__ == "__main__":
    unittest.main()
