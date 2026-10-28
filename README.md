# KMH OIA

Operating Intelligence Architecture — executable runtime and integration system.

## Runtime path

`User Goal → Input Gateway → OIA Core → Context Assembly → Workflow → Agent → State → Tool Security → Governed Tool → Evaluation → Response → Trace`

The runtime exposes replaceable boundaries for input gateway, OIA core, context assembly, workflow, agent decisions, state, security policy, governed-tool execution, evaluation, response rendering, and structured tracing. The default implementations remain deterministic and local.

## Run

```bash
python -m src.main "hello"
```

## Test

```bash
python -m unittest discover -s tests -v
```

## State

The default `StateStore` is in-memory and isolated by session ID.

For local durable state across process restarts, use `JsonFileStateStore`:

```python
from src.main import run
from src.state import JsonFileStateStore

state = JsonFileStateStore("runtime/state.json")
response, trace = run("hello", session_id="session-a", state=state)
```

The JSON-file store is a local persistence boundary for the current integration stage. It is not a substitute for a production database or distributed state backend.

## Security and governed tools

`SecurityPolicy` is the authorization boundary for governed tool calls. `ToolSecurityPolicy` is the default deterministic allowlist implementation. `ToolExecutor` is the execution boundary, with `ToolRegistry` providing the local `echo` implementation.

The current policy allows `echo` and rejects unlisted or empty tool names.

## Trace / observability

`Tracer` is the runtime observability boundary. `InMemoryTracer` is the default deterministic implementation and retains ordered `TraceEvent` records. A compatible tracer can be injected through `run(..., tracer=...)` or `OIARuntime(..., tracer=...)`.

No external telemetry backend is required by the current runtime.


## Controlled evidence and independent structural QA

The local runtime-to-evidence pilot can be run with:

```bash
python -m src.pilot "controlled pilot hello"
```

The pilot writes an inspectable JSON artifact and an `OBSERVED` EvidenceObject. It verifies that the persisted bytes can be read back with the same SHA-256 digest; that safeguard proves byte consistency at write/read time, not output truth or business quality.

The independent structural QA gate can be used from Python:

```python
from src.pilot import run_pilot
from src.qa_gate import evaluate_evidence, write_verdict

_, evidence, _ = run_pilot("controlled pilot hello")
verdict = evaluate_evidence(evidence, expected_output="controlled pilot hello")
write_verdict(verdict, "runtime/qa-verdicts.jsonl")
print(verdict.status, verdict.reason)
```

The QA verdict is a separate append-only JSONL record with per-check results and a digest of the inspected artifact. Missing/unreadable artifacts are `NOT_VERIFIED`; digest, provenance, structure, or explicit expected-output mismatches are `FAIL`; all performed checks passing yields `PASS`. A structural QA `PASS` does not independently assess semantic quality, prove a business outcome, authorize release, or promote the EvidenceObject from `OBSERVED`.

Before relying on a verdict for release, add independent reviewer identity/authorization and policy gates, verify the source revision against the actual runtime, and complete operational tests for concurrency, crash durability, backup/recovery, and tamper-evident storage. Production readiness remains **UNVERIFIED**.


## Release governance decision gate

A structural QA verdict alone is not release authorization. The controlled governance helper adds a separate fail-closed decision record:

```python
from src.governance_gate import decide_release, write_decision
from src.qa_gate import evaluate_evidence
from src.pilot import run_pilot

_, evidence, _ = run_pilot(
    "controlled release check",
    source_revision="<verified full source commit SHA>",
)
qa = evaluate_evidence(evidence, expected_output="controlled release check")
decision = decide_release(
    evidence,
    qa,
    expected_source_revision="<expected full source commit SHA>",
    actual_source_revision="<actual checkout commit SHA read from trusted runtime>",
    approval_id="<approval record ID>",
    approver_id="<authenticated reviewer ID>",
    approver_authorized=True,  # must come from a trusted identity/policy service
)
write_decision(decision, "runtime/release-decisions.jsonl")
print(decision.status, decision.reason)
```

The decision is `ALLOW` only when a PASS verdict refers to the same evidence, artifact/digest references exist, the evidence revision matches both the expected and actual runtime revision (and is not `unresolved`), and a named approver plus approval record are supplied with authorization. Any missing/mismatched gate yields `BLOCK`. The decision record is separate and does not promote EvidenceObject state.

**Important trust boundary:** this helper does not authenticate users, discover the live Git revision, or query an approval service itself. The caller must supply those values from trusted sources; a client-controlled `approver_authorized=True` is not authentication. This is a testable policy seam, not a deployed release enforcement point. Production readiness remains **UNVERIFIED**.


## Release enforcement adapter (controlled prototype)

