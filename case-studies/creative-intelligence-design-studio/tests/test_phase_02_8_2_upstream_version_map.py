import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_MAP = ROOT / "contracts" / "phase-02-8.2-upstream-version-map.json"


class Phase0282UpstreamVersionMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(VERSION_MAP.read_text(encoding="utf-8"))

    def test_python_cross_file_fix_was_introduced_in_0954(self):
        releases = {item["version"]: item for item in self.data["release_history"]}
        fix = releases["0.9.54"]
        self.assertEqual(fix["issue"], "#3252")
        self.assertEqual(
            fix["classification"],
            "INTRODUCED_PYTHON_CROSS_FILE_TYPE_REPOINT",
        )
        self.assertIn("same-named types in different modules", fix["change"])

    def test_0995_alias_extraction_is_a_separate_python_change(self):
        releases = {item["version"]: item for item in self.data["release_history"]}
        aliases = releases["0.9.95"]
        self.assertEqual(aliases["issue"], "#4578")
        self.assertEqual(
            aliases["classification"],
            "PYTHON_EXPLICIT_TYPE_ALIAS_EXTRACTION",
        )
        self.assertNotEqual(
            aliases["classification"],
            releases["0.9.54"]["classification"],
        )

    def test_0100_does_not_claim_to_introduce_the_python_3252_fix(self):
        releases = {item["version"]: item for item in self.data["release_history"]}
        latest = releases["0.9.100"]
        self.assertEqual(latest["release_commit"], self.data["pinned_commit"])
        self.assertEqual(
            latest["classification"],
            "LATER_ID_NORMALIZATION_AND_JVM_RESOLUTION_UPDATES",
        )
        self.assertIn("not where that fix was first introduced", latest["change"])

    def test_fix_commit_is_recorded_as_ancestor_of_first_and_pinned_releases(self):
        verification = self.data["verification"]
        self.assertTrue(verification["python_fix_commit_ancestor_of_v0_9_54_release"])
        self.assertTrue(verification["python_fix_commit_ancestor_of_v0_9_100_pinned_commit"])
        self.assertEqual(
            verification["first_release_with_python_cross_file_type_repoint"],
            "0.9.54",
        )
        self.assertEqual(verification["pinned_release_under_test"], "0.9.100")

    def test_unreproduced_issue_and_extraction_limits_remain_explicit(self):
        caveats = " ".join(self.data["caveats"]).lower()
        self.assertIn("issue #1186", caveats)
        self.assertIn("multiple bases", caveats)
        self.assertIn("same-line parameter/return", caveats)
        self.assertIn("not a replacement for executing", caveats)


if __name__ == "__main__":
    unittest.main()
