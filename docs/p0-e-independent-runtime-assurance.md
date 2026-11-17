# P0-E — Independent Trust & Runtime Assurance

Status: IMPLEMENTED ON FEATURE BRANCH; EXACT-HEAD CI MUST BE RECONFIRMED AFTER HARDENING; NOT PRODUCTION READY

## Scope delivered in this implementation slice

This branch adds a small, testable trust foundation:

1. Short-lived reviewer assertions authenticated with HMAC-SHA256.
2. Issuer, audience, key ID, expiry, future-issued, role and signature checks.
3. Durable single-host SQLite nonce claims to reject assertion replay.
4. The production JSONL audit sink now requires a verified, one-time reviewer assertion for public QA-decision recording; the recorded reviewer_id is derived from the authenticated subject.
5. HMAC-authenticated audit checkpoints retained in a separate SQLite trust ledger.
6. Checkpoint creation and verification recompute every JSONL event hash and previous-hash link before accepting the independently retained sequence, event count and chain head.
7. Health checks for the reviewer replay and checkpoint stores.

## Trust model and limitations

- HMAC is a shared-secret MAC, not an asymmetric digital signature. Every verifier holding the secret can also mint assertions/checkpoints.
- Keys must be provisioned outside the repository and outside the local audit directory. Do not store keys in source, JSONL, SQLite, CI logs, or PR artifacts.
- Key custody, rotation, revocation, KMS/HSM integration and production secret delivery are not implemented.
- SQLite stores are single-host primitives. Multi-host operation requires a shared transactional database with equivalent unique-key and monotonic-sequence guarantees.
- The checkpoint database is a separate trust boundary only when its access controls, backup and administration are independent of the audit file. A local file beside the audit log does not provide independent retention.
- Checkpoint creation and verification validate the full event hash chain themselves. A checkpoint anchors the chain head and event count; it does not authenticate the source runtime or prove visual quality.
- Reviewer assertions are an application-level authentication mechanism. They do not establish a human's identity unless the assertion issuer itself is securely authenticated and governed.
- The authenticated QA helper consumes a nonce before writing the QA event. If the append fails, issue a new assertion; do not reuse the consumed token.
- The local production JSONL QA audit boundary now enforces the assertion contract. The upstream application/login route that issues reviewer assertions is not integrated; until a trusted issuer is connected, the pilot assertion issuer must remain an explicitly controlled service, not a user-facing identity system.
- No live ComfyUI execution, external identity-provider integration, asymmetric signing, independent remote/WORM retention, or production readiness is claimed.

## Required deployment controls before production

1. Select an identity provider and document how it authenticates the reviewer.
2. Provision separate HMAC keys through an approved secret manager; establish rotation and revocation.
3. Place checkpoint/replay databases under separately administered storage and define backup/restore and retention.
4. For multi-host use, replace local SQLite stores with a shared transactional implementation.
5. Integrate authenticated QA decisions into the actual runtime boundary; remove or restrict direct caller-supplied reviewer IDs.
6. Add operational monitoring, alerting, key compromise response and recovery drills.
7. Capture a genuine local ComfyUI execution using the real-execution runbook. CI tests are not runtime evidence.

## Verification

Run:

```bash
python -m unittest tests.test_trust_assurance -v
python -m unittest discover -s tests -v
```

CI results must be checked against the exact final PR head. Passing fake-adapter/unit tests does not prove a real provider, reviewer identity provider, or ComfyUI instance was exercised.

## Release gate

P0-E remains HOLD until independent review, exact-head CI, key-custody review, runtime integration evidence and Owner release approval are complete.
