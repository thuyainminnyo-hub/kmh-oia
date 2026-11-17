"""Local JSONL audit sink for provenance-bound production evidence."""
from __future__ import annotations
import hashlib
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from src.production_evidence import ProductionEvidence
from src.verified_snapshot_store import VerifiedArtifactStore, VerifiedSnapshot

AuditEventType = Literal["evidence_created", "qa_decision_recorded"]


class JsonlProductionAuditSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    @contextmanager
    def _exclusive_lock(self):
        """Serialize read/validate/append transactions across threads and processes."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as lock_stream:
            if os.name == "nt":
                import msvcrt
                lock_stream.seek(0, os.SEEK_END)
                if lock_stream.tell() == 0:
                    lock_stream.write(b"\0")
                    lock_stream.flush()
                lock_stream.seek(0)
                msvcrt.locking(lock_stream.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    lock_stream.seek(0)
                    msvcrt.locking(lock_stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)

    def record_evidence(self, evidence: ProductionEvidence, *, snapshot_store: VerifiedArtifactStore) -> dict:
        if not isinstance(evidence, ProductionEvidence):
            raise TypeError("evidence must be a ProductionEvidence")
        if not isinstance(snapshot_store, VerifiedArtifactStore):
            raise TypeError("snapshot_store must be a VerifiedArtifactStore")
        reference = VerifiedSnapshot(
            artifact_id=evidence.artifact_id,
            sha256=evidence.output_sha256,
            size_bytes=evidence.output_size_bytes,
            storage_key=evidence.snapshot_reference,
            verification_version=evidence.verification_version,
        )
        # Never audit a manifest merely because its fields are self-consistent:
        # verify its metadata and blob against the trusted snapshot store first.
        snapshot_store.verify(reference)
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
        # The lookup, duplicate check, and append are one cross-process transaction.
        with self._exclusive_lock():
            events = self._verify_chain_unlocked()
            matching_evidence = [
                event for event in events
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
                for event in events
            ):
                raise ValueError("a QA decision is already recorded for this evidence event")
            return self._append_unlocked(
                event_type="qa_decision_recorded", job_id=job_id,
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
        with self._exclusive_lock():
            return self._append_unlocked(event_type=event_type, job_id=job_id, payload=payload)

    def _append_unlocked(self, *, event_type: AuditEventType, job_id: str, payload: dict) -> dict:
        events = self._verify_chain_unlocked()
        previous_hash = events[-1]["event_hash"] if events else "0"*64
        event={"event_type":event_type,"job_id":job_id,"timestamp":datetime.now(timezone.utc).isoformat(),
               "previous_hash":previous_hash,"payload":payload}
        canonical=json.dumps(event,sort_keys=True,separators=(",",":"))
        event["event_hash"]=hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        # A single encoded write while holding the lock prevents interleaved JSONL records.
        line = json.dumps(event,sort_keys=True)+"\n"
        with self.path.open("a",encoding="utf-8") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        return event

    def verify_chain(self) -> list[dict]:
        with self._exclusive_lock():
            return self._verify_chain_unlocked()

    def _verify_chain_unlocked(self) -> list[dict]:
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
