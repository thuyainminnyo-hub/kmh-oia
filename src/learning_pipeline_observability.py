"""Read-only operational snapshot for the SQLite learning pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class LearningPipelineSnapshot:
    captured_at: str
    total_events: int
    pending_events: int
    projected_events: int
    dead_letter_events: int
    active_leases: int
    expired_leases: int
    unleased_pending_events: int
    oldest_pending_age_seconds: float | None
    retry_attempts_total: int
    pending_attempts_max: int
    ledger_healthy: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningPipelineObservability:
    """Build a point-in-time, read-only view; never mutates queue state."""

    def __init__(self, *, ledger: Any) -> None:
        self.ledger = ledger

    def snapshot(self, *, now_epoch: float | None = None) -> LearningPipelineSnapshot:
        import time

        now = time.time() if now_epoch is None else now_epoch
        if not isinstance(now, (int, float)) or isinstance(now, bool):
            raise ValueError("now_epoch must be a numeric timestamp")
        captured_at = datetime.fromtimestamp(now, timezone.utc).isoformat()
        with self.ledger._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM learning_events),
                    (SELECT COUNT(*) FROM learning_outbox o
                     WHERE o.state = 'PENDING'
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id)),
                    (SELECT COUNT(*) FROM learning_outbox WHERE state = 'PROJECTED'),
                    (SELECT COUNT(*) FROM learning_dead_letters),
                    (SELECT COUNT(*) FROM learning_outbox o
                     WHERE o.state = 'PENDING' AND o.lease_until > ?
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id)),
                    (SELECT COUNT(*) FROM learning_outbox o
                     WHERE o.state = 'PENDING' AND o.lease_until IS NOT NULL
                       AND o.lease_until <= ?
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id)),
                    (SELECT COUNT(*) FROM learning_outbox o
                     WHERE o.state = 'PENDING' AND o.lease_until IS NULL
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id)),
                    (SELECT MIN((julianday('now') - julianday(o.created_at)) * 86400.0)
                     FROM learning_outbox o
                     WHERE o.state = 'PENDING'
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id)),
                    (SELECT COALESCE(SUM(attempts), 0) FROM learning_outbox),
                    (SELECT COALESCE(MAX(attempts), 0) FROM learning_outbox o
                     WHERE o.state = 'PENDING'
                       AND NOT EXISTS (SELECT 1 FROM learning_dead_letters d
                                       WHERE d.event_id = o.event_id))
                """,
                (now, now),
            ).fetchone()
        return LearningPipelineSnapshot(
            captured_at=captured_at,
            total_events=int(row[0]),
            pending_events=int(row[1]),
            projected_events=int(row[2]),
            dead_letter_events=int(row[3]),
            active_leases=int(row[4]),
            expired_leases=int(row[5]),
            unleased_pending_events=int(row[6]),
            oldest_pending_age_seconds=(
                max(0.0, float(row[7])) if row[7] is not None else None
            ),
            retry_attempts_total=int(row[8]),
            pending_attempts_max=int(row[9]),
            ledger_healthy=bool(self.ledger.health_check()),
        )
