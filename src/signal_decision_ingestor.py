"""Automatically ingest intelligence signals into the governed decision queue."""

from dataclasses import dataclass

from .decision_queue import DecisionItem, DecisionQueue
from .telemetry_signal_engine import IntelligenceSignal


@dataclass(frozen=True)
class IngestedSignal:
    signal_kind: str
    decision_id: str


class SignalDecisionIngestor:
    """Convert detected signals into pending decisions without approving them."""

    def __init__(self, queue: DecisionQueue | None = None) -> None:
        self.queue = queue or DecisionQueue()

    def ingest(self, signals: list[IntelligenceSignal], *, owner: str) -> list[IngestedSignal]:
        if not owner.strip():
            raise ValueError("owner is required")

        ingested: list[IngestedSignal] = []
        for signal in signals:
            item = self.queue.enqueue(signal, owner=owner)
            ingested.append(IngestedSignal(signal.kind, item.id))
        return ingested

    def ingest_one(self, signal: IntelligenceSignal, *, owner: str) -> IngestedSignal:
        return self.ingest([signal], owner=owner)[0]
