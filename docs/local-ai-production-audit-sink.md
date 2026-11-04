# Local Production Audit Sink

Status: IMPLEMENTED ON PILOT BRANCH; CI FOR THIS REVISION PENDING

`JsonlProductionAuditSink` writes `evidence_created` and `qa_decision_recorded`
events to a local JSONL file. Each event contains a timestamp, job ID, payload,
previous-event hash, and its own SHA-256 event hash. `verify_chain()` validates
the file's JSON shape, event hashes, and previous-hash links.

## Important security boundary
- Hash chaining detects changes if a trusted expected chain head is retained separately.
- A local JSONL file is not immutable storage; someone who can rewrite the whole file can rebuild the chain.
- No digital signature, external log sink, access control, multi-process locking, retention policy, or backup is provided.
- QA decision events record a reviewer identifier supplied by the caller; this helper does not authenticate that reviewer.
- Evidence records are separate from actual model execution and do not prove visual quality.

## Verification
```bash
python -m unittest tests.test_production_audit -v
python -m unittest discover -s tests -v
```
