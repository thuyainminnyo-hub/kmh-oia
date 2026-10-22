import tempfile
import unittest
from pathlib import Path

from src.live_operating_console import LiveOperatingConsole
from src.production_evidence_runtime import (
    ProductionEvidenceRuntimeConfig,
    build_production_evidence_runtime,
)
from src.trusted_source_receipt import TrustedSourceReceipt


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

    def test_builds_runtime_with_explicit_durable_sqlite_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = build_production_evidence_runtime(
                self.console,
                config=ProductionEvidenceRuntimeConfig(
                    sqlite_path=str(Path(tmp) / "evidence-replay.sqlite3"),
                    allowed_source_providers=("test-provider",),
                
                    require_signed_release_bundle=False),
                trusted_source_adapter=self.adapter,
            )
            self.assertTrue(bridge.trusted_source_verifier.replay_store.health_check())
            self.assertEqual(
                bridge.trusted_source_verifier.allowed_providers,
                frozenset({"test-provider"}),
            )

    def test_rejects_empty_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ProductionEvidenceRuntimeConfig("", ("test-provider",),
                    require_signed_release_bundle=False).validate()

    def test_rejects_memory_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            ProductionEvidenceRuntimeConfig(":memory:", ("test-provider",),
                    require_signed_release_bundle=False).validate()


    def test_rejects_uri_in_memory_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            ProductionEvidenceRuntimeConfig("file::memory:?cache=shared", ("test-provider",),
                    require_signed_release_bundle=False).validate()


    def test_rejects_sqlite_uri_even_when_it_looks_file_backed(self):
        with self.assertRaisesRegex(ValueError, "file-backed SQLite path"):
            ProductionEvidenceRuntimeConfig("file:/var/lib/kmh-oia/replay.sqlite3?mode=rw", ("test-provider",),
                    require_signed_release_bundle=False).validate()

    def test_requires_provider_allowlist_to_be_explicit_tuple(self):
        with self.assertRaisesRegex(ValueError, "explicit tuple"):
            ProductionEvidenceRuntimeConfig("/tmp/receipts.sqlite3", ["test-provider"],
                    require_signed_release_bundle=False).validate()

    def test_requires_explicit_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "at least one explicit"):
            ProductionEvidenceRuntimeConfig("/tmp/receipts.sqlite3", (),
                    require_signed_release_bundle=False).validate()


    def test_rejects_blank_entry_in_provider_allowlist_instead_of_silently_dropping_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provider names must be non-empty strings"):
                ProductionEvidenceRuntimeConfig(
                    str(Path(tmp) / "replay.sqlite3"),
                    ("test-provider", "   "),
                
                    require_signed_release_bundle=False).validate()

    def test_rejects_non_string_entry_in_provider_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provider names must be non-empty strings"):
                ProductionEvidenceRuntimeConfig(
                    str(Path(tmp) / "replay.sqlite3"),
                    ("test-provider", 17),
                
                    require_signed_release_bundle=False).validate()

    def test_rejects_duplicate_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "must be unique"):
            ProductionEvidenceRuntimeConfig(
                "/tmp/receipts.sqlite3", ("test-provider", "test-provider")
            ,
                    require_signed_release_bundle=False).validate()

    def test_rejects_missing_provider_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "adapter is required"):
                build_production_evidence_runtime(
                    self.console,
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    
                    require_signed_release_bundle=False),
                    trusted_source_adapter=None,
                )


    def test_provider_name_with_surrounding_whitespace_matches_normalized_allowlist(self):
        adapter = MinimalAdapter()
        adapter.provider_name = " test-provider "
        with tempfile.TemporaryDirectory() as tmp:
            bridge = build_production_evidence_runtime(
                self.console,
                config=ProductionEvidenceRuntimeConfig(
                    str(Path(tmp) / "evidence-replay.sqlite3"),
                    ("test-provider",),
                
                    require_signed_release_bundle=False),
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
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    
                    require_signed_release_bundle=False),
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
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    
                    require_signed_release_bundle=False),
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
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    
                    require_signed_release_bundle=False),
                    trusted_source_adapter=adapter,
                )

    def test_rejects_invalid_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(TypeError, "LiveOperatingConsole"):
                build_production_evidence_runtime(
                    object(),
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    
                    require_signed_release_bundle=False),
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
                config=ProductionEvidenceRuntimeConfig(db_path, ("test-provider",),
                    require_signed_release_bundle=False),
                trusted_source_adapter=StableReceiptAdapter(),
            )
            first_result = first.trusted_source_verifier.verify("record-unique", "execution-unique")
            self.assertTrue(first_result.verified)

            # Build a fresh factory/runtime to simulate process restart while the
            # SQLite file is retained. Reuse the same provider record and payload.
            second = build_production_evidence_runtime(
                LiveOperatingConsole(date="2026-10-20"),
                config=ProductionEvidenceRuntimeConfig(db_path, ("test-provider",),
                    require_signed_release_bundle=False),
                trusted_source_adapter=StableReceiptAdapter(),
            )
            second_result = second.trusted_source_verifier.verify("record-unique", "execution-unique")
            self.assertFalse(second_result.verified)
            self.assertTrue(any("replay" in reason.lower() for reason in second_result.reasons))


    def test_partial_release_bundle_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "release bundle activation requires every"):
                ProductionEvidenceRuntimeConfig(
                    sqlite_path=str(Path(tmp) / "replay.sqlite3"),
                    allowed_source_providers=("test-provider",),
                    runtime_bundle_path=str(Path(tmp) / "bundle.tar.gz"),
                ).validate()

    def test_invalid_release_bundle_is_rejected_before_bridge_or_store_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "bundle.tar.gz"
            bundle.write_bytes(b"not-a-runtime-bundle")
            attestation = root / "attestation.json"
            attestation.write_text("{}", encoding="utf-8")
            config = ProductionEvidenceRuntimeConfig(
                sqlite_path=str(root / "replay.sqlite3"),
                allowed_source_providers=("test-provider",),
                runtime_bundle_path=str(bundle),
                runtime_attestation_path=str(attestation),
                expected_source_revision="a" * 40,
                expected_build_run_id="12345",
                expected_artifact_id="67890",
                expected_artifact_name="kmh-oia-runtime-bundle",
                expected_artifact_digest="sha256:" + "b" * 64,
                trusted_release_public_keys={"release-key": b"k" * 32},
                allowed_release_issuers=("kmh-release-signer",),
                allowed_release_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",),
            )
            with self.assertRaisesRegex(ValueError, "configured runtime release bundle or provenance did not verify"):
                build_production_evidence_runtime(
                    self.console,
                    config=config,
                    trusted_source_adapter=self.adapter,
                )
            self.assertFalse((root / "replay.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()


    def test_production_startup_requires_signed_release_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ProductionEvidenceRuntimeConfig(
                sqlite_path=str(Path(tmp) / "replay.sqlite3"),
                allowed_source_providers=("test-provider",),
            )
            with self.assertRaisesRegex(ValueError, "production startup requires a signed runtime release bundle"):
                build_production_evidence_runtime(
                    self.console,
                    config=config,
                    trusted_source_adapter=self.adapter,
                )
            self.assertFalse((Path(tmp) / "replay.sqlite3").exists())
