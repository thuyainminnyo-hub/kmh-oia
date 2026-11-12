"""Local validator for AEE -02 Execution Receipt task/causal semantics.

This is an application-level state machine, not an AEE wire-format,
canonical-CBOR/JCS, COSE, SCITT registration, or cryptographic verifier.
Callers must supply already-decoded receipts and independently verified
record hashes. The implementation intentionally fails closed on malformed
ordering and causal relationships.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


ZERO_HASH = b"\x00" * 32
RECORD_TYPES = {
    "task_start", "task_end", "inference", "tool_call",
    "tool_result", "egress", "admission",
}
DECISIONS = {"allow", "block", "confirm", "record"}
EXPECTED_DECISION_POINT = {
    "inference": "model",
    "tool_call": "tool",
    "tool_result": "tool",
    "egress": "network",
    "admission": "ingress",
}


class AeeTaskValidationError(ValueError):
    """An AEE receipt sequence violates task or causal semantics."""


@dataclass(frozen=True)
class AeeExecutionReceipt:
    seq: int
    prev_hash: bytes
    record_hash: bytes
    record_type: str
    decision: str
    policy_pack_digest: bytes
    config_integrity_digest: bytes
    agent_id: str
    principal: str | bytes
    task_seq: int
    ts: int
    parent_seq: int | None = None
    request_digest: bytes | None = None
    response_digest: bytes | None = None
    target: str | None = None
    decision_point: str | None = None
    confirm_seq: int | None = None
    egress_host: str | None = None


@dataclass(frozen=True)
class AeeTaskValidationResult:
    receipt_count: int
    task_count: int
    admission_count: int
    confirmed_call_count: int
    tool_result_count: int
    final_record_hash: bytes


@dataclass
class _Task:
    task_seq: int
    principal: str | bytes
    policy_pack_digest: bytes
    ended: bool = False


@dataclass(frozen=True)
class _Confirmation:
    receipt: AeeExecutionReceipt
    outcome_seq: int | None = None


def _digest_or_none(value: bytes | None, name: str, *, required: bool = False) -> None:
    if value is None:
        if required:
            raise AeeTaskValidationError(f"{name} is required")
        return
    if not isinstance(value, bytes) or len(value) != 32:
        raise AeeTaskValidationError(f"{name} must be a 32-byte digest")


def validate_aee_receipt_sequence(
    receipts: Iterable[AeeExecutionReceipt],
) -> AeeTaskValidationResult:
    """Validate AEE -02 chain, task, parent and confirmation ordering.

    This function validates decoded semantics only. It does not recompute
    record_hash from canonical CBOR/JCS; the caller must do that separately.
    """
    items = tuple(receipts)
    if not items:
        raise AeeTaskValidationError("evidence chain must not be empty")

    tasks: dict[int, _Task] = {}
    confirmations: dict[int, _Confirmation] = {}
    parent_types: dict[int, AeeExecutionReceipt] = {}
    tool_results: set[int] = set()
    previous_hash = ZERO_HASH
    task_count = 0
    admission_count = 0
    tool_result_count = 0

    for expected_seq, receipt in enumerate(items):
        if not isinstance(receipt, AeeExecutionReceipt):
            raise AeeTaskValidationError("all entries must be AeeExecutionReceipt")
        if receipt.seq != expected_seq:
            raise AeeTaskValidationError("seq must start at zero and increase by exactly one")
        if not isinstance(receipt.prev_hash, bytes) or receipt.prev_hash != previous_hash:
            raise AeeTaskValidationError("prev_hash does not match preceding record hash")
        if not isinstance(receipt.record_hash, bytes) or len(receipt.record_hash) != 32:
            raise AeeTaskValidationError("record_hash must be a 32-byte verified digest")
        if receipt.record_type not in RECORD_TYPES:
            raise AeeTaskValidationError("unsupported record_type")
        if receipt.decision not in DECISIONS:
            raise AeeTaskValidationError("unsupported decision")
        _digest_or_none(receipt.policy_pack_digest, "policy_pack_digest", required=True)
        _digest_or_none(receipt.config_integrity_digest, "config_integrity_digest", required=True)
        _digest_or_none(receipt.request_digest, "request_digest")
        _digest_or_none(receipt.response_digest, "response_digest")
        if not isinstance(receipt.agent_id, str) or not receipt.agent_id.strip():
            raise AeeTaskValidationError("agent_id is required")
        if not isinstance(receipt.principal, (str, bytes)) or not receipt.principal:
            raise AeeTaskValidationError("principal is required")
        if not isinstance(receipt.ts, int) or receipt.ts < 0:
            raise AeeTaskValidationError("ts must be a non-negative millisecond timestamp")
        if not isinstance(receipt.task_seq, int) or receipt.task_seq < 0:
            raise AeeTaskValidationError("task_seq must be a non-negative integer")

        expected_point = EXPECTED_DECISION_POINT.get(receipt.record_type)
        if receipt.decision_point is not None and expected_point is not None:
            if receipt.decision_point != expected_point:
                raise AeeTaskValidationError("decision_point does not match record_type")

        if receipt.record_type == "admission":
            admission_count += 1
            if receipt.task_seq != receipt.seq:
                raise AeeTaskValidationError("admission receipt task_seq must equal its own seq")
            if receipt.parent_seq is not None or receipt.confirm_seq is not None:
                raise AeeTaskValidationError("admission receipt cannot use task parent/confirmation fields")
            if receipt.decision not in {"allow", "block"}:
                raise AeeTaskValidationError("admission decision must be allow or block")
            previous_hash = receipt.record_hash
            parent_types[receipt.seq] = receipt
            continue

        if receipt.record_type == "task_start":
            if receipt.task_seq != receipt.seq:
                raise AeeTaskValidationError("task_start task_seq must equal its own seq")
            if receipt.decision != "allow":
                raise AeeTaskValidationError("task_start must have allow decision")
            if receipt.seq in tasks:
                raise AeeTaskValidationError("duplicate task_start")
            if receipt.confirm_seq is not None:
                raise AeeTaskValidationError("task_start cannot resolve a confirmation")
            if receipt.parent_seq is not None:
                parent = parent_types.get(receipt.parent_seq)
                if (
                    parent is None or parent.record_type != "admission"
                    or parent.decision != "allow" or receipt.parent_seq >= receipt.seq
                ):
                    raise AeeTaskValidationError("admitted task_start must reference an earlier allowed admission")
            tasks[receipt.seq] = _Task(
                task_seq=receipt.seq,
                principal=receipt.principal,
                policy_pack_digest=receipt.policy_pack_digest,
            )
            task_count += 1
        else:
            task = tasks.get(receipt.task_seq)
            if task is None or task.ended:
                raise AeeTaskValidationError("receipt must belong to an earlier open task_start")
            if receipt.principal != task.principal:
                raise AeeTaskValidationError("principal differs from task_start principal")
            if receipt.record_type != "admission" and receipt.parent_seq is not None:
                if receipt.parent_seq >= receipt.seq:
                    raise AeeTaskValidationError("parent_seq must refer to an earlier receipt")
                parent = parent_types.get(receipt.parent_seq)
                if parent is None:
                    raise AeeTaskValidationError("parent_seq is missing from this evidence chain")
                if parent.task_seq != receipt.task_seq:
                    raise AeeTaskValidationError("parent receipt must belong to the same task")
                required_parent = {
                    "tool_call": {"inference"},
                    "tool_result": {"tool_call"},
                    "egress": {"tool_call", "inference"},
                }.get(receipt.record_type)
                if required_parent is not None and parent.record_type not in required_parent:
                    raise AeeTaskValidationError("parent receipt has the wrong record_type")
            elif receipt.record_type in {"tool_call", "tool_result", "egress"}:
                raise AeeTaskValidationError("causal parent_seq is required for this record_type")

            if receipt.record_type == "task_end":
                if receipt.decision != "allow":
                    raise AeeTaskValidationError("task_end must have allow decision")
                pending = [
                    seq for seq, item in confirmations.items()
                    if item.receipt.task_seq == receipt.task_seq and item.outcome_seq is None
                ]
                if pending:
                    raise AeeTaskValidationError("task_end cannot close while confirmation is pending")
                task.ended = True

        if receipt.record_type == "tool_call":
            if receipt.decision == "confirm":
                if receipt.confirm_seq is not None:
                    raise AeeTaskValidationError("confirm request cannot itself carry confirm_seq")
                if receipt.parent_seq is None or not receipt.target or receipt.request_digest is None:
                    raise AeeTaskValidationError("confirm requires parent_seq, target and request_digest")
                confirmations[receipt.seq] = _Confirmation(receipt)
            elif receipt.confirm_seq is not None:
                if receipt.decision not in {"allow", "block"}:
                    raise AeeTaskValidationError("confirmation outcome must be allow or block")
                pending = confirmations.get(receipt.confirm_seq)
                if pending is None or pending.outcome_seq is not None:
                    raise AeeTaskValidationError("confirm_seq must identify one unresolved earlier confirm")
                original = pending.receipt
                if (
                    original.parent_seq != receipt.parent_seq
                    or original.target != receipt.target
                    or original.request_digest != receipt.request_digest
                    or original.task_seq != receipt.task_seq
                ):
                    raise AeeTaskValidationError("confirmation outcome does not match original call")
                confirmations[receipt.confirm_seq] = _Confirmation(original, receipt.seq)

        if receipt.record_type == "tool_result":
            if receipt.decision not in {"allow", "record"}:
                raise AeeTaskValidationError("tool_result must describe an executed or observed result")
            parent = parent_types[receipt.parent_seq]  # validated above
            if parent.decision != "allow":
                raise AeeTaskValidationError("tool_result cannot precede an allow tool_call outcome")
            if receipt.parent_seq in tool_results:
                raise AeeTaskValidationError("a tool_call may have at most one tool_result")
            tool_results.add(receipt.parent_seq)
            tool_result_count += 1

        if receipt.confirm_seq is not None and receipt.record_type != "tool_call":
            raise AeeTaskValidationError("confirm_seq is only valid on a tool_call outcome")

        if receipt.record_type == "egress":
            if not isinstance(receipt.egress_host, str) or not receipt.egress_host.strip():
                raise AeeTaskValidationError("egress receipt requires egress_host")

        parent_types[receipt.seq] = receipt
        previous_hash = receipt.record_hash

    return AeeTaskValidationResult(
        receipt_count=len(items),
        task_count=task_count,
        admission_count=admission_count,
        confirmed_call_count=len(confirmations),
        tool_result_count=tool_result_count,
        final_record_hash=previous_hash,
    )
