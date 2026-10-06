"""Aggregate evidence-backed learning across independent OIA runtime instances."""
from dataclasses import dataclass
from collections import Counter
from typing import Iterable
from .operating_memory import OperatingMemoryRecord

@dataclass(frozen=True)
class InstanceLearningRecord:
    instance_id: str
    memory: OperatingMemoryRecord

@dataclass(frozen=True)
class CrossInstanceInsight:
    pattern: str
    instance_count: int
    observation_count: int
    confidence: float
    recommendation: str

class CrossInstanceLearningEngine:
    """Federate learning without sharing raw runtime state between instances."""
    def ingest(self, instance_id: str, records: Iterable[OperatingMemoryRecord]) -> tuple[InstanceLearningRecord, ...]:
        if not instance_id.strip():
            raise ValueError("instance_id is required")
        return tuple(InstanceLearningRecord(instance_id.strip(), record) for record in records)

    def synthesize(self, records: Iterable[InstanceLearningRecord]) -> tuple[CrossInstanceInsight, ...]:
        grouped: dict[str, list[InstanceLearningRecord]] = {}
        for item in records:
            if not item.instance_id.strip():
                raise ValueError("instance_id is required")
            pattern = item.memory.learned.strip()
            if pattern:
                grouped.setdefault(pattern, []).append(item)
        insights = []
        for pattern, items in grouped.items():
            instances = {item.instance_id for item in items}
            confidence = sum(item.memory.confidence for item in items) / len(items)
            insights.append(CrossInstanceInsight(
                pattern=pattern,
                instance_count=len(instances),
                observation_count=len(items),
                confidence=confidence,
                recommendation="Consider a governed adaptation when the pattern is repeated across instances.",
            ))
        return tuple(sorted(insights, key=lambda item: (-item.instance_count, -item.observation_count, item.pattern)))