The governance helper produces a decision record. A separate enforcement seam can be used at the point immediately before a protected action:

```python
from src.release_enforcer import require_release_allowed, ReleaseBlocked

# Obtain this decision from trusted, integrity-protected decision storage.
try:
    require_release_allowed(decision)
except ReleaseBlocked:
    # Abort release/deployment. Do not run the protected action.
    raise
# Invoke the protected action only after require_release_allowed returns.
```

The adapter raises when the decision is `BLOCK`, its input is not a ReleaseDecision, or its decision checks are empty or not all passing. Tests ensure a BLOCK decision raises before a sample protected-action marker can run.

This is still a local enforcement seam: it does not deploy, authenticate the decision author, verify a signature, or retrieve a tamper-protected decision from trusted storage. A production action must load the decision from trusted storage and enforce the gate in the deployment/job entrypoint with least privilege. A constructed `ALLOW` object alone is not trusted authorization.


## Release decision integrity envelope

`src/release_envelope.py` creates a stable JSON representation of a release-decision record and a SHA-256 digest, and verifies that a supplied envelope body matches the digest. This provides tamper detection when the trusted digest/envelope is separately protected.

```python
from src.release_envelope import create_envelope, verify_envelope

envelope = create_envelope(decision)
assert verify_envelope(envelope)
```

A plain checksum is **not** a signature: anyone who can change both the body and digest can recompute it. Therefore, the envelope must be stored in a trusted access-controlled system, or be signed with a key whose private component is unavailable to the decision writer. The current helper does not implement signatures or trusted storage.


## Verify decision envelope before enforcement

`src/trusted_release_gate.py` composes checksum verification with the fail-closed enforcer:

```python
from src.trusted_release_gate import require_trusted_release_allowed

# Load this envelope from trusted, access-controlled storage.
decision = require_trusted_release_allowed(envelope_dict)
```

It rejects envelopes whose decision body does not match the stored checksum, reconstructs the decision record, and then applies the release enforcement check. This still does not authenticate the issuer: trusted storage or a digital signature remains required. A checksum is integrity detection, not proof of who produced the decision.


## HMAC-authenticated release decision envelope

`src/signed_release_envelope.py` wraps the decision envelope checksum in HMAC-SHA256. The protected action path can require a valid HMAC before it enforces the release decision:

```python
from src.signed_release_envelope import require_signed_release_allowed

# Load a signed envelope from controlled storage.
# Obtain HMAC_KEY from a trusted secret manager; never hard-code it.
decision = require_signed_release_allowed(signed_envelope, HMAC_KEY)
```

The key must be supplied by a trusted secret manager or protected runtime configuration; do not commit it to source control, put it in the envelope, or log it. The verifier rejects missing/short keys, wrong-key signatures, envelope body changes, and non-ALLOW decisions.

**Security boundary:** HMAC authenticates the envelope relative to holders of the shared key. It does not establish independent reviewer identity if the same service can both approve and sign; it does not implement key rotation or hardware-backed protection. Production deployment must isolate signing authority, store keys outside the repository, and enforce this gate at the actual release entrypoint. Tests use a test-only key string and are not production key material.


### Key IDs and controlled rotation

HMAC envelopes now carry a non-secret `key_id`, and that ID is included in the signed material so it cannot be changed independently. The verifier can select an HMAC key from a caller-supplied keyring and enforce an allowlist of accepted key IDs:

```python
from src.signed_release_envelope import (
    sign_decision,
    require_release_allowed_with_keyring,
)

# keyring values must be loaded from a trusted secret manager, not hard-coded.
keyring = {"release-key-v2": active_key, "release-key-v1": retiring_key}
accepted_key_ids = {"release-key-v2", "release-key-v1"}  # explicit overlap window
signed = sign_decision(decision, active_key, key_id="release-key-v2")
allowed = require_release_allowed_with_keyring(signed, keyring, accepted_key_ids)

# After the migration window, remove release-key-v1 from accepted_key_ids.
```

Rotation policy is explicit: accept old and new IDs only during a reviewed overlap window; after retirement, remove the old ID from the accepted set so signatures using it fail closed. The implementation does not provide a secret manager, automatic rotation scheduler, key revocation feed, or production KMS integration. Key provisioning/retirement remain operator-controlled and must be audit logged.


## Key rotation audit trail (local prototype)

`src/key_rotation_audit.py` records `KEY_ACTIVATED`, `KEY_DEPRECATED`, and `KEY_RETIRED` events with key ID, actor ID, reason, accepted-key IDs, timestamp, sequence, previous hash, and entry hash. Before appending, the implementation validates the existing chain; the local JSONL write flushes and calls `fsync`. Any altered record or broken link is rejected.

