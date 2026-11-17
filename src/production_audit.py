"""Local JSONL audit sink for provenance-bound production evidence."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from src.production_evidence import ProductionEvidence
AuditEventType = Literal["evidence_created", "qa_decision_recorded"]

class JsonlProductionAuditSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record_evidence(self, evidence: ProductionEvidence) -> dict:
        fields = ("adapter_name","output_path","output_sha256","output_size_bytes","elapsed_ms",
                  "provider_execution_id","snapshot_reference","artifact_id","execution_id",
                  "command_id","identity_key","verification_version","qa_decision")
        return self._append(event_type="evidence_created", job_id=evidence.job_id,
                            payload={name:getattr(evidence,name) for name in fields})

    def record_qa_decision(self, *, job_id: str, output_sha256: str,
                           decision: Literal["approved","rejected"], reviewer_id: str) -> dict:
        if not isinstance(job_id,str) or not job_id.strip(): raise ValueError("job_id must be a non-empty string")
        if not isinstance(output_sha256,str) or len(output_sha256)!=64 or any(c not in "0123456789abcdef" for c in output_sha256):
            raise ValueError("output_sha256 must be a lowercase SHA-256 digest")
        if decision not in {"approved","rejected"}: raise ValueError("QA decision must be approved or rejected")
        if not isinstance(reviewer_id,str) or not reviewer_id.strip(): raise ValueError("reviewer_id must be a non-empty string")
        matching_evidence = [
            event for event in self.verify_chain()
            if event.get("event_type") == "evidence_created"
            and event.get("job_id") == job_id
            and event.get("payload", {}).get("output_sha256") == output_sha256
        ]
        if not matching_evidence:
            raise ValueError("QA decision requires a prior evidence event matching job_id and output_sha256")
        evidence_event = matching_evidence[-1]
        evidence_payload = evidence_event["payload"]
        if any(
            event.get("event_type") == "qa_decision_recorded"
            and event.get("payload", {}).get("evidence_event_hash") == evidence_event["event_hash"]
            for event in self.verify_chain()
        ):
            raise ValueError("a QA decision is already recorded for this evidence event")
        return self._append(event_type="qa_decision_recorded",job_id=job_id,
                            payload={
                                "output_sha256":output_sha256,
                                "decision":decision,
                                "reviewer_id":reviewer_id,
                                "evidence_event_hash":evidence_event["event_hash"],
                                "snapshot_reference":evidence_payload["snapshot_reference"],
                                "execution_id":evidence_payload["execution_id"],
                                "identity_key":evidence_payload["identity_key"],
                            })

    def _append(self, *, event_type: AuditEventType, job_id: str, payload: dict) -> dict:
        previous_hash = "0"*64
        if self.path.exists() and self.path.stat().st_size: previous_hash=self.verify_chain()[-1]["event_hash"]
        event={"event_type":event_type,"job_id":job_id,"timestamp":datetime.now(timezone.utc).isoformat(),
               "previous_hash":previous_hash,"payload":payload}
        canonical=json.dumps(event,sort_keys=True,separators=(",",":"))
        event["event_hash"]=hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.path.open("a",encoding="utf-8") as stream: stream.write(json.dumps(event,sort_keys=True)+"\n")
        return event

    def verify_chain(self) -> list[dict]:
        if not self.path.exists(): return []
        events=[]; expected_previous="0"*64
        with self.path.open("r",encoding="utf-8") as stream:
            for line_number,line in enumerate(stream,start=1):
                try: event=json.loads(line)
                except json.JSONDecodeError as exc: raise ValueError(f"invalid JSONL audit event at line {line_number}") from exc
                if not isinstance(event,dict) or "event_hash" not in event: raise ValueError(f"invalid audit event at line {line_number}")
                recorded=event["event_hash"]; unhashed={k:v for k,v in event.items() if k!="event_hash"}
                calculated=hashlib.sha256(json.dumps(unhashed,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
                if recorded!=calculated: raise ValueError(f"audit event hash mismatch at line {line_number}")
                if event.get("previous_hash")!=expected_previous: raise ValueError(f"audit chain link mismatch at line {line_number}")
                expected_previous=recorded; events.append(event)
        return events
