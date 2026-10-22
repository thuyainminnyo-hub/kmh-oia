import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.live_operating_console import LiveOperatingConsole
from src.production_evidence_runtime import (
    ProductionEvidenceRuntimeConfig,
    build_production_evidence_runtime,
)
from src.trusted_source_receipt import TrustedSourceReceipt


def make_test_config(sqlite_path, allowed_source_providers=("test-provider",)):
    """Build a fully specified test-only config; never a production trust fixture."""
    return ProductionEvidenceRuntimeConfig(
        sqlite_path=sqlite_path,
        allowed_source_providers=allowed_source_providers,
        runtime_bundle_path="test-only/runtime-bundle.zip",
        runtime_attestation_path="test-only/runtime-attestation.json",
        runtime_source_revision="test-source-revision",
        runtime_build_run_id="test-build-run",
        runtime_artifact_id="test-artifact-id",
        runtime_artifact_name="test-runtime-bundle.zip",
        runtime_artifact_digest="a" * 64,
        runtime_trusted_public_keys={"test-key": b"test-only-public-key"},
        runtime_allowed_issuers=("test-issuer",),
        runtime_allowed_subjects=("test-subject",),
    )


class MinimalAdapter:
    provider_name = "test-provider"

    def fetch_receipt(self, source_record_id, execution_id):
        return None

    def verify_receipt(self, receipt):
        return False

    def match_execution(self, receipt, execution_id):
        return False


