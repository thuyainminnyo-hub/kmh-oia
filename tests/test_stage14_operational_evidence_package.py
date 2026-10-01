import unittest

from src.operational_evidence_package import OperationalEvidencePackageBuilder


class OperationalEvidencePackageBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = OperationalEvidencePackageBuilder()
        self.evidence = {
            key: f"{key}-evidence" for key in self.builder.REQUIRED_EVIDENCE
        }

    def test_builds_complete_package_from_explicit_evidence(self) -> None:
        package = self.builder.build(deployment_id="deploy-14", evidence=self.evidence)
        self.assertTrue(package.complete)
        self.assertEqual(package.missing, ())
        self.assertEqual(len(package.items), len(self.builder.REQUIRED_EVIDENCE))
        self.builder.require_complete(package)

    def test_missing_evidence_blocks_completion(self) -> None:
        evidence = dict(self.evidence)
        del evidence["telemetry"]
        package = self.builder.build(deployment_id="deploy-14", evidence=evidence)
        self.assertFalse(package.complete)
        self.assertIn("telemetry", package.missing)
        with self.assertRaises(RuntimeError):
            self.builder.require_complete(package)

    def test_empty_evidence_is_incomplete(self) -> None:
        package = self.builder.build(deployment_id="deploy-14", evidence={})
        self.assertFalse(package.complete)
        self.assertEqual(set(package.missing), set(self.builder.REQUIRED_EVIDENCE))

    def test_invalid_inputs_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(deployment_id=" ", evidence=self.evidence)
        with self.assertRaises(ValueError):
            self.builder.build(deployment_id="deploy-14", evidence={"release": 42})


if __name__ == "__main__":
    unittest.main()
