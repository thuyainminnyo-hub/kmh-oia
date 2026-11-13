"""Tests that the protected action callback only runs after signed ALLOW."""
import tempfile
import unittest
from pathlib import Path

from src.governance_gate import decide_release
from src.key_provider_signing import sign_decision_with_provider
from src.pilot import run_pilot
from src.protected_action import ProtectedActionBlocked, execute_protected_action
from src.qa_gate import evaluate_evidence
from src.trusted_key_provider import InMemoryTrustedKeyProvider


KEY_V1=b"kmh-oia-protected-action-test-key-v1-minimum-32-bytes"
KEY_V2=b"kmh-oia-protected-action-test-key-v2-minimum-32-bytes"


class ProtectedActionTests(unittest.TestCase):
    def provider(self):
        return InMemoryTrustedKeyProvider({"key-v1":KEY_V1},"key-v1",{"key-v1"})

    def decision(self, root, approved=True):
        _, evidence, _ = run_pilot(
            "protected action",
            artifact_dir=root/"artifacts",
            evidence_path=root/"evidence.jsonl",
            source_revision="a"*40,
        )
        qa=evaluate_evidence(evidence, expected_output="protected action")
        return decide_release(
            evidence,qa,expected_source_revision="a"*40,actual_source_revision="a"*40,
            approval_id="approval:protected" if approved else None,
            approver_id="reviewer:protected" if approved else None,
            approver_authorized=approved,
        )

    def test_valid_signed_allow_runs_action_once(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=self.provider()
            signed=sign_decision_with_provider(provider,self.decision(Path(directory)))
            calls=[]
            decision,result=execute_protected_action(provider,signed,lambda: calls.append("ran") or "ok")
            self.assertEqual(decision.status,"ALLOW")
            self.assertEqual(result,"ok")
            self.assertEqual(calls,["ran"])

    def test_block_decision_never_runs_action(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=self.provider()
            signed=sign_decision_with_provider(provider,self.decision(Path(directory),approved=False))
            calls=[]
            with self.assertRaises(ProtectedActionBlocked):
                execute_protected_action(provider,signed,lambda: calls.append("ran"))
            self.assertEqual(calls,[])

    def test_bad_signature_never_runs_action(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=self.provider()
            signed=sign_decision_with_provider(provider,self.decision(Path(directory))).to_dict()
            signed["hmac_sha256"]="0"*64
            calls=[]
            with self.assertRaises(ProtectedActionBlocked):
                execute_protected_action(provider,signed,lambda: calls.append("ran"))
            self.assertEqual(calls,[])

    def test_retired_key_never_runs_action(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=self.provider()
            signed=sign_decision_with_provider(provider,self.decision(Path(directory)))
            provider.rotate(new_key_id="key-v2",new_secret=KEY_V2,accepted_key_ids={"key-v2"})
            calls=[]
            with self.assertRaises(ProtectedActionBlocked):
                execute_protected_action(provider,signed,lambda: calls.append("ran"))
            self.assertEqual(calls,[])

    def test_provider_unavailable_never_runs_action(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=self.provider()
            provider._keyring.pop("key-v1")
            signed={"key_id":"key-v1","hmac_sha256":"bad","envelope":{}}
            calls=[]
            with self.assertRaises(ProtectedActionBlocked):
                execute_protected_action(provider,signed,lambda: calls.append("ran"))
            self.assertEqual(calls,[])

    def test_invalid_callback_rejected(self):
        with self.assertRaises(TypeError):
            execute_protected_action(self.provider(),{},None)


if __name__=="__main__":
    unittest.main()
