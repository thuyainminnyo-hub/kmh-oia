"""Stage 15 operational drill evidence records.

These records describe evidence captured from an actual exercise. They do not
execute infrastructure operations and cannot be treated as proof until an
operator supplies the corresponding observed result and provenance.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DrillRecord:
    drill_id: str
    drill_type: str
    environment: str
    started_at: str
    completed_at: str
    operator: str
    observed_result: str
    evidence_source: str


class OperationalDrillRecordValidator:
    REQUIRED_DRILLS = ("rollback", "incident_response")

    def validate(self, record: DrillRecord) -> None:
        fields = (
            record.drill_id,
            record.drill_type,
            record.environment,
            record.started_at,
            record.completed_at,
            record.operator,
            record.observed_result,
            record.evidence_source,
        )
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            raise ValueError("drill records require complete provenance and observed result")
        if record.drill_type not in self.REQUIRED_DRILLS:
            raise ValueError("unsupported operational drill type")

    def require_success_evidence(self, records: tuple[DrillRecord, ...]) -> None:
        for drill_type in self.REQUIRED_DRILLS:
            matches = [r for r in records if r.drill_type == drill_type]
            if not matches:
                raise RuntimeError(f"missing operational drill evidence: {drill_type}")
            if not any(r.observed_result.strip().lower() in {"passed", "success", "successful"} for r in matches):
                raise RuntimeError(f"no successful {drill_type} drill evidence")
