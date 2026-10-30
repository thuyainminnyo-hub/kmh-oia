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

    def __init__(self, *, ledger: Any, memory: Any, proposal_repository: Any, max_attempts: int = 5) -> None:
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        self.max_attempts = max_attempts
        self.ledger = ledger
        self.memory = memory
        self.proposal_repository = proposal_repository

    def run_once(self, limit: int = 100) -> ProjectionBatchResult:
        return self._project(self.ledger.pending_outbox(limit), claim_aware=False)

    def run_claimed(self, claimed: tuple[dict[str, Any], ...]) -> ProjectionBatchResult:
        return self._project(claimed, claim_aware=True)

    def _project(self, items: tuple[dict[str, Any], ...], *, claim_aware: bool) -> ProjectionBatchResult:
        projected = failed = 0
        for item in items:
            event_id = item["event_id"]
            claim_token = item.get("claim_token") if claim_aware else None
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
                self.ledger.mark_projected(event_id, claim_token=claim_token)
                projected += 1
            except Exception:
                failed += 1
                try:
                    if claim_aware and claim_token:
                        self.ledger.record_projection_failure(
                            event_id, "ProjectionError: projection failed",
                            claim_token=claim_token, max_attempts=self.max_attempts,
                        )
                        self.ledger.release_claim(event_id, claim_token=claim_token)
                    else:
                        self.ledger.record_projection_failure(
                            event_id, "ProjectionError: projection failed",
                            max_attempts=self.max_attempts,
                        )
                except Exception:
                    pass
        return ProjectionBatchResult(
            scanned=len(items), projected=projected, failed=failed
        )
