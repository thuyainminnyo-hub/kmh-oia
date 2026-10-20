"""Connect a real KMH OIA runtime execution to inspectable evidence records.

This is a controlled local pilot, not a production evidence service. It persists
an output artifact and an OBSERVED evidence record for a successful runtime call.
A failed call is traced by the runtime but is not promoted to an output evidence
record by this pilot.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid

from src.evidence_object import EvidenceObject
from src.evidence_store import JsonlEvidenceStore
from src.main import run
from src.trace import InMemoryTracer


def run_pilot(
    goal: str,
    artifact_dir: str | Path = "runtime/pilot-artifacts",
    evidence_path: str | Path = "runtime/evidence.jsonl",
    session_id: str = "controlled-pilot",
) -> tuple[str, EvidenceObject, dict]:
    """Execute the runtime and persist the output, trace metadata, and evidence."""
    tracer = InMemoryTracer()
    output, trace = run(goal, session_id=session_id, tracer=tracer)
    tracer.validate_integrity()

    run_id = trace.events[0].metadata["request_id"]
    trace_id = trace.events[0].metadata["trace_id"]
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{run_id}.json"
    payload = {
        "run_id": run_id,
        "trace_id": trace_id,
        "session_id": session_id,
        "goal": goal,
        "output": output,
        "stages": trace.stages,
        "events": [asdict(event) for event in trace.events],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    artifact_path.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()

    evidence = EvidenceObject(
        evidence_id=f"evidence:{uuid.uuid4()}",
        kind="runtime_execution_output",
        source="kmh-oia",
        observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        scope="controlled-pilot",
        source_revision="working-tree-unresolved",
        artifact_ref=str(artifact_path),
        sha256_digest=digest,
        run_id=run_id,
        trace_id=trace_id,
        validation_state="OBSERVED",
    )
    JsonlEvidenceStore(evidence_path).append(evidence)
    return output, evidence, payload


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run one controlled KMH OIA evidence pilot.")
    parser.add_argument("goal")
    parser.add_argument("--artifacts", default="runtime/pilot-artifacts")
    parser.add_argument("--evidence", default="runtime/evidence.jsonl")
    args = parser.parse_args()
    response, evidence, _ = run_pilot(args.goal, args.artifacts, args.evidence)
    print(response)
    print(json.dumps(asdict(evidence), ensure_ascii=False, indent=2))