class ProductionEvidenceRuntimeFactoryTests(unittest.TestCase):
    def setUp(self):
        self.console = LiveOperatingConsole(date="2026-10-20")
        self.adapter = MinimalAdapter()
        # Factory integration tests exercise configuration wiring, not signature
        # authenticity. Real bundle verification is tested in its own suite.
        self._release_verifier_patch = patch(
            "src.production_evidence_runtime.verify_runtime_bundle_release", autospec=True
        )
        self.release_verifier = self._release_verifier_patch.start()
        self.addCleanup(self._release_verifier_patch.stop)

    def test_builds_runtime_with_explicit_durable_sqlite_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = build_production_evidence_runtime(
                self.console,
                config=make_test_config(
                    sqlite_path=str(Path(tmp) / "evidence-replay.sqlite3"),
                    allowed_source_providers=("test-provider",),
                ),
                trusted_source_adapter=self.adapter,
            )
            self.release_verifier.assert_called_once_with(
                "test-only/runtime-bundle.zip",
                "test-only/runtime-attestation.json",
                expected_source_revision="test-source-revision",
                expected_build_run_id="test-build-run",
                expected_artifact_id="test-artifact-id",
                expected_artifact_name="test-runtime-bundle.zip",
                expected_artifact_digest="a" * 64,
                trusted_public_keys={"test-key": b"test-only-public-key"},
                allowed_issuers=("test-issuer",),
                allowed_subjects=("test-subject",),
            )
            self.assertTrue(bridge.trusted_source_verifier.replay_store.health_check())
            self.assertEqual(
                bridge.trusted_source_verifier.allowed_providers,
                frozenset({"test-provider"}),
            )

    def test_rejects_empty_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            make_test_config("", ("test-provider",)).validate()

    def test_rejects_memory_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            make_test_config(":memory:", ("test-provider",)).validate()


    def test_rejects_uri_in_memory_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            make_test_config("file::memory:?cache=shared", ("test-provider",)).validate()


    def test_rejects_sqlite_uri_even_when_it_looks_file_backed(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            make_test_config("file:/var/lib/kmh-oia/replay.sqlite3?mode=rw", ("test-provider",)).validate()

    def test_requires_provider_allowlist_to_be_explicit_tuple(self):
        with self.assertRaisesRegex(ValueError, "explicit tuple"):
            make_test_config("/tmp/receipts.sqlite3", ["test-provider"]).validate()

    def test_requires_explicit_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "at least one explicit"):
            make_test_config("/tmp/receipts.sqlite3", ()).validate()


    def test_rejects_blank_entry_in_provider_allowlist_instead_of_silently_dropping_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provider names must be non-empty strings"):
                make_test_config(
                    str(Path(tmp) / "replay.sqlite3"),
                    ("test-provider", "   "),
                ).validate()

    def test_rejects_non_string_entry_in_provider_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provider names must be non-empty strings"):
                make_test_config(
                    str(Path(tmp) / "replay.sqlite3"),
                    ("test-provider", 17),
                ).validate()

    def test_rejects_duplicate_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "must be unique"):
            make_test_config(
                "/tmp/receipts.sqlite3", ("test-provider", "test-provider")
            ).validate()

    def test_rejects_missing_provider_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "adapter is required"):
                build_production_evidence_runtime(
                    self.console,
                    config=make_test_config(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=None,
                )


    def test_provider_name_with_surrounding_whitespace_matches_normalized_allowlist(self):
        adapter = MinimalAdapter()
        adapter.provider_name = " test-provider "
        with tempfile.TemporaryDirectory() as tmp:
            bridge = build_production_evidence_runtime(
                self.console,
                config=make_test_config(
                    str(Path(tmp) / "evidence-replay.sqlite3"),
                    ("test-provider",),
                ),
                trusted_source_adapter=adapter,
            )
            self.assertEqual(
                bridge.trusted_source_verifier.allowed_providers,
                frozenset({"test-provider"}),
            )

    def test_rejects_provider_not_in_allowlist(self):
        adapter = MinimalAdapter()
        adapter.provider_name = "other-provider"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not explicitly allowlisted"):
                build_production_evidence_runtime(
                    self.console,
                    config=make_test_config(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=adapter,
                )


    def test_factory_rejects_provider_name_property_that_raises(self):
        class BrokenProviderNameAdapter:
            @property
            def provider_name(self):
                raise RuntimeError("private adapter error detail")

            def fetch_receipt(self, source_record_id, execution_id):
                return None

            def verify_receipt(self, receipt):
                return False

            def match_execution(self, receipt, execution_id):
                return False

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provider_name could not be read safely") as error:
                build_production_evidence_runtime(
                    self.console,
                    config=make_test_config(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=BrokenProviderNameAdapter(),
                )
        self.assertNotIn("private adapter error detail", str(error.exception))

    def test_rejects_adapter_without_provider_name(self):
        adapter = MinimalAdapter()
        adapter.provider_name = ""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "declare a provider_name"):
                build_production_evidence_runtime(
                    self.console,
                    config=make_test_config(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=adapter,
                )

    def test_rejects_invalid_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(TypeError, "LiveOperatingConsole"):
                build_production_evidence_runtime(
                    object(),
                    config=make_test_config(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=self.adapter,
                )


    def test_receipt_replay_is_blocked_after_factory_recreation(self):
        from datetime import datetime, timezone
        from src.trusted_source_receipt import TrustedSourceReceipt

        class StableReceiptAdapter:
            provider_name = "test-provider"

            def fetch_receipt(self, source_record_id, execution_id):
                return TrustedSourceReceipt(
                    provider_name=self.provider_name,
                    source_record_id=source_record_id,
                    execution_id=execution_id,
                    raw_observation="external_event=confirmed",
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    content_hash="sha256:stable-replay-fixture",
                    verification_method="fake-test-only",
                )

            def verify_receipt(self, receipt):
                return True

            def match_execution(self, receipt, execution_id):
                return receipt.execution_id == execution_id

        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "durable-replay.sqlite3")
            first = build_production_evidence_runtime(
                LiveOperatingConsole(date="2026-10-20"),
                config=make_test_config(db_path, ("test-provider",)),
                trusted_source_adapter=StableReceiptAdapter(),
            )
            first_result = first.trusted_source_verifier.verify("record-unique", "execution-unique")
            self.assertTrue(first_result.verified)

            # Build a fresh factory/runtime to simulate process restart while the
            # SQLite file is retained. Reuse the same provider record and payload.
            second = build_production_evidence_runtime(
                LiveOperatingConsole(date="2026-10-20"),
                config=make_test_config(db_path, ("test-provider",)),
                trusted_source_adapter=StableReceiptAdapter(),
            )
            second_result = second.trusted_source_verifier.verify("record-unique", "execution-unique")
            self.assertFalse(second_result.verified)
            self.assertTrue(any("replay" in reason.lower() for reason in second_result.reasons))


if __name__ == "__main__":
    unittest.main()
