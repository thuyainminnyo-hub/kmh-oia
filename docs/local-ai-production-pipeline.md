# Production Execution → Evidence → Audit Pipeline

Status: IMPLEMENTED ON PILOT BRANCH; CI FOR THIS REVISION PENDING

`execute_with_evidence` composes the existing execution bridge, output-root
verification, SHA-256 evidence manifest, and JSONL audit sink. A verified
execution returns a `qa_pending` job with evidence and an `evidence_created`
audit event. Failed execution does not create evidence. Evidence/audit errors
fail the job closed rather than returning a successful pipeline result.

This remains a pilot orchestration helper. It does not invoke a real model on
its own, perform semantic/visual QA, authenticate reviewers, or provide
tamper-proof remote storage. Provider execution IDs must be supplied by the
caller; no live ComfyUI ID is fabricated.

Run:
```bash
python -m unittest tests.test_production_pipeline -v
python -m unittest discover -s tests -v
```
