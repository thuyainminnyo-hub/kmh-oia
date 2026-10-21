"""Tests for staged, non-destructive legacy memory migration and rollback export."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from src.learning_admission_repository import SQLiteLearningAdmissionRepository
from src.operating_memory import OperatingMemoryRecord
from src.operating_memory_migration import MemoryMigrationError, export_memory_snapshot, import_memory_snapshot, record_hash

def samples():
    return [
        OperatingMemoryRecord(command_id="old:1", timestamp="2026-10-01T00:00:00+00:00", wanted="w1", did="d1", actual="a1", verified="v1", decision="dec1", learned="l1", changed="c1", next_command="n1", confidence=0.8).to_dict(),
        OperatingMemoryRecord(command_id="old:2", timestamp="2026-10-02T00:00:00+00:00", wanted="w2", did="d2", actual="a2", verified="v2", decision="dec2", learned="l2", changed="c2", next_command="n2", confidence=0.9).to_dict(),
    ]

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "memory.json"
        self.source.write_text(json.dumps(samples(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.repo = SQLiteLearningAdmissionRepository(self.root / "stage.sqlite3")

    def test_import_hashes_counts_and_preserves_source_bytes(self):
        before = self.source.read_bytes()
        result = import_memory_snapshot(self.source, self.repo)
        self.assertTrue(result["reconciled"])
        self.assertEqual(result["source_record_count"], 2)
        self.assertEqual(result["source_file_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(result["source_record_hashes"], [record_hash(r) for r in samples()])

    def test_duplicate_records_preserved_by_source_index(self):
        one = samples()[0]
        self.source.write_text(json.dumps([one, one]), encoding="utf-8")
        result = import_memory_snapshot(self.source, self.repo)
        self.assertEqual(result["source_record_count"], 2)
        self.assertEqual(result["source_record_hashes"], [record_hash(one), record_hash(one)])
        self.assertEqual(self.repo.counts()["learning_records"], 2)

    def test_rollback_export_hashes_match_original_and_source_remains(self):
        original = samples()
        import_memory_snapshot(self.source, self.repo)
        destination = self.root / "rollback.json"
        result = export_memory_snapshot(self.repo, destination)
        restored = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(result["exported_record_count"], 2)
        self.assertEqual([record_hash(r) for r in restored], [record_hash(r) for r in original])
        self.assertTrue(self.source.exists())

    def test_export_refuses_overwrite(self):
        import_memory_snapshot(self.source, self.repo)
        destination = self.root / "rollback.json"
        destination.write_text("preserve", encoding="utf-8")
        with self.assertRaises(MemoryMigrationError):
            export_memory_snapshot(self.repo, destination)
        self.assertEqual(destination.read_text(encoding="utf-8"), "preserve")

    def test_bad_json_fails_before_writes(self):
        self.source.write_text("{bad", encoding="utf-8")
        with self.assertRaises(MemoryMigrationError):
            import_memory_snapshot(self.source, self.repo)
        self.assertEqual(self.repo.counts()["learning_records"], 0)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "{bad")

    def test_nonempty_target_rejected(self):
        self.repo.commit(admission_key="existing", fingerprint="fp",
            learning_record={"command_id":"existing"}, adaptation_proposal=None,
            audit_event={"event_id":"event"}, result={"admitted":True})
        with self.assertRaises(MemoryMigrationError):
            import_memory_snapshot(self.source, self.repo)

if __name__ == "__main__":
    unittest.main()
