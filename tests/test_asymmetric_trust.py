import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from src.asymmetric_trust import Ed25519TrustAuthority


class Ed25519TrustTests(unittest.TestCase):
    def setUp(self):
        self.private, self.public = Ed25519TrustAuthority.generate_key_pair()
        self.authority = Ed25519TrustAuthority(
            issuer="kmh-oia-test-issuer", audience="kmh-oia-qa",
            verification_keys={"key-1": self.public},
            active_key_id="key-1", active_private_key=self.private,
        )

    def test_valid_assertion_and_role(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        verified = self.authority.verify(token, required_role="qa_approver", now=101)
        self.assertEqual(verified.subject, "reviewer-1")
        self.assertEqual(verified.key_id, "key-1")

    def test_tampering_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        left, right = token.split(".")
        with self.assertRaisesRegex(ValueError, "invalid Ed25519"):
            self.authority.verify(left[:-2] + "AA." + right, required_role="qa_approver", now=101)

    def test_expired_and_wrong_role_are_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_viewer"], ttl_seconds=10, now=100)
        with self.assertRaisesRegex(ValueError, "expired"):
            self.authority.verify(token, required_role="qa_viewer", now=110)
        with self.assertRaisesRegex(ValueError, "lacks required role"):
            self.authority.verify(token, required_role="qa_approver", now=101)

    def test_rotation_keeps_old_key_verifiable_until_revoked(self):
        token_old = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        new_private, new_public = Ed25519TrustAuthority.generate_key_pair()
        self.authority.rotate_signing_key(key_id="key-2", private_key=new_private, public_key=new_public)
        token_new = self.authority.issue(subject="reviewer-2", roles=["qa_approver"], now=100)
        self.assertEqual(self.authority.verify(token_old, required_role="qa_approver", now=101).key_id, "key-1")
        self.assertEqual(self.authority.verify(token_new, required_role="qa_approver", now=101).key_id, "key-2")
        self.authority.revoke_key("key-1")
        with self.assertRaisesRegex(ValueError, "invalid Ed25519"):
            self.authority.verify(token_old, required_role="qa_approver", now=101)

    def test_revoked_active_key_fails_closed(self):
        self.authority.revoke_key("key-1")
        with self.assertRaisesRegex(RuntimeError, "no active signing key"):
            self.authority.issue(subject="reviewer-1", roles=["qa_approver"])

    def test_checkpoint_signature_and_revocation(self):
        checkpoint = {"sequence": 1, "event_count": 2, "head_hash": "a" * 64}
        key_id, signature = self.authority.sign_checkpoint(checkpoint)
        self.assertTrue(self.authority.verify_checkpoint(checkpoint, key_id=key_id, signature=signature))
        self.assertFalse(self.authority.verify_checkpoint({**checkpoint, "event_count": 3},
                                                          key_id=key_id, signature=signature))


if __name__ == "__main__":
    unittest.main()
