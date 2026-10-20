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
