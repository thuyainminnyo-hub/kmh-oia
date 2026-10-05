"""Operational telemetry for governed OIA executions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionTelemetry:
    command_id: str
    qa_passed: bool
    blocked: bool
    rework: bool
    evidence_count: int
    standard_compliant: bool | None
    drift_detected: bool
    revalidation_triggered: bool
    revalidation_verdict: str | None

    @property
    def evidence_coverage(self) -> float:
        return 1.0 if self.evidence_count > 0 else 0.0


@dataclass(frozen=True)
class SystemHealthSnapshot:
    executions: int
    qa_pass_rate: float
    blocked_rate: float
    rework_rate: float
    evidence_coverage: float
    standard_compliance_rate: float | None
    drift_rate: float
    revalidation_rate: float
    learning_rate: float


class ExecutionTelemetryCollector:
    """Collect deterministic, local-first execution health metrics."""

    def __init__(self) -> None:
        self._records: list[ExecutionTelemetry] = []

    def record(self, telemetry: ExecutionTelemetry) -> ExecutionTelemetry:
        if not telemetry.command_id.strip():
            raise ValueError("command_id is required")
        if telemetry.evidence_count < 0:
            raise ValueError("evidence_count cannot be negative")
        self._records.append(telemetry)
        return telemetry

    def snapshot(self) -> SystemHealthSnapshot:
        total = len(self._records)
        if total == 0:
            return SystemHealthSnapshot(0, 0.0, 0.0, 0.0, 0.0, None, 0.0, 0.0, 0.0)

        def rate(predicate):
            return sum(1 for item in self._records if predicate(item)) / total

        compliance_records = [
            item for item in self._records
            if item.standard_compliant is not None
        ]
        compliance_rate = (
            sum(1 for item in compliance_records if item.standard_compliant)
            / len(compliance_records)
            if compliance_records else None
        )
        return SystemHealthSnapshot(
            executions=total,
            qa_pass_rate=rate(lambda x: x.qa_passed),
            blocked_rate=rate(lambda x: x.blocked),
            rework_rate=rate(lambda x: x.rework),
            evidence_coverage=rate(lambda x: x.evidence_count > 0),
            standard_compliance_rate=compliance_rate,
            drift_rate=rate(lambda x: x.drift_detected),
            revalidation_rate=rate(lambda x: x.revalidation_triggered),
            learning_rate=rate(lambda x: x.qa_passed and x.evidence_count > 0),
        )
