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
