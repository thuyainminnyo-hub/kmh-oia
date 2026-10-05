"""Deterministic bridge from a KMH Reel production job to the OIA runtime."""

from dataclasses import dataclass

from src.main import run


@dataclass(frozen=True)
class ReelProductionJob:
    run_id: str
    topic: str
    platform: str = "Facebook Reels"
    duration_seconds: int = 55
    aspect_ratio: str = "9:16"
    script_version: str = "v1.0"


@dataclass(frozen=True)
class ReelExecutionResult:
    run_id: str
    response: str
    stages: list[str]
    trace_event_count: int


def execute_reel_job(job: ReelProductionJob) -> ReelExecutionResult:
    if not job.run_id.strip():
        raise ValueError("run_id must not be empty")
    if not job.topic.strip():
        raise ValueError("topic must not be empty")
    if job.platform != "Facebook Reels":
        raise ValueError("unsupported platform")
    if job.duration_seconds < 15 or job.duration_seconds > 90:
        raise ValueError("duration_seconds must be between 15 and 90")
    if job.aspect_ratio != "9:16":
        raise ValueError("aspect_ratio must be 9:16")

    goal = (
        f"Execute Reel production job {job.run_id}: "
        f"topic={job.topic}; platform={job.platform}; "
        f"duration={job.duration_seconds}s; aspect_ratio={job.aspect_ratio}; "
        f"script_version={job.script_version}"
    )
    response, trace = run(goal, session_id=job.run_id)
    return ReelExecutionResult(
        run_id=job.run_id,
        response=response,
        stages=trace.stages,
        trace_event_count=len(trace.events),
    )
