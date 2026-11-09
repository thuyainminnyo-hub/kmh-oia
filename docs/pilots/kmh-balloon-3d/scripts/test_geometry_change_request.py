#!/usr/bin/env python3
"""Regression tests for KMH geometry change-control fail-closed behavior."""
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
VALIDATOR = HERE / "validate_geometry_change_request.py"
TEMPLATE = PACKAGE / "templates" / "geometry_change_request.template.json"
PROJECT_ROOT = Path("/mnt/data/KMH_Myanmar_Balloon_3D_Intelligence_Pilot")

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def complete_request(candidate_root):
    data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
    data["target_state"]="BASE-UNLOADED"
    data["proposed_assets"]={
        "body_file":"geometry_v2/body_candidate.glb",
        "body_sha256":None,
        "lower_skirt_file":"geometry_v2/skirt_candidate.glb",
        "lower_skirt_sha256":None,
        "source_preserved":True
    }
    body=candidate_root/data["proposed_assets"]["body_file"]
    skirt=candidate_root/data["proposed_assets"]["lower_skirt_file"]
    body.parent.mkdir(parents=True,exist_ok=True)
    body.write_bytes(b"TEST-CANDIDATE-BODY-NOT-A-REAL-MESH")
    skirt.write_bytes(b"TEST-CANDIDATE-SKIRT-NOT-A-REAL-MESH")
    data["proposed_assets"]["body_sha256"]=digest(body)
    data["proposed_assets"]["lower_skirt_sha256"]=digest(skirt)
    data["change_rationale"]={
        "observed_deviation":"Regression fixture only.",
        "expected_benefit":"Exercise evidence-complete validator path.",
        "why_existing_geometry_is_insufficient":"Test fixture only.",
        "affected_features":["TEST_ONLY"]
    }
    data["supporting_evidence"]={
        "source_confirmation_record":"TEST-STATE-CONFIRM",
        "capture_set_manifest":"TEST-CAPTURE-MANIFEST",
        "camera_calibration_record":"TEST-CAMERA-CALIBRATION",
        "scale_control_record":"TEST-SCALE-CONTROL",
        "measurement_record":"TEST-INDEPENDENT-MEASUREMENT",
        "source_image_hashes":["a"*64],
        "state_attribution_confirmed":True,
        "independent_measurement_verified":True
    }
    data["qa_results"]={
        "mesh_integrity":"PASS",
        "dimension_residuals":"PASS",
        "silhouette_comparison":"PASS",
        "state_consistency":"PASS",
        "source_provenance":"PASS",
        "limitations_recorded":True
    }
    data["approvals"]={
        "technical_reviewer":{"name_or_role":"TEST REVIEWER","decision":"APPROVED","date":"2099-01-01","evidence_reference":"TEST-TECH-APPROVAL"},
        "project_owner":{"name_or_role":"TEST OWNER","decision":"APPROVED","date":"2099-01-01","evidence_reference":"TEST-OWNER-APPROVAL"}
    }
    data["release"]={"authorized":True,"merge_approval":"APPROVED","production_approval":"NOT_IN_SCOPE"}
    data["scope_guard"]={
        "non_operational_visual_geometry_only":True,
        "pyrotechnic_operational_calculation_included":False,
        "attachment_mechanics_inferred":False
    }
    return data

class GeometryChangeControlTests(unittest.TestCase):
    def validate(self,data,candidate_root=None):
        with tempfile.TemporaryDirectory() as tmp:
            req=Path(tmp)/"request.json"
            report=Path(tmp)/"report.json"
            req.write_text(json.dumps(data),encoding="utf-8")
            cmd=[sys.executable,str(VALIDATOR),str(req),"--report",str(report)]
            if PROJECT_ROOT.exists():
                cmd += ["--asset-root",str(PROJECT_ROOT)]
            if candidate_root is not None:
                cmd += ["--candidate-root",str(candidate_root)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
            return result,json.loads(report.read_text(encoding="utf-8"))

    def test_01_empty_template_fails_closed(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
        result,report=self.validate(data)
        self.assertEqual(result.returncode,1)
        self.assertEqual(report["decision"],"BLOCKED_HOLD")
        self.assertGreater(report["blocker_count"],0)
        self.assertEqual(len(report["baseline_file_checks"]),2)
        self.assertTrue(all(x["matches"] for x in report["baseline_file_checks"]))

    def test_02_complete_evidence_only_eligible_for_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)
            data=complete_request(candidate)
            result,report=self.validate(data,candidate)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(report["decision"],"ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW")
            self.assertEqual(report["blocker_count"],0)
            self.assertTrue(all(x["matches"] for x in report["candidate_file_checks"]))
            self.assertIn("never approves",report["note"])

    def test_03_unknown_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)
            data=complete_request(candidate)
            data["target_state"]="UNKNOWN"
            result,report=self.validate(data,candidate)
            self.assertEqual(result.returncode,1)
            self.assertTrue(any("Target state must be confirmed" in x for x in report["blockers"]))

    def test_04_missing_project_owner_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)
            data=complete_request(candidate)
            data["approvals"]["project_owner"]["decision"]="PENDING"
            result,report=self.validate(data,candidate)
            self.assertEqual(result.returncode,1)
            self.assertTrue(any("project_owner approval is missing" in x for x in report["blockers"]))

    def test_05_candidate_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)
            data=complete_request(candidate)
            data["proposed_assets"]["body_sha256"]="0"*64
            result,report=self.validate(data,candidate)
            self.assertEqual(result.returncode,1)
            self.assertTrue(any("candidate body hash does not match" in x for x in report["blockers"]))

    def test_06_baseline_hash_mismatch_is_rejected(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
        data["baseline"]["body_sha256"]="0"*64
        result,report=self.validate(data)
        self.assertEqual(result.returncode,1)
        self.assertTrue(any("baseline body hash does not match" in x for x in report["blockers"]))

    def test_07_attachment_mechanics_inference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)
            data=complete_request(candidate)
            data["scope_guard"]["attachment_mechanics_inferred"]=True
            result,report=self.validate(data,candidate)
            self.assertEqual(result.returncode,1)
            self.assertTrue(any("Attachment mechanics must not be inferred" in x for x in report["blockers"]))

if __name__ == "__main__":
    unittest.main(verbosity=2)
