"""Tests for the P15.9 evidence receipt manifest."""

import unittest

from src.p15_9_evidence_receipt import (
    EvidenceReceipt,
    EvidenceReceiptManifestBuilder,
)


DIGEST = "a" * 64


def receipt(category: str, artifact_id: str = "artifact-1", release_id: str = "release-15-9"):
    return EvidenceReceipt(
        category=category,
        release_id=release_id,
        artifact_id=artifact_id,
        observed_at="2026-10-02T00:00:00Z",
        source=f"operator://{artifact_id}",
        sha256=DIGEST,
    )


class EvidenceReceiptManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = EvidenceReceiptManifestBuilder()

    def test_complete_receipts_have_no_missing_categories(self) -> None:
        manifest = self.builder.build(
            release_id="release-15-9",
            receipts=tuple(
                receipt(category, f"artifact-{index}")
                for index, category in enumerate(
                    self.builder.REQUIRED_CATEGORIES,
                    start=1,
                )
            ),
        )

        self.assertEqual(self.builder.missing_categories(manifest), ())

    def test_release_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(
                release_id="release-15-9",
                receipts=(receipt("telemetry", release_id="different-release"),),
            )

    def test_duplicate_artifact_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(
                release_id="release-15-9",
                receipts=(receipt("telemetry"), receipt("performance")),
            )

    def test_invalid_digest_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceReceipt(
                category="telemetry",
                release_id="release-15-9",
                artifact_id="artifact-1",
                observed_at="2026-10-02T00:00:00Z",
                source="operator://artifact-1",
                sha256="not-a-sha256",
            )

    def test_missing_categories_are_reported(self) -> None:
        manifest = self.builder.build(
            release_id="release-15-9",
            receipts=(receipt("telemetry"),),
        )

        self.assertEqual(
            self.builder.missing_categories(manifest),
            ("performance", "rollback_drill", "authorization", "incident_exercise"),
        )


if __name__ == "__main__":
    unittest.main()
