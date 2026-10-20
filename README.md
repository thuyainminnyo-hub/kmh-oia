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