```python
from src.key_rotation_audit import KeyRotationEvent, append_rotation_event, verify_rotation_audit

event = KeyRotationEvent.create(
    action="KEY_ACTIVATED",
    key_id="release-key-v2",
    actor_id="authenticated-operator-id",
    reason="planned rotation with temporary overlap",
    accepted_key_ids={"release-key-v1", "release-key-v2"},
    previous_active_key_id="release-key-v1",
)
append_rotation_event(event, "runtime/security/key-rotation-audit.jsonl")
assert verify_rotation_audit("runtime/security/key-rotation-audit.jsonl")
```

This hash chain is **tamper-evident, not tamper-proof**: an actor who can rewrite the entire local file can recompute the chain. Production must export events to independently retained, access-controlled audit storage and verify operator identity through a trusted service. Do not log key bytes, secret-manager payloads, or credentials in rotation events.


## Trusted HMAC key-provider boundary

`src/key_provider.py` defines the minimal `HMACKeyProvider` protocol: retrieve key bytes by key ID and expose the currently accepted key-ID set. The included `InMemoryKeyProvider` is for tests only; use a dedicated secret-manager/KMS adapter for production. `verify_with_provider` checks that the envelope key ID is accepted, obtains its key through the provider, and then verifies the HMAC and inner digest.

This separation allows the signing/verifying logic to remain stable as the underlying key service changes. It is not yet a production secret-manager integration and it does not provide key provisioning, rotation, revocation, or operator authentication. Never commit key material.


## Trusted key provider boundary

`src/trusted_key_provider.py` defines a small `TrustedKeyProvider` protocol for active signing-key and accepted verification-key retrieval. Its in-memory implementation is explicitly for controlled tests only. It supports explicit overlap and retirement policies and fails closed if the active key is unavailable or a retired key ID is not accepted.

A production adapter should implement this protocol using a trusted secret manager or KMS, enforce IAM, audit secret access, and never log key material. The repository does not yet contain a production secret-manager implementation; environment or local in-memory key sources must not be treated as production trust boundaries.


## Trusted key provider + signing integration (controlled prototype)

`src/key_provider_signing.py` combines the provider protocol with HMAC signing and enforcement:
- `sign_decision_with_provider(provider, decision)` requests the currently active key and refuses to sign if the provider cannot supply a key accepted by its own verification policy.
- `require_provider_signed_release_allowed(provider, signed)` resolves `key_id` through the provider's accepted-key policy and then verifies the HMAC/checksum before release enforcement.
- Retired, unknown, or unavailable keys fail closed.

The in-memory provider exists only for controlled tests. A production secret-manager/KMS adapter is still required; it must authenticate callers, enforce least privilege, audit key access, and avoid exposing key bytes. The shared-key HMAC design still does not provide non-repudiation: independent approval and signing authorities should be separated.


## Independent approval policy boundary

`src/approval_policy.py` defines an `ApprovalAuthority` protocol and a validation contract for approval records. Before the signing service treats an approval as valid, the policy check requires:
- a retrievable `APPROVE` record whose approval ID matches the requested ID;
- evidence ID, QA verdict ID, and source revision matching the reviewed release;
- a non-`unresolved` source revision;
- a policy ID in the explicitly accepted policy set;
- the approver to be different from the signing service identity; and
- positive authorization from the trusted identity/policy adapter.

The repository tests use a mock authority only. This code does not authenticate real users or connect to an approval database/identity provider. In production, the approval authority and key-signing service must be separate principals with least privilege; do not pass unverified caller booleans as proof of authorization.


## Release decision with independent approval authority

`src/approval_gated_release.py` composes the QA, source-revision and approval checks. It calls `ApprovalAuthority` to load an approval record tied to the exact evidence ID, QA ID, and source revision; it requires an accepted policy and an approver authorized by the trusted authority; and it rejects an approver who is the signing service identity. Any failed or unavailable check produces `BLOCK`.

```python
from src.approval_gated_release import decide_release_with_approval

decision = decide_release_with_approval(
    evidence,
    qa_verdict,
    expected_source_revision=expected_sha,
    actual_source_revision=runtime_sha,
    approval_authority=trusted_approval_authority,
    approval_id=approval_record_id,
    signing_service_id="service:release-signer",
    accepted_policy_ids={"release-policy:v1"},
)
```

The tests use a fake authority only. The real identity provider and approval storage are not integrated. Do not pass a client-controlled approval boolean as identity proof; the real authority must verify approver identity and policy independently.


## Verify source revision against the actual checkout

`src/source_revision.py` obtains the full commit SHA from `git rev-parse HEAD` and inspects `git status --porcelain`. It does not trust a revision string supplied by the request caller. The fail-closed helper only returns the SHA if the expected full SHA matches actual HEAD and the working tree has no modified or untracked files:

