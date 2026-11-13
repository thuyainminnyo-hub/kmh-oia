"""Single orchestration path from checkout preflight to protected action.

The caller supplies a trusted approval-authority adapter and a trusted key
provider. This module composes existing gates; it does not provide production
identity, KMS, approval storage, or deployment infrastructure by itself.
"""
from pathlib import Path
from typing import Callable, TypeVar

from src.approval_policy import ApprovalAuthority
from src.evidence_object import EvidenceObject
from src.governance_gate import ReleaseDecision
from src.key_provider_signing import sign_decision_with_provider
from src.protected_action import execute_protected_action
from src.qa_gate import QAVerdict
from src.release_preflight import preflight_release
from src.signed_release_envelope import SignedDecisionEnvelope
from src.trusted_key_provider import TrustedKeyProvider

T = TypeVar("T")


def execute_release_pipeline(
    evidence: EvidenceObject,
    qa_verdict: QAVerdict | None,
    *,
    expected_source_revision: str,
    checkout_root: str | Path,
    approval_authority: ApprovalAuthority,
    approval_id: str | None,
    signing_service_id: str,
    accepted_policy_ids: set[str],
    key_provider: TrustedKeyProvider,
    protected_action: Callable[[], T],
) -> tuple[ReleaseDecision, SignedDecisionEnvelope, T]:
    """Preflight, decide, sign, verify, then invoke the action only if ALLOW.

    A BLOCK decision may still be signed to retain a verifiable decision record,
    but the protected-action guard will refuse to run its callback. Source
    revision discovery or key-provider failures raise before the action.
    """
    decision = preflight_release(
        evidence,
        qa_verdict,
        expected_source_revision=expected_source_revision,
        checkout_root=checkout_root,
        approval_authority=approval_authority,
        approval_id=approval_id,
        signing_service_id=signing_service_id,
        accepted_policy_ids=accepted_policy_ids,
    )
    signed_decision = sign_decision_with_provider(key_provider, decision)
    verified_decision, result = execute_protected_action(
        key_provider, signed_decision, protected_action
    )
    return verified_decision, signed_decision, result
