"""Local JSONL audit sink for production evidence and QA decisions.

Hash chaining detects edits if the expected chain head is retained independently.
This is not a signed or tamper-proof remote audit service.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.production_evidence import ProductionEvidence

AuditEventType = Literal["evidence_created", "qa_decision_recorded"]


class JsonlProductionAuditSink:
    """Persist ordered, hash-chained audit events to a local JSONL file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record_evidence(self, evidence: ProductionEvidence) -> dict:
        return self._append(
            event_type="evidence_created",
            job_id=evidence.job_id,
            payload={
                "adapter_name": evidence.adapter_name,
                "output_path": evidence.output_path,
                "output_sha256": evidence.output_sha256,
                "output_size_bytes": evidence.output_size_bytes,
                "elapsed_ms": evidence.elapsed_ms,
                "provider_execution_id": evidence.provider_execution_id,
                "qa_decision": evidence.qa_decision,
            },
        )

    def record_qa_decision(
        self, *, job_id: str, output_sha256: str,
        decision: Literal["approved", "rejected"], reviewer_id: str,
    ) -> dict:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string")
        if not isinstance(output_sha256, str) or len(output_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in output_sha256
        ):
            raise ValueError("output_sha256 must be a lowercase SHA-256 digest")
        if decision not in {"approved", "rejected"}:
            raise ValueError("QA decision must be approved or rejected")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            raise ValueError("reviewer_id must be a non-empty string")
        return self._append(
            event_type="qa_decision_recorded",
            job_id=job_id,
            payload={
                "output_sha256": output_sha256,
                "decision": decision,
                "reviewer_id": reviewer_id,
            },
        )

    def _append(self, *, event_type: AuditEventType, job_id: str, payload: dict) -> dict:
        previous_hash = "0" * 64
        if self.path.exists() and self.path.stat().st_size:
            previous_hash = self.verify_chain()[-1]["event_hash"]
        event = {
            "event_type": event_type,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": previous_hash,
            "payload": payload,
        }
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
        event["event_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def verify_chain(self) -> list[dict]:
        """Validate JSONL shape, event hashes, and previous-hash continuity."""
        if not self.path.exists():
            return []
        events: list[dict] = []
        expected_previous = "0" * 64
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL audit event at line {line_number}") from exc
                if not isinstance(event, dict) or "event_hash" not in event:
                    raise ValueError(f"invalid audit event at line {line_number}")
                recorded_hash = event["event_hash"]
                unhashed = {key: value for key, value in event.items() if key != "event_hash"}
                canonical = json.dumps(unhashed, sort_keys=True, separators=(",", ":"))
                calculated = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if recorded_hash != calculated:
                    raise ValueError(f"audit event hash mismatch at line {line_number}")
                if event.get("previous_hash") != expected_previous:
                    raise ValueError(f"audit chain link mismatch at line {line_number}")
                expected_previous = recorded_hash
                events.append(event)
        return events
