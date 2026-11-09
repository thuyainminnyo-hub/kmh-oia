#!/usr/bin/env python3
"""Portable regression tests for KMH geometry change-control fail-closed behavior.

Synthetic byte fixtures exercise metadata/hash gates only; they are not meshes.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent
VALIDATOR=HERE/"validate_geometry_change_request.py"
TEMPLATE=PACKAGE/"templates"/"geometry_change_request.template.json"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def complete_request(candidate_root):
    data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
    data["target_state"]="BASE-UNLOADED"
    data["proposed_assets"]={
        "body_file":"geometry_v2/body_candidate.glb","body_sha256":None,
        "lower_skirt_file":"geometry_v2/skirt_candidate.glb","lower_skirt_sha256":None,
        "source_preserved":True
    }
    for path_key,hash_key,payload in [
        ("body_file","body_sha256",b"TEST-BODY-NOT-A-REAL-MESH"),
        ("lower_skirt_file","lower_skirt_sha256",b"TEST-SKIRT-NOT-A-REAL-MESH")
    ]:
        p=candidate_root/data["proposed_assets"][path_key]
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(payload)
        data["proposed_assets"][hash_key]=digest(p)
    data["change_rationale"]={
        "observed_deviation":"Test fixture only","expected_benefit":"Test fixture only",
        "why_existing_geometry_is_insufficient":"Test fixture only","affected_features":["TEST_ONLY"]
    }
    data["supporting_evidence"]={
        "source_confirmation_record":"TEST-STATE","capture_set_manifest":"TEST-CAPTURE",
        "camera_calibration_record":"TEST-CAMERA","scale_control_record":"TEST-SCALE",
        "measurement_record":"TEST-MEASUREMENT","source_image_hashes":["a"*64],
        "state_attribution_confirmed":True,"independent_measurement_verified":True
    }
    data["qa_results"]={
        "mesh_integrity":"PASS","dimension_residuals":"PASS","silhouette_comparison":"PASS",
        "state_consistency":"PASS","source_provenance":"PASS","limitations_recorded":True
    }
    data["approvals"]={
        "technical_reviewer":{"name_or_role":"TEST REVIEWER","decision":"APPROVED","date":"2099-01-01","evidence_reference":"TEST-TECH"},
        "project_owner":{"name_or_role":"TEST OWNER","decision":"APPROVED","date":"2099-01-01","evidence_reference":"TEST-OWNER"}
    }
    data["release"]={"authorized":True,"merge_approval":"APPROVED","production_approval":"NOT_IN_SCOPE"}
    data["scope_guard"]={
        "non_operational_visual_geometry_only":True,
        "pyrotechnic_operational_calculation_included":False,
        "attachment_mechanics_inferred":False
    }
    return data

class GeometryChangeControlTests(unittest.TestCase):
    def run_gate(self,data,candidate_root=None,include_baseline=True,pin_baseline=True):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp); request=work/"request.json"; report=work/"report.json"
            baseline_root=work/"baseline"
            if include_baseline:
                for path_key,hash_key,payload in [
                    ("body_file","body_sha256",b"TEST-BASE-BODY"),
                    ("lower_skirt_file","lower_skirt_sha256",b"TEST-BASE-SKIRT")
                ]:
                    p=baseline_root/data["baseline"][path_key]
                    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(payload)
                    if pin_baseline:
                        data["baseline"][hash_key]=digest(p)
            request.write_text(json.dumps(data),encoding="utf-8")
            cmd=[sys.executable,str(VALIDATOR),str(request),"--report",str(report)]
            if include_baseline: cmd += ["--asset-root",str(baseline_root)]
            if candidate_root is not None: cmd += ["--candidate-root",str(candidate_root)]
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            return proc,json.loads(report.read_text(encoding="utf-8"))

    def test_01_empty_request_fails_closed(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
        proc,report=self.run_gate(data)
        self.assertEqual(proc.returncode,1)
        self.assertEqual(report["decision"],"BLOCKED_HOLD")
        self.assertGreater(report["blocker_count"],0)
        self.assertEqual(len(report["baseline_file_checks"]),2)
        self.assertTrue(all(x["matches"] for x in report["baseline_file_checks"]))

    def test_02_complete_request_only_reaches_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            proc,report=self.run_gate(data,candidate)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertEqual(report["decision"],"ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW")
            self.assertEqual(report["blocker_count"],0)
            self.assertTrue(all(x["matches"] for x in report["candidate_file_checks"]))
            self.assertIn("never approves",report["note"])

    def test_03_unknown_state_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate); data["target_state"]="UNKNOWN"
            proc,report=self.run_gate(data,candidate)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("Target state must be confirmed" in x for x in report["blockers"]))

    def test_04_missing_project_owner_approval_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            data["approvals"]["project_owner"]["decision"]="PENDING"
            proc,report=self.run_gate(data,candidate)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("project_owner approval is missing" in x for x in report["blockers"]))

    def test_05_candidate_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            data["proposed_assets"]["body_sha256"]="0"*64
            proc,report=self.run_gate(data,candidate)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("candidate body hash does not match" in x for x in report["blockers"]))

    def test_06_baseline_hash_mismatch_rejected(self):
        data=json.loads(TEMPLATE.read_text(encoding="utf-8"))
        data["baseline"]["body_sha256"]="0"*64
        proc,report=self.run_gate(data,pin_baseline=False)
        self.assertEqual(proc.returncode,1)
        self.assertTrue(any("baseline body hash does not match" in x for x in report["blockers"]))

    def test_07_attachment_mechanics_inference_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            data["scope_guard"]["attachment_mechanics_inferred"]=True
            proc,report=self.run_gate(data,candidate)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("Attachment mechanics must not be inferred" in x for x in report["blockers"]))

    def test_08_candidate_root_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            proc,report=self.run_gate(data,candidate_root=None)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("Candidate asset root is required" in x for x in report["blockers"]))

    def test_09_baseline_root_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp); data=complete_request(candidate)
            proc,report=self.run_gate(data,candidate,include_baseline=False)
            self.assertEqual(proc.returncode,1)
            self.assertTrue(any("Locked baseline asset root is required" in x for x in report["blockers"]))

if __name__=="__main__":
    unittest.main(verbosity=2)