```python
from src.source_revision import require_verified_source_revision

actual_sha = require_verified_source_revision(
    expected_revision=reviewed_build_sha,
    root=".",
)
```

Tests create temporary Git repositories and cover matching clean HEAD, mismatched revision, modified/untracked files, invalid expected SHA, and a non-Git directory. This helper verifies the current checkout only; production must bind the expected SHA to the reviewed/build artifact and invoke the check in the same execution environment that produces the release.


## Release preflight with actual checkout verification

`src/release_preflight.py` composes actual Git checkout verification with the independent approval-gated decision path. It discovers HEAD itself, rejects a dirty checkout, verifies the expected reviewed full SHA, confirms the evidence's source revision matches that actual HEAD, and only then evaluates QA and the injected approval authority.

```python
from src.release_preflight import preflight_release

decision = preflight_release(
    evidence,
    qa_verdict,
    expected_source_revision=reviewed_build_sha,
    checkout_root=".",
    approval_authority=trusted_approval_authority,
    approval_id=approval_record_id,
    signing_service_id="service:release-signer",
    accepted_policy_ids={"release-policy:v1"},
)
```

The test suite creates temporary Git checkouts and exercises a clean matching release through HMAC signing/enforcement, then verifies dirty tree, wrong expected SHA, evidence/checkout revision mismatch, and missing approval fail closed. This remains a controlled integration prototype; the expected SHA must still come from a trusted reviewed build/deployment artifact, and the actual production entrypoint must enforce the resulting signed decision before performing the protected action.


## Protected action entrypoint (controlled integration prototype)

`src/protected_action.py` is the last guard before a protected callback. It resolves and verifies a signed release decision through the trusted-key-provider path; if signature/key policy verification fails or the decision is not `ALLOW`, it raises `ProtectedActionBlocked` before calling the action. Tests use a callback marker to prove that BLOCK, bad HMAC, retired-key, and provider-unavailable cases do not invoke the action.

```python
from src.protected_action import execute_protected_action, ProtectedActionBlocked

try:
    verified_decision, result = execute_protected_action(
        trusted_key_provider,
        signed_release_envelope,
        action=deploy_or_execute,
    )
except ProtectedActionBlocked:
    # Fail closed; protected callback was not invoked.
    raise
```

This remains a local adapter/test boundary, not a deployed CI/CD action. The production entrypoint must load signed decisions from trusted storage, use a production secret manager/KMS provider and independent approval authority, and enforce this check immediately before the protected action with least privilege.


## Single release-pipeline orchestration

`src/release_pipeline.py` connects the checkout preflight, QA/evidence checks, independent approval authority, HMAC signing through the key provider, and protected-action callback into one controlled path:

```python
from src.release_pipeline import execute_release_pipeline

decision, signed_envelope, result = execute_release_pipeline(
    evidence,
    qa_verdict,
    expected_source_revision=reviewed_build_sha,
    checkout_root=".",
    approval_authority=trusted_approval_authority,
    approval_id=approval_record_id,
    signing_service_id="service:release-signer",
    accepted_policy_ids={"release-policy:v1"},
    key_provider=trusted_key_provider,
    protected_action=deploy_or_execute,
)
```

The integration tests prove that a clean checkout, matching evidence revision, passing QA, and matching authorized independent approval can reach the callback; dirty checkout, wrong revision, evidence revision mismatch, or missing approval must prevent the callback. This test uses a fake approval authority and in-memory key provider. The production secret manager/KMS, real approval/identity service, trusted decision storage, and actual deployment entrypoint are still not integrated.


## Trusted key-provider interface

`src/key_provider.py` defines the interface between signing/release verification and a secret manager. The repository includes only `InMemoryKeyProvider` for deterministic tests; do not use it for live secrets.

A production adapter should implement `HMACKeyProvider` by reading key bytes from a trusted secret manager/KMS and return only the currently accepted key IDs. The provider exposes one active key ID for new signatures plus an accepted-key allowlist for verification during rotation.

```python
from src.key_provider import sign_with_provider, require_release_allowed_with_provider

# provider must be backed by a trusted secret manager/KMS in production.
signed = sign_with_provider(decision, provider)
# On the protected release path, load signed envelope from trusted storage.
verified_decision = require_release_allowed_with_provider(signed, provider)
```

Signing fails closed if there is no unambiguous active key, if that ID is not in the accepted set, or if the key is unavailable/too short. Verification fails closed for retired or unavailable keys and delegates the signed decision to the release enforcement gate.

**Still outstanding:** a real secret-manager/KMS adapter, identity-verified approver source, separation between approval authority and signing authority, key rotation/revocation audit integration, and a real deployment/job entrypoint. The provider interface alone does not make production releases protected.
