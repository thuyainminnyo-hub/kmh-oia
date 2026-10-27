import tempfile
import unittest
from pathlib import Path

from src.trusted_learning_service_factory import (
    TrustedLearningServiceConfig,
    build_trusted_learning_service,
)


class FakeVerifier:
    def verify(self, *args, **kwargs):
        raise AssertionError("factory tests must not verify a receipt")


class FakeClassifier:
    def classify(self, *args, **kwargs):
        raise AssertionError("factory tests must not classify an outcome")


class TrustedLearningServiceFactoryTests(unittest.TestCase):
    def test_builds_service_with_explicit_file_backed_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = build_trusted_learning_service(
                config=TrustedLearningServiceConfig(
                    memory_path=str(root / "memory.json"),
                    proposal_sqlite_path=str(root / "proposals.sqlite3"),
                ),
                receipt_verifier=FakeVerifier(),
                classifier=FakeClassifier(),
            )
            self.assertIsNotNone(service)
            self.assertTrue((root / "proposals.sqlite3").exists())
            self.assertFalse((root / "memory.json").exists())

    def test_rejects_missing_verifier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "receipt verifier"):
                build_trusted_learning_service(
                    config=TrustedLearningServiceConfig(
                        memory_path=str(root / "memory.json"),
                        proposal_sqlite_path=str(root / "proposals.sqlite3"),
                    ),
                    receipt_verifier=None,
                    classifier=FakeClassifier(),
                )

    def test_rejects_missing_classifier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "classifier"):
                build_trusted_learning_service(
                    config=TrustedLearningServiceConfig(
                        memory_path=str(root / "memory.json"),
                        proposal_sqlite_path=str(root / "proposals.sqlite3"),
                    ),
                    receipt_verifier=FakeVerifier(),
                    classifier=None,
                )

    def test_rejects_in_memory_paths(self):
        with self.assertRaisesRegex(ValueError, "regular persistent file path"):
            TrustedLearningServiceConfig(
                memory_path=":memory:",
                proposal_sqlite_path="/tmp/kmh-proposals.sqlite3",
            ).validate()

    def test_rejects_same_path_for_both_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            shared = str(Path(directory) / "shared.db")
            with self.assertRaisesRegex(ValueError, "different files"):
                TrustedLearningServiceConfig(
                    memory_path=shared,
                    proposal_sqlite_path=shared,
                ).validate()

    def test_rejects_tilde_and_absolute_alias_of_same_file(self):
        shared_name = "kmh-oia-factory-path-collision-test.sqlite3"
        tilde_path = str(Path("~") / shared_name)
        absolute_path = str(Path.home() / shared_name)
        with self.assertRaisesRegex(ValueError, "different files"):
            TrustedLearningServiceConfig(
                memory_path=tilde_path,
                proposal_sqlite_path=absolute_path,
            ).validate()


if __name__ == "__main__":
    unittest.main()
