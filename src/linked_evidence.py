"""Linked caller/serving-party evidence prototype.

Both sides independently commit to one call. This is local application logic,
not a wire-compatible SCITT implementation or cryptographic trust boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class CallerEvidence:
    request_id: str
    caller_agent_id: str
    caller_receipt_digest: str
    call_digest: str


@dataclass(frozen=True)
class ServingAdmissionReceipt:
    sequence: int
    serving_party_id: str
    request_id: str
    caller_agent_id: str
    caller_receipt_digest: str
    call_digest: str
    decision: str
    reason_code: str
    occurred_at_epoch: int
    previous_receipt_digest: str


@dataclass(frozen=True)
class LinkedEvidence:
    caller_receipt_digest: str
    admission_receipt_digest: str
    call_digest: str
    request_id: str


class ReplayDetected(ValueError):
    pass


class ServingEvidenceLedger:
    """In-memory admission ledger; persistence and distributed replay are TODO."""

    _GENESIS = "0" * 64

    def __init__(self, serving_party_id: str) -> None:
        if not serving_party_id.strip():
            raise ValueError("serving_party_id is required")
        self.serving_party_id = serving_party_id
        self._receipts: list[ServingAdmissionReceipt] = []
        self._seen_caller_refs: set[tuple[str, str]] = set()

    @property
    def receipts(self) -> tuple[ServingAdmissionReceipt, ...]:
        return tuple(self._receipts)

    def admit(
        self,
        *,
        caller: CallerEvidence,
        actual_request: dict[str, Any],
        decision: str,
        reason_code: str,
        occurred_at_epoch: int,
    ) -> ServingAdmissionReceipt:
        if decision not in {"allow", "deny", "indeterminate"}:
            raise ValueError("invalid admission decision")
        if not caller.request_id.strip() or not caller.caller_agent_id.strip():
            raise ValueError("caller identity and request ID are required")
        if not reason_code.strip() or occurred_at_epoch < 0:
            raise ValueError("reason code and valid timestamp are required")
        computed = _digest(_canonical(actual_request))
        if computed != caller.call_digest:
            raise ValueError("caller call digest does not match serving-party request digest")
        replay_key = (caller.caller_agent_id, caller.caller_receipt_digest)
        if replay_key in self._seen_caller_refs:
            raise ReplayDetected("caller receipt reference already admitted")
        sequence = len(self._receipts) + 1
        previous = self._GENESIS if not self._receipts else _digest(_canonical(self._receipts[-1].__dict__))
        receipt = ServingAdmissionReceipt(
            sequence=sequence,
            serving_party_id=self.serving_party_id,
            request_id=caller.request_id,
            caller_agent_id=caller.caller_agent_id,
            caller_receipt_digest=caller.caller_receipt_digest,
            call_digest=computed,
            decision=decision,
            reason_code=reason_code,
            occurred_at_epoch=occurred_at_epoch,
            previous_receipt_digest=previous,
        )
        self._receipts.append(receipt)
        self._seen_caller_refs.add(replay_key)
        return receipt

    def verify_chain(self) -> bool:
        previous = self._GENESIS
        seen: set[tuple[str, str]] = set()
        for expected_sequence, receipt in enumerate(self._receipts, start=1):
            if receipt.sequence != expected_sequence:
                return False
            if receipt.serving_party_id != self.serving_party_id:
                return False
            if receipt.previous_receipt_digest != previous:
                return False
            key = (receipt.caller_agent_id, receipt.caller_receipt_digest)
            if key in seen:
                return False
            seen.add(key)
            previous = _digest(_canonical(receipt.__dict__))
        return True


def link_caller_and_admission(
    *,
    caller: CallerEvidence,
    admission: ServingAdmissionReceipt,
    actual_request: dict[str, Any],
) -> LinkedEvidence | None:
    """Verify both parties refer to the same request and caller receipt."""
    computed = _digest(_canonical(actual_request))
    if caller.request_id != admission.request_id:
        return None
    if caller.caller_agent_id != admission.caller_agent_id:
        return None
    if caller.caller_receipt_digest != admission.caller_receipt_digest:
        return None
    if caller.call_digest != computed or admission.call_digest != computed:
        return None
    if admission.decision not in {"allow", "deny", "indeterminate"}:
        return None
    return LinkedEvidence(
        caller_receipt_digest=caller.caller_receipt_digest,
        admission_receipt_digest=_digest(_canonical(admission.__dict__)),
        call_digest=computed,
        request_id=caller.request_id,
    )
