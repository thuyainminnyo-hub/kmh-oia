# Local Production Audit Sink

Status: PILOT IMPLEMENTATION; exact-head CI is tracked on P0-E PR #238

`JsonlProductionAuditSink` writes `evidence_created` and `qa_decision_recorded`
events to a local JSONL file. Each event contains a timestamp, job ID, payload,
previous-event hash, and its own SHA-256 event hash. `verify_chain()` validates
the file's JSON shape, event hashes, and previous-hash links.

## Important security boundary
- Hash chaining detects changes if a trusted expected chain head is retained separately.
- A local JSONL file is not immutable storage; someone who can rewrite the whole file can rebuild the chain.
- No digital signature, external log sink, access control, multi-process locking, retention policy, or backup is provided.
- Public QA-decision recording requires a short-lived HMAC reviewer assertion, validates the required role and consumes its nonce in a durable SQLite replay store. The audit event's reviewer_id is derived from the verified subject. The assertion issuer itself is not an external identity provider; real human identity depends on upstream issuer authentication and key custody.
- Evidence records are separate from actual model execution and do not prove visual quality.

## Verification
```bash
python -m unittest tests.test_production_audit -v
python -m unittest discover -s tests -v
```
