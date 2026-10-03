"""Tests for the P15.9 evidence receipt manifest."""

import unittest

from src.p15_9_evidence_receipt import (
    EvidenceReceipt,
    EvidenceReceiptManifest,
    EvidenceReceiptManifestBuilder,
)


DIGEST = "a" * 64


def receipt(category: str, artifact_id: str = "artifact-1", release_id: str = "release-15-9", observed_at: str = "2026-10-02T00:00:00Z"):
    return EvidenceReceipt(
        category=category,
        release_id=release_id,
        artifact_id=artifact_id,
        observed_at=observed_at,
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
                for index, category in enumerate(self.builder.REQUIRED_CATEGORIES, start=1)
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
                category="telemetry", release_id="release-15-9",
                artifact_id="artifact-1", observed_at="2026-10-02T00:00:00Z",
                source="operator://artifact-1", sha256="not-a-sha256",
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

    def test_unknown_category_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "category"):
            receipt("placeholder")

    def test_malformed_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            receipt("telemetry", observed_at="yesterday")

    def test_timestamp_without_timezone_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            receipt("telemetry", observed_at="2026-10-02T00:00:00")

    def test_direct_manifest_construction_rejects_release_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "release_id"):
            EvidenceReceiptManifest("release-15-9", (receipt("telemetry", release_id="other"),))


if __name__ == "__main__":
    unittest.main()
