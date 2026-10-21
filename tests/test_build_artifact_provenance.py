import unittest
from copy import deepcopy

from scripts.validate_build_artifact_provenance import (
    BuildArtifactProvenanceError,
    validate_build_artifact_provenance,
)


class BuildArtifactProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "schema_version": 1,
            "repository": "thuyainminnyo-hub/kmh-oia",
            "workflow_path": ".github/workflows/trusted-build.yml",
            "run_id": "123456",
            "run_attempt": 1,
            "run_conclusion": "success",
            "source_sha": "a" * 40,
            "artifact_id": "789012",
            "artifact_name": "kmh-oia-runtime-bundle",
            "artifact_digest": "sha256:" + "b" * 64,
            "producer_run_id": "123456",
        }
        self.expected = {
            "expected_repository": "thuyainminnyo-hub/kmh-oia",
            "allowed_workflow_paths": (".github/workflows/trusted-build.yml",),
            "expected_source_sha": "a" * 40,
            "expected_run_id": "123456",
            "expected_artifact_id": "789012",
            "expected_artifact_name": "kmh-oia-runtime-bundle",
            "expected_artifact_digest": "sha256:" + "b" * 64,
        }

    def test_accepts_exact_approved_successful_provenance_contract(self):
        self.assertEqual(
            validate_build_artifact_provenance(self.payload, **self.expected),
            self.payload,
        )

    def test_rejects_missing_or_extra_fields(self):
        for mutation in ("missing", "extra"):
            payload = deepcopy(self.payload)
            if mutation == "missing":
                del payload["artifact_id"]
            else:
                payload["mutable_download_url"] = "https://example.invalid"
            with self.subTest(mutation=mutation), self.assertRaises(BuildArtifactProvenanceError):
                validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_non_successful_run(self):
        payload = deepcopy(self.payload)
        payload["run_conclusion"] = "failure"
        with self.assertRaisesRegex(BuildArtifactProvenanceError, "successful"):
            validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_unapproved_workflow_identity(self):
        payload = deepcopy(self.payload)
        payload["workflow_path"] = ".github/workflows/untrusted.yml"
        with self.assertRaisesRegex(BuildArtifactProvenanceError, "allowlist"):
            validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_source_sha_mismatch_and_abbreviated_sha(self):
        for sha in ("c" * 40, "a" * 12):
            payload = deepcopy(self.payload)
            payload["source_sha"] = sha
            with self.subTest(sha=sha), self.assertRaises(BuildArtifactProvenanceError):
                validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_run_id_mismatch_or_cross_run_artifact(self):
        for field in ("run_id", "producer_run_id"):
            payload = deepcopy(self.payload)
            payload[field] = "654321"
            with self.subTest(field=field), self.assertRaisesRegex(BuildArtifactProvenanceError, "run ID"):
                validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_artifact_id_name_or_digest_mismatch(self):
        changes = {
            "artifact_id": "789013",
            "artifact_name": "other-artifact",
            "artifact_digest": "sha256:" + "c" * 64,
        }
        for field, value in changes.items():
            payload = deepcopy(self.payload)
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(BuildArtifactProvenanceError):
                validate_build_artifact_provenance(payload, **self.expected)

    def test_rejects_malformed_ids_digest_and_attempt(self):
        changes = {
            "artifact_id": "0",
            "run_id": "0123",
            "artifact_digest": "b" * 64,
            "run_attempt": True,
        }
        for field, value in changes.items():
            payload = deepcopy(self.payload)
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(BuildArtifactProvenanceError):
                validate_build_artifact_provenance(payload, **self.expected)

    def test_requires_explicit_allowlist_and_release_sha(self):
        with self.assertRaisesRegex(BuildArtifactProvenanceError, "allowlist"):
            validate_build_artifact_provenance(self.payload, **{**self.expected, "allowed_workflow_paths": ()})
        with self.assertRaisesRegex(BuildArtifactProvenanceError, "expected release SHA"):
            validate_build_artifact_provenance(self.payload, **{**self.expected, "expected_source_sha": "c" * 40})


if __name__ == "__main__":
    unittest.main()
