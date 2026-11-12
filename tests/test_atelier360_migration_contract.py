from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "migrations" / "postgresql" / "001_atelier360_foundation.sql"
DOC = ROOT / "docs" / "atelier360" / "PHASE_B_DATABASE_AND_GOVERNANCE.md"
OPENAPI = ROOT / "docs" / "atelier360" / "openapi.yaml"


class TestAtelier360MigrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.api = OPENAPI.read_text(encoding="utf-8")

    def test_migration_is_transactional_and_scoped(self):
        self.assertTrue(self.sql.lstrip().startswith("BEGIN;"))
        self.assertTrue(self.sql.rstrip().endswith("COMMIT;"))
        self.assertIn("CREATE SCHEMA IF NOT EXISTS atelier360", self.sql)

    def test_model_batch_item_lineage_exists(self):
        for table in ("product_models", "production_batches", "individual_items"):
            self.assertRegex(self.sql, rf"CREATE TABLE atelier360\.{table}\s*\(")
        self.assertIn("REFERENCES atelier360.product_models", self.sql)
        self.assertIn("REFERENCES atelier360.production_batches", self.sql)

    def test_approved_records_require_human_actor_and_time(self):
        self.assertIn("approved_by IS NOT NULL AND approved_at IS NOT NULL", self.sql)
        self.assertIn("technical_review_by IS NOT NULL AND technical_review_at IS NOT NULL", self.sql)

    def test_positive_quantities_and_batch_limit(self):
        self.assertIn("planned_quantity integer NOT NULL CHECK (planned_quantity > 0)", self.sql)
        self.assertIn("approved_quantity <= planned_quantity", self.sql)
        self.assertIn("quantity numeric(14,4) NOT NULL CHECK (quantity > 0)", self.sql)

    def test_evidence_and_event_are_append_only(self):
        self.assertIn("evidence_no_update_delete", self.sql)
        self.assertIn("events_no_update_delete", self.sql)
        self.assertIn("CREATE TRIGGER evidence_no_update_delete", self.sql)
        self.assertIn("CREATE TRIGGER events_no_update_delete", self.sql)

    def test_rls_enabled_for_all_tenant_tables(self):
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.sql)
        self.assertIn("'production_events','qa_inspections','ip_assets','dpp_records'", self.sql)

    def test_qa_pass_requires_evidence(self):
        self.assertIn("disposition <> 'pass' OR evidence_id IS NOT NULL", self.sql)

    def test_dpp_publish_requires_human_approval(self):
        self.assertIn("publication_status NOT IN ('approved','published') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)", self.sql)
        self.assertIn("publication_status <> 'published' OR published_at IS NOT NULL", self.sql)

    def test_agent_controlled_autonomy_and_permission_expiry(self):
        self.assertIn("DEFAULT 'controlled'", self.sql)
        self.assertIn("expires_at timestamptz NOT NULL", self.sql)
        self.assertIn("revoked_at", self.sql)

    def test_spec_and_openapi_enforce_controlled_operations(self):
        self.assertIn("Default deny", self.doc)
        self.assertIn("single-use", self.doc)
        self.assertIn("Idempotency-Key", self.api)
        self.assertIn("If-Match", self.api)
        self.assertIn("production-release", self.api)
        self.assertIn("const: controlled", self.api)


if __name__ == "__main__":
    unittest.main(verbosity=2)
