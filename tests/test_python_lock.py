import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_python_lock import EXPECTED, REQ, audit, parse_lock


HASH = "a" * 64


def make_lock():
    return "".join(
        f"{name}=={version} \\\n    --hash=sha256:{HASH}\n"
        for name, version in EXPECTED.items()
    )


class PythonLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "requirements-ci.lock").write_text(make_lock(), encoding="utf-8")
        (self.root / "requirements.txt").write_text(
            "jsonschema==4.26.0\nPyYAML==6.0.3\n", encoding="utf-8"
        )
        for workflow in (
            ".github/workflows/test.yml",
            ".github/workflows/validation.yml",
            ".github/workflows/prompt-library-schema-qa.yml",
            ".github/workflows/action-dependency-assurance.yml",
            ".github/workflows/reusable-workflow-sha-audit.yml",
        ):
            path = self.root / workflow
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "run: python -m pip install --require-hashes --only-binary=:all: -r requirements-ci.lock\n",
                encoding="utf-8",
            )

    def tearDown(self):
        self.temp.cleanup()

    def test_reviewed_lock_and_all_ci_consumers_pass(self):
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["expected_package_count"], 7)

    def test_missing_hash_holds(self):
        path = self.root / "requirements-ci.lock"
        path.write_text(path.read_text().replace(f"--hash=sha256:{HASH}", ""), encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("unhashed" in error for error in result["errors"]))

    def test_unlocked_workflow_consumer_holds(self):
        path = self.root / ".github/workflows/test.yml"
        path.write_text("run: python -m pip install -r requirements.txt\n", encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("unlocked requirements install" in error for error in result["errors"]))

    def test_direct_pin_drift_holds(self):
        path = self.root / "requirements.txt"
        path.write_text("jsonschema==4.25.0\nPyYAML==6.0.3\n", encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("not represented" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
