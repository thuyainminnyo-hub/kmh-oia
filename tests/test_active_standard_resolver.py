import unittest

from src.active_standard_resolver import ActiveStandardResolver
from src.standardization_engine import OperatingStandard


class ActiveStandardResolverTests(unittest.TestCase):
    def test_resolves_active_version(self):
        resolver = ActiveStandardResolver()
        resolver.register(OperatingStandard("std:a:v1", "a", "Rule v1", "Effect", 1, "ACTIVE"))
        resolver.register(OperatingStandard("std:a:v2", "a", "Rule v2", "Effect", 2, "RETIRED"))
        selected = resolver.resolve("a")
        self.assertEqual(selected.standard.id, "std:a:v1")

    def test_missing_active_standard_is_rejected(self):
        resolver = ActiveStandardResolver()
        with self.assertRaises(LookupError):
            resolver.resolve("missing")

    def test_blank_source_is_rejected(self):
        with self.assertRaises(ValueError):
            ActiveStandardResolver().resolve(" ")

    def test_registry_rejects_multiple_active_versions(self):
        resolver = ActiveStandardResolver()
        resolver.register(OperatingStandard("std:a:v1", "a", "Rule v1", "Effect", 1, "ACTIVE"))
        resolver.register(OperatingStandard("std:a:v2", "a", "Rule v2", "Effect", 2, "ACTIVE"))
        with self.assertRaises(ValueError):
            resolver.resolve("a")


if __name__ == "__main__":
    unittest.main()
