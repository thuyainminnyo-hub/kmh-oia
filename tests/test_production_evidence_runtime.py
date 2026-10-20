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
                ),
                trusted_source_adapter=self.adapter,
            )
            self.assertTrue(bridge.trusted_source_verifier.replay_store.health_check())
            self.assertEqual(
                bridge.trusted_source_verifier.allowed_providers,
                frozenset({"test-provider"}),
            )

    def test_rejects_empty_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ProductionEvidenceRuntimeConfig("", ("test-provider",)).validate()

    def test_rejects_memory_sqlite_path(self):
        with self.assertRaisesRegex(ValueError, "cannot use SQLite :memory:"):
            ProductionEvidenceRuntimeConfig(":memory:", ("test-provider",)).validate()

    def test_requires_explicit_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "at least one explicit"):
            ProductionEvidenceRuntimeConfig("/tmp/receipts.sqlite3", ()).validate()

    def test_rejects_duplicate_provider_allowlist(self):
        with self.assertRaisesRegex(ValueError, "must be unique"):
            ProductionEvidenceRuntimeConfig(
                "/tmp/receipts.sqlite3", ("test-provider", "test-provider")
            ).validate()

    def test_rejects_missing_provider_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "adapter is required"):
                build_production_evidence_runtime(
                    self.console,
                    config=ProductionEvidenceRuntimeConfig(
                        str(Path(tmp) / "evidence-replay.sqlite3"),
                        ("test-provider",),
                    ),
                    trusted_source_adapter=None,
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
                    ),
                    trusted_source_adapter=adapter,
                )

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
                    ),
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
                    ),
                    trusted_source_adapter=self.adapter,
                )


if __name__ == "__main__":
    unittest.main()
