"""Operational recovery worker for the SQLite learning outbox.

The worker is deliberately explicit: applications may invoke run_once() during
startup or from a scheduler. It does not create hidden background threads.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.learning_outbox_projector import LearningOutboxProjector


@dataclass(frozen=True)
class RecoveryRun:
    scanned: int
    projected: int
    failed: int
    remaining: int
    healthy: bool


class LearningRecoveryWorker:
    """Run bounded, observable recovery passes over pending outbox records."""

    def __init__(
        self,
        *,
        ledger: Any,
        memory: Any,
        proposal_repository: Any,
        max_batch_size: int = 100,
        max_batches: int = 10,
    ) -> None:
        if not isinstance(max_batch_size, int) or isinstance(max_batch_size, bool) or max_batch_size < 1:
            raise ValueError("max_batch_size must be a positive integer")
        if not isinstance(max_batches, int) or isinstance(max_batches, bool) or max_batches < 1:
            raise ValueError("max_batches must be a positive integer")
        self.ledger = ledger
        self.projector = LearningOutboxProjector(
            ledger=ledger,
            memory=memory,
            proposal_repository=proposal_repository,
        )
        self.max_batch_size = max_batch_size
        self.max_batches = max_batches

    def run_once(self) -> RecoveryRun:
        scanned = projected = failed = 0
        for _ in range(self.max_batches):
            pending = self.ledger.pending_outbox(self.max_batch_size)
            if not pending:
                break
            result = self.projector.run_once(self.max_batch_size)
            scanned += result.scanned
            projected += result.projected
            failed += result.failed
            # Avoid a hot loop if a sink is persistently failing.
            if result.failed or result.projected == 0:
                break
        remaining = len(self.ledger.pending_outbox(self.max_batch_size * self.max_batches))
        healthy = bool(
            self.ledger.health_check()
            and remaining == 0
            and failed == 0
        )
        return RecoveryRun(
            scanned=scanned,
            projected=projected,
            failed=failed,
            remaining=remaining,
            healthy=healthy,
        )
