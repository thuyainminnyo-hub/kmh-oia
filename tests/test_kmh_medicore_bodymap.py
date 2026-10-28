"""Acceptance tests for KMH MediCore's local synthetic Orthopedics body-map pilot."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pilots.kmh_medicore_bodymap.service import (
    BodyMapError, BodyMapStore, REGISTRY_VERSION, load_anatomy_registry, validate_annotation
)


def sample_annotation(**changes):
    record = {
        "schema_version": "0.2",
        "annotation_id": "SYN-BMA-ORTHO-0001",
        "encounter_ref": "SYN-ENC-0001",
        "data_classification": "synthetic",
        "specialty": "orthopedics",
        "anatomy_system": REGISTRY_VERSION,
        "anatomy_code": "SKULL",
        "region": "Skull",
        "view": "front",
        "laterality": "midline",
        "finding": "fracture",
        "treatment": {"code": "cast_or_splint", "status": "proposed"},
        "status": "draft",
        "author_ref": "SYN-ACTOR-CLINICIAN-1",
        "created_at": "2026-10-29T00:00:00+00:00",
        "updated_at": "2026-10-29T00:00:00+00:00",
    }
    record.update(changes)
    return record


class BodyMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "medicore-synthetic.sqlite3"
        self.actor = "SYN-ACTOR-CLINICIAN-1"
        self.store = BodyMapStore(self.db_path, authorized_actors={self.actor})

    def tearDown(self):
        self.temp.cleanup()

    def test_schema_v02_contract_matches_backend_fixture(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "medicore" / "body-map-annotation-0.2.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        fixture = sample_annotation()
        self.assertEqual(schema["properties"]["schema_version"]["const"], fixture["schema_version"])
        self.assertEqual(set(schema["required"]), set(fixture))
        self.assertFalse(set(fixture) - set(schema["properties"]))
        self.assertEqual(schema["properties"]["specialty"]["const"], fixture["specialty"])
        self.assertEqual(schema["properties"]["anatomy_system"]["const"], fixture["anatomy_system"])
        self.assertIn(fixture["anatomy_code"], schema["properties"]["anatomy_code"]["enum"])
        self.assertIn(fixture["view"], schema["properties"]["view"]["enum"])
        self.assertIn(fixture["laterality"], schema["properties"]["laterality"]["enum"])
        self.assertIn(fixture["finding"], schema["properties"]["finding"]["enum"])
        self.assertIn(fixture["treatment"]["code"], schema["properties"]["treatment"]["properties"]["code"]["enum"])
        self.assertIn(fixture["treatment"]["status"], schema["properties"]["treatment"]["properties"]["status"]["enum"])
        self.assertIn(fixture["status"], schema["properties"]["status"]["enum"])

    def test_schema_rejects_unknown_fields_by_contract(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "medicore" / "body-map-annotation-0.2.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        fixture = sample_annotation()
        fixture["patient_name"] = "must-not-be-present"
        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(set(fixture) - set(schema["properties"]))

    def test_requested_orthopedics_front_skull_fracture_draft_is_valid(self):
        result = validate_annotation(sample_annotation())
        self.assertEqual(result["specialty"], "orthopedics")
        self.assertEqual(result["view"], "front")
        self.assertEqual(result["anatomy_code"], "SKULL")
        self.assertEqual(result["finding"], "fracture")
        self.assertEqual(result["treatment"], {"code": "cast_or_splint", "status": "proposed"})
        self.assertEqual(result["status"], "draft")

    def test_service_uses_the_versioned_registry_file(self):
        registry = load_anatomy_registry()
        self.assertEqual(registry["SKULL"]["label"], "Skull")
        self.assertEqual(registry["SKULL"]["views"], ["front", "back", "both"])

    def test_unknown_registry_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            bad_registry = Path(directory) / "registry.json"
            bad_registry.write_text(json.dumps({
                "registry_version": "unexpected",
                "classification": "synthetic-pilot-only",
                "regions": [{"code": "SKULL", "label": "Skull", "views": ["front"], "laterality": ["midline"]}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(BodyMapError, "unsupported local anatomy registry version"):
                validate_annotation(sample_annotation(), registry_path=bad_registry)

    def test_create_persists_record_and_minimal_audit_atomically(self):
        created = self.store.create_annotation(sample_annotation(), actor_ref=self.actor)
        self.assertEqual(self.store.get_annotation(created["annotation_id"], self.actor), created)
        events = self.store.list_audit_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "annotation.create")
        self.assertEqual(events[0]["outcome"], "success")
        serialized_audit = json.dumps(events)
        self.assertNotIn("fracture", serialized_audit)
        self.assertNotIn("cast_or_splint", serialized_audit)
        self.assertNotIn("encounter_ref", serialized_audit)

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(BodyMapError, "created_at must be an ISO timestamp"):
            validate_annotation(sample_annotation(created_at="not-a-timestamp"))

    def test_timestamp_without_timezone_is_rejected(self):
        with self.assertRaisesRegex(BodyMapError, "created_at must include a timezone"):
            validate_annotation(sample_annotation(created_at="2026-10-29T00:00:00"))

    def test_malformed_synthetic_reference_is_rejected(self):
        with self.assertRaisesRegex(BodyMapError, "annotation_id must be a valid synthetic reference"):
            validate_annotation(sample_annotation(annotation_id="BMA-REAL-0001"))

    def test_skull_requires_midline_laterality_from_registry(self):
        with self.assertRaisesRegex(BodyMapError, "laterality is not allowed"):
            validate_annotation(sample_annotation(laterality="left"))

    def test_region_must_match_registry_label(self):
        with self.assertRaisesRegex(BodyMapError, "do not match"):
            validate_annotation(sample_annotation(region="Cranium"))

    def test_unknown_fields_are_rejected(self):
        with self.assertRaisesRegex(BodyMapError, "unknown fields"):
            validate_annotation(sample_annotation(patient_name="not-allowed"))

    def test_non_synthetic_record_is_rejected(self):
        with self.assertRaisesRegex(BodyMapError, "synthetic"):
            validate_annotation(sample_annotation(data_classification="real"))

    def test_signed_record_requires_timestamp_but_create_only_accepts_draft(self):
        signed = sample_annotation(status="signed")
        with self.assertRaisesRegex(BodyMapError, "signed_at"):
            validate_annotation(signed)
        signed["signed_at"] = "2026-10-29T00:00:00+00:00"
        with self.assertRaisesRegex(BodyMapError, "draft records only"):
            self.store.create_annotation(signed, actor_ref=self.actor)

    def test_performed_treatment_cannot_be_claimed_by_create_draft(self):
        record = sample_annotation(treatment={"code": "cast_or_splint", "status": "performed"})
        with self.assertRaisesRegex(BodyMapError, "cannot claim treatment was performed"):
            self.store.create_annotation(record, actor_ref=self.actor)

    def test_unauthorized_actor_is_denied_and_audited(self):
        with self.assertRaises(PermissionError):
            self.store.create_annotation(sample_annotation(), actor_ref="SYN-ACTOR-OTHER")
        events = self.store.list_audit_events()
        self.assertEqual(events[-1]["outcome"], "denied")
        self.assertEqual(events[-1]["action"], "annotation.create")
        with self.assertRaises(PermissionError):
            self.store.get_annotation("SYN-BMA-ORTHO-0001", actor_ref="SYN-ACTOR-OTHER")

    def test_duplicate_annotation_id_is_rejected(self):
        self.store.create_annotation(sample_annotation(), actor_ref=self.actor)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.create_annotation(sample_annotation(), actor_ref=self.actor)

    def test_audit_rows_are_append_only(self):
        self.store.create_annotation(sample_annotation(), actor_ref=self.actor)
        with self.assertRaises(sqlite3.IntegrityError):
            with sqlite3.connect(self.db_path) as db:
                db.execute("UPDATE audit_events SET outcome='tampered' WHERE event_id=1")
        with self.assertRaises(sqlite3.IntegrityError):
            with sqlite3.connect(self.db_path) as db:
                db.execute("DELETE FROM audit_events WHERE event_id=1")

    def test_existing_annotation_is_not_silently_overwritten_by_create(self):
        self.store.create_annotation(sample_annotation(), actor_ref=self.actor)
        changed = sample_annotation()
        changed["finding"] = "arthritis"
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.create_annotation(changed, actor_ref=self.actor)
        self.assertEqual(self.store.get_annotation("SYN-BMA-ORTHO-0001", self.actor)["finding"], "fracture")


if __name__ == "__main__":
    unittest.main()
