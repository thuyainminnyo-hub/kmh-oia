"""Idempotent projector from the SQLite learning outbox to legacy stores.

The SQLite learning ledger remains authoritative. JSON memory and the proposal
repository are downstream projections and may be replayed after partial failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectionBatchResult:
    scanned: int
    projected: int
    failed: int


class LearningOutboxProjector:
    """Project pending ledger records, marking completion only after all sinks."""

    def __init__(self, *, ledger: Any, memory: Any, proposal_repository: Any) -> None:
        self.ledger = ledger
        self.memory = memory
        self.proposal_repository = proposal_repository

    def run_once(self, limit: int = 100) -> ProjectionBatchResult:
        pending = self.ledger.pending_outbox(limit)
        projected = failed = 0
        for item in pending:
            event_id = item["event_id"]
            try:
                bundle = self.ledger.get_projection_bundle(event_id)
                if bundle["state"] != "PENDING":
                    continue
                if bundle["event_id"] != event_id:
                    raise ValueError("outbox event identity mismatch")

                event = bundle["event"]
                memory_fields = {
                    name: event[name]
                    for name in (
                        "command_id", "wanted", "did", "actual", "verified",
                        "decision", "learned", "changed", "next_command",
                    )
                }
                if "confidence" in event:
                    memory_fields["confidence"] = event["confidence"]
                record = self.memory.record(**memory_fields, event_id=event_id)
                if record.event_id != event_id:
                    raise ValueError("memory projection returned a different event identity")

                proposal = bundle["proposal"]
                if proposal is not None:
                    proposal_payload = dict(proposal)
                    proposal_payload["id"] = bundle["proposal_id"]
                    canonical = self.proposal_repository.get_or_create(
                        proposal_payload, idempotency_key=bundle["proposal_id"]
                    )
                    if canonical.get("id") != bundle["proposal_id"]:
                        raise ValueError("proposal projection returned a different identity")

                # Only acknowledge after every configured projection succeeded.
                self.ledger.mark_projected(event_id)
                projected += 1
            except Exception as exc:
                failed += 1
                # Keep error text bounded; do not include payloads or secrets.
                try:
                    self.ledger.record_projection_failure(
                        event_id, f"{type(exc).__name__}: projection failed"
                    )
                except Exception:
                    # A failed failure-record must not hide the original failure
                    # or falsely acknowledge the outbox item.
                    pass
        return ProjectionBatchResult(
            scanned=len(pending), projected=projected, failed=failed
        )
