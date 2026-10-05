"""Orchestrate the continuous telemetry-to-decision operating loop."""

from dataclasses import dataclass

from .decision_queue import DecisionQueue
from .execution_telemetry import ExecutionTelemetryCollector, SystemHealthSnapshot
from .signal_decision_ingestor import IngestedSignal, SignalDecisionIngestor
from .telemetry_signal_engine import IntelligenceSignal, TelemetrySignalEngine


@dataclass(frozen=True)
class IntelligenceCycle:
    snapshot: SystemHealthSnapshot
    signals: tuple[IntelligenceSignal, ...]
    ingested: tuple[IngestedSignal, ...]


class ContinuousIntelligenceOrchestrator:
    """Observe system health, detect signals, and queue governed decisions."""

    def __init__(
        self,
        *,
        telemetry: ExecutionTelemetryCollector | None = None,
        signal_engine: TelemetrySignalEngine | None = None,
        decision_queue: DecisionQueue | None = None,
        owner: str = "system",
    ) -> None:
        if not owner.strip():
            raise ValueError("owner is required")
        self.telemetry = telemetry or ExecutionTelemetryCollector()
        self.signal_engine = signal_engine or TelemetrySignalEngine()
        self.decision_queue = decision_queue or DecisionQueue()
        self.ingestor = SignalDecisionIngestor(self.decision_queue)
        self.owner = owner

    def cycle(self) -> IntelligenceCycle:
        snapshot = self.telemetry.snapshot()
        signals = tuple(self.signal_engine.analyze(snapshot))
        ingested = tuple(self.ingestor.ingest(list(signals), owner=self.owner))
        return IntelligenceCycle(snapshot, signals, ingested)
