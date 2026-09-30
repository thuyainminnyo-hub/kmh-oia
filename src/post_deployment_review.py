"""Stage 14 deterministic post-deployment review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PostDeploymentReview:
    deployment_id: str
    phase: str
    validated: bool
    findings: tuple[str, ...]
    reason: str = ""


class PostDeploymentReviewController:
    """Review explicitly supplied deployment evidence without fabricating production facts."""

    REQUIRED_EVIDENCE = (
        "deployment",
        "configuration",
        "health",
        "telemetry",
        "stability",
        "rollback",
        "change_control",
    )

    def start(self, *, deployment_id: str) -> PostDeploymentReview:
        if not deployment_id.strip():
            raise ValueError("deployment_id is required")
        return PostDeploymentReview(deployment_id.strip(), "started", False, ())

    def review(self, state: PostDeploymentReview, *, evidence: dict[str, str], findings: tuple[str, ...] = ()) -> PostDeploymentReview:
        if state.phase != "started":
            raise RuntimeError("review requires started state")
        missing = tuple(name for name in self.REQUIRED_EVIDENCE if not isinstance(evidence.get(name), str) or not evidence.get(name, "").strip())
        normalized_findings = tuple(item.strip() for item in findings if item.strip())
        if missing:
            return PostDeploymentReview(state.deployment_id, "blocked", False, normalized_findings, "missing required evidence: " + ", ".join(missing))
        return PostDeploymentReview(state.deployment_id, "reviewed", True, normalized_findings, "deployment evidence reviewed")

    def validate(self, state: PostDeploymentReview) -> None:
        if state.phase != "reviewed" or not state.validated:
            raise RuntimeError("post-deployment review is not validated")
