"""Evidence-first social-impact platform transparency checks.

This pilot emits review signals, not findings of fraud or legal conclusions.
It deliberately uses explicit, verified observations rather than inferred
identity, behavioral biometrics, or opaque model scores.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json


class EvidenceStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ReviewDisposition(str, Enum):
    MORE_EVIDENCE_REQUIRED = "more_evidence_required"
    HUMAN_REVIEW_RECOMMENDED = "human_review_recommended"
    NO_RULE_TRIGGERED = "no_rule_triggered"


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    evidence_type: str
    status: EvidenceStatus
    observed_facts: tuple[str, ...] = ()
    content_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if not self.evidence_type.strip():
            raise ValueError("evidence_type must not be empty")
        if self.content_sha256 is not None:
            digest = self.content_sha256.lower()
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("content_sha256 must be a 64-character hexadecimal SHA-256 digest")


@dataclass(frozen=True)
class PlatformCase:
    case_id: str
    claim_type: str
    evidence: tuple[EvidenceItem, ...] = ()
    reported_claim: str = ""

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if not self.claim_type.strip():
            raise ValueError("claim_type must not be empty")
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique within a case")


@dataclass(frozen=True)
class RiskSignal:
    code: str
    explanation: str
    supporting_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    case_id: str
    occurred_at: str
    details: dict[str, object]
    previous_hash: str | None
    event_hash: str


@dataclass
class AuditChain:
    """In-memory append-only hash chain for pilot/demo use only."""
    events: list[AuditEvent] = field(default_factory=list)

    def append(self, event_type: str, case_id: str, details: dict[str, object]) -> AuditEvent:
        previous_hash = self.events[-1].event_hash if self.events else None
        occurred_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "event_type": event_type,
            "case_id": case_id,
            "occurred_at": occurred_at,
            "details": details,
            "previous_hash": previous_hash,
        }
        event_hash = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        event = AuditEvent(event_type, case_id, occurred_at, dict(details), previous_hash, event_hash)
        self.events.append(event)
        return event

    def verify(self) -> bool:
        previous_hash = None
        for event in self.events:
            payload = {
                "event_type": event.event_type,
                "case_id": event.case_id,
                "occurred_at": event.occurred_at,
                "details": event.details,
                "previous_hash": event.previous_hash,
            }
            expected = sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            if event.previous_hash != previous_hash or event.event_hash != expected:
                return False
            previous_hash = event.event_hash
        return True


RULES: dict[str, tuple[str, str]] = {
    "additional_payment_requested_after_withdrawal": (
        "additional_payment_before_withdrawal",
        "A request for additional payment after a withdrawal request was reported; verify terms and transaction evidence.",
    ),
    "withdrawal_delayed_without_timeline": (
        "withdrawal_delay_without_timeline",
        "A withdrawal delay without a clear timeline was reported; compare against published terms and dated records.",
    ),
    "account_restricted_without_reason": (
        "restriction_without_explanation",
        "An account restriction without a stated reason was reported; request the platform's written explanation.",
    ),
    "transaction_records_conflict": (
        "conflicting_transaction_records",
        "Two or more records may conflict; reconcile timestamps, amounts, currency, and transaction references.",
    ),
}


@dataclass(frozen=True)
class AuditResult:
    case_id: str
    disposition: ReviewDisposition
    signals: tuple[RiskSignal, ...]
    verified_evidence_count: int
    rejected_evidence_count: int
    unverified_evidence_count: int


class PlatformTransparencyAuditor:
    """Deterministic rule-based triage. Never labels a platform fraudulent."""

    def __init__(self, audit_chain: AuditChain | None = None) -> None:
        self.audit_chain = audit_chain if audit_chain is not None else AuditChain()

    def evaluate(self, case: PlatformCase) -> AuditResult:
        verified = [item for item in case.evidence if item.status == EvidenceStatus.VERIFIED]
        rejected = [item for item in case.evidence if item.status == EvidenceStatus.REJECTED]
        pending = [item for item in case.evidence if item.status == EvidenceStatus.PENDING]

        signals: list[RiskSignal] = []
        if verified:
            fact_to_evidence: dict[str, list[str]] = {}
            for item in verified:
                for fact in item.observed_facts:
                    fact_to_evidence.setdefault(fact, []).append(item.evidence_id)
            for fact, (code, explanation) in RULES.items():
                evidence_ids = tuple(sorted(fact_to_evidence.get(fact, [])))
                if evidence_ids:
                    signals.append(RiskSignal(code, explanation, evidence_ids))

        if not verified:
            disposition = ReviewDisposition.MORE_EVIDENCE_REQUIRED
        elif signals:
            disposition = ReviewDisposition.HUMAN_REVIEW_RECOMMENDED
        else:
            disposition = ReviewDisposition.NO_RULE_TRIGGERED

        result = AuditResult(
            case_id=case.case_id,
            disposition=disposition,
            signals=tuple(signals),
            verified_evidence_count=len(verified),
            rejected_evidence_count=len(rejected),
            unverified_evidence_count=len(pending),
        )
        self.audit_chain.append("platform_case_evaluated", case.case_id, {
            "claim_type": case.claim_type,
            "disposition": result.disposition.value,
            "signal_codes": [signal.code for signal in result.signals],
            "verified_evidence_count": result.verified_evidence_count,
            "rejected_evidence_count": result.rejected_evidence_count,
            "unverified_evidence_count": result.unverified_evidence_count,
        })
        return result
