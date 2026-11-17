# P0-E — Independent Trust & Runtime Assurance

Status: IMPLEMENTED ON FEATURE BRANCH; CI PENDING; NOT PRODUCTION READY

## Scope delivered in this implementation slice

This branch adds a small, testable trust foundation:

1. Short-lived reviewer assertions authenticated with HMAC-SHA256.
2. Issuer, audience, key ID, expiry, future-issued, role and signature checks.
3. Durable single-host SQLite nonce claims to reject assertion replay.
4. An authenticated QA helper that derives reviewer_id from the verified assertion rather than a caller-supplied identity string.
5. HMAC-authenticated audit checkpoints retained in a separate SQLite trust ledger.
6. Checkpoint verification binds the independently retained sequence and audit-chain head to the locally supplied verified event list.
7. Health checks for the reviewer replay and checkpoint stores.

## Trust model and limitations

- HMAC is a shared-secret MAC, not an asymmetric digital signature. Every verifier holding the secret can also mint assertions/checkpoints.
- Keys must be provisioned outside the repository and outside the local audit directory. Do not store keys in source, JSONL, SQLite, CI logs, or PR artifacts.
- Key custody, rotation, revocation, KMS/HSM integration and production secret delivery are not implemented.
- SQLite stores are single-host primitives. Multi-host operation requires a shared transactional database with equivalent unique-key and monotonic-sequence guarantees.
- The checkpoint database is a separate trust boundary only when its access controls, backup and administration are independent of the audit file. A local file beside the audit log does not provide independent retention.
- The checkpoint verifier must receive events obtained from a successful audit-chain verification. A checkpoint anchors the chain head and event count; it does not authenticate the source runtime or prove visual quality.
- Reviewer assertions are an application-level authentication mechanism. They do not establish a human's identity unless the assertion issuer itself is securely authenticated and governed.
- The authenticated QA helper consumes a nonce before writing the QA event. If the append fails, issue a new assertion; do not reuse the consumed token.
- No existing production route has been silently changed to require this new authentication helper. Integration into deployment identity, real reviewer login and production QA workflow remains a separate rollout.
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
