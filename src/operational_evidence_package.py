"""Stage 14 deterministic operational evidence package."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OperationalEvidencePackage:
    deployment_id: str
    items: tuple[tuple[str, str], ...]
    complete: bool
    missing: tuple[str, ...]


class OperationalEvidencePackageBuilder:
    """Build a completeness-checked package from explicitly supplied evidence."""

    REQUIRED_EVIDENCE = (
        "release",
        "deployment",
        "configuration",
        "backup_recovery",
        "security_governance",
        "health",
        "telemetry",
        "stability",
        "rollback",
        "recovery",
        "slo_reliability",
        "incident",
        "change_control",
        "post_deployment_review",
    )

    def build(self, *, deployment_id: str, evidence: dict[str, str]) -> OperationalEvidencePackage:
        if not deployment_id.strip():
            raise ValueError("deployment_id is required")
        items = []
        missing = []
        for key in self.REQUIRED_EVIDENCE:
            value = evidence.get(key, "")
            if not isinstance(value, str):
                raise ValueError("evidence values must be strings")
            value = value.strip()
            items.append((key, value))
            if not value:
                missing.append(key)
        return OperationalEvidencePackage(
            deployment_id.strip(), tuple(items), not missing, tuple(missing)
        )

    def require_complete(self, package: OperationalEvidencePackage) -> None:
        if not package.complete:
            raise RuntimeError(
                "operational evidence package incomplete: " + ", ".join(package.missing)
            )
