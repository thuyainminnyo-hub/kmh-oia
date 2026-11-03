import unittest
from src.eduautomate_learning_adapter import CONTRACT_VERSION, ContractValidationError, adapt_learning_record

def valid_payload():
    return {
        "contract_version": CONTRACT_VERSION, "source_record_ref": "edu-record-0001",
        "course_ref": "course-python-49", "lesson_ref": "lesson-functions-01",
        "observed_at": "2026-11-03T12:30:00Z",
        "evidence": {
            "evidence_id": "ev-0001", "learner_ref": "learner-pseudo-001", "task_ref": "task-debug-01",
            "assistance_level": "hint", "task_risk": "low", "planning_observed": True,
            "verification_actions": 2, "reflection_observed": True, "task_performance_score": 0.9,
            "independent_learning_score": None, "delayed_retention_score": None,
        },
    }

class TestEduAutomateLearningAdapter(unittest.TestCase):
    def test_valid_contract_maps_and_preserves_missing_as_unknown(self):
        record = adapt_learning_record(valid_payload())
        self.assertEqual(record.source_record_ref, "edu-record-0001")
        self.assertEqual(record.evidence.learner_ref, "learner-pseudo-001")
        self.assertEqual(record.evidence.task_performance_score, 0.9)
        self.assertIsNone(record.evidence.independent_learning_score)
        self.assertIsNone(record.evidence.delayed_retention_score)
        self.assertEqual(record.observed_at, "2026-11-03T12:30:00+00:00")
    def test_naive_timestamp_rejected(self):
        p = valid_payload(); p["observed_at"] = "2026-11-03T12:30:00"
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_unknown_top_level_fields_rejected(self):
        p = valid_payload(); p["student_email"] = "not-accepted@example.invalid"
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_unknown_evidence_fields_rejected(self):
        p = valid_payload(); p["evidence"]["emotion"] = "happy"
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_missing_fields_rejected(self):
        p = valid_payload(); del p["course_ref"]
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_unsupported_version_rejected(self):
        p = valid_payload(); p["contract_version"] = "2.0"
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_non_pseudonymous_learner_ref_rejected(self):
        p = valid_payload(); p["evidence"]["learner_ref"] = "student@example.com"
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_invalid_score_rejected(self):
        p = valid_payload(); p["evidence"]["task_performance_score"] = 1.5
        with self.assertRaises(ContractValidationError): adapt_learning_record(p)
    def test_non_mapping_rejected(self):
        with self.assertRaises(TypeError): adapt_learning_record([])

if __name__ == "__main__": unittest.main()