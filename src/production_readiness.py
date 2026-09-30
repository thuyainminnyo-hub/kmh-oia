"""Stage 14 deterministic production-readiness controllers."""

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    passed: bool
    checks: tuple[ReadinessCheck, ...]


class ReleaseCandidateLoader:
    """Load and validate a release-candidate manifest."""

    def load(self, path: str | Path) -> dict[str, str]:
        manifest_path = Path(path)
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("release candidate manifest must be a JSON object")
        required = ("release_id", "commit")
        if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in required):
            raise ValueError("release candidate manifest requires non-empty release_id and commit")
        return {key: str(value) for key, value in payload.items()}


class ProductionEnvironmentValidator:
    """Validate environment prerequisites without performing deployment."""

    def validate(self, *, environment: str, release: dict[str, str], dependencies: list[str]) -> ReadinessReport:
        checks = (
            ReadinessCheck("environment", bool(environment.strip()), "environment is required"),
            ReadinessCheck("release_commit", bool(release.get("commit", "").strip()), "release commit is identified"),
            ReadinessCheck("dependencies", all(item.strip() for item in dependencies), "dependency entries are non-empty"),
        )
        return ReadinessReport(all(check.passed for check in checks), checks)


class PreDeploymentHealthController:
    """Block promotion when mandatory readiness checks fail."""

    def gate(self, report: ReadinessReport) -> None:
        if not report.passed:
            failed = ", ".join(check.name for check in report.checks if not check.passed)
            raise RuntimeError(f"pre-deployment health gate blocked: {failed}")

