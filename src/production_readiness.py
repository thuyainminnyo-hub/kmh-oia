"""Stage 14 deterministic production-readiness, deployment, and health controllers."""

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


@dataclass(frozen=True)
class DeploymentState:
    release_id: str
    traffic_percent: int
    phase: str
    reason: str = ""


@dataclass(frozen=True)
class HealthCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class HealthReport:
    passed: bool
    checks: tuple[HealthCheck, ...]


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


class ControlledDeploymentController:
    """Model bounded staged promotion without performing a real deployment."""

    def start(
        self,
        *,
        release_id: str,
        readiness: ReadinessReport,
        traffic_stages: tuple[int, ...] = (5, 25, 100),
    ) -> DeploymentState:
        if not release_id.strip():
            raise ValueError("release_id is required")
        self._validate_traffic_stages(traffic_stages)
        PreDeploymentHealthController().gate(readiness)
        first = traffic_stages[0]
        return DeploymentState(
            release_id=release_id,
            traffic_percent=first,
            phase=self._phase_for(first, traffic_stages),
        )

    def promote(
        self,
        state: DeploymentState,
        *,
        health_passed: bool,
        traffic_stages: tuple[int, ...] = (5, 25, 100),
    ) -> DeploymentState:
        self._validate_traffic_stages(traffic_stages)
        if state.phase in {"promoted", "rolled_back"}:
            raise RuntimeError(f"cannot promote from phase: {state.phase}")
        if not health_passed:
            raise RuntimeError("promotion blocked by failed health gate")

        try:
            index = traffic_stages.index(state.traffic_percent)
        except ValueError as exc:
            raise ValueError("state traffic is not part of the deployment plan") from exc
        if index >= len(traffic_stages) - 1:
            raise RuntimeError("deployment plan has no next promotion stage")

        next_traffic = traffic_stages[index + 1]
        return DeploymentState(
            release_id=state.release_id,
            traffic_percent=next_traffic,
            phase=self._phase_for(next_traffic, traffic_stages),
        )

    def rollback(self, state: DeploymentState, *, reason: str) -> DeploymentState:
        if not reason.strip():
            raise ValueError("rollback reason is required")
        return DeploymentState(
            release_id=state.release_id,
            traffic_percent=0,
            phase="rolled_back",
            reason=reason.strip(),
        )

    @staticmethod
    def _validate_traffic_stages(traffic_stages: tuple[int, ...]) -> None:
        if not traffic_stages:
            raise ValueError("traffic_stages must not be empty")
        if any(not isinstance(value, int) for value in traffic_stages):
            raise ValueError("traffic stages must be integers")
        if any(value <= 0 or value > 100 for value in traffic_stages):
            raise ValueError("traffic stages must be between 1 and 100")
        if any(left >= right for left, right in zip(traffic_stages, traffic_stages[1:])):
            raise ValueError("traffic stages must be strictly increasing")
        if traffic_stages[-1] != 100:
            raise ValueError("traffic stages must end at 100 percent")

    @staticmethod
    def _phase_for(traffic_percent: int, traffic_stages: tuple[int, ...]) -> str:
        if traffic_percent == 100:
            return "promoted"
        if traffic_percent == traffic_stages[0]:
            return "canary"
        return "staged"


class ProductionHealthGate:
    """Assess and gate deterministic post-deployment component health evidence."""

    REQUIRED_COMPONENTS = (
        "service",
        "api",
        "worker",
        "audio",
        "memory",
        "knowledge",
        "agent",
        "workflow",
        "tool",
        "security",
        "observability",
    )

    def assess(self, checks: dict[str, bool]) -> HealthReport:
        ordered_checks = tuple(
            HealthCheck(
                name=name,
                passed=checks.get(name, False),
                detail="healthy" if checks.get(name, False) else "health evidence missing or failed",
            )
            for name in self.REQUIRED_COMPONENTS
        )
        return HealthReport(all(check.passed for check in ordered_checks), ordered_checks)

    def gate(self, report: HealthReport) -> None:
        if not report.passed:
            failed = ", ".join(check.name for check in report.checks if not check.passed)
            raise RuntimeError(f"production health gate blocked: {failed}")
