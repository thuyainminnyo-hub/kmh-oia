# KMH OIA

Operating Intelligence Architecture — executable runtime and integration system.

## Runtime path

`User Goal → Input Gateway → OIA Core → Context Assembly → Workflow → Agent → State → Tool Security → Governed Tool → Evaluation → Response → Trace`

The runtime exposes replaceable boundaries for state, governed-tool execution, agent decisions, evaluation, response rendering, and structured tracing. The default implementations remain deterministic and local.

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

## Trace / observability

`Tracer` is the runtime observability boundary. `InMemoryTracer` is the default deterministic implementation and retains ordered `TraceEvent` records. A compatible tracer can be injected through `run(..., tracer=...)` or `OIARuntime(..., tracer=...)`.

No external telemetry backend is required by the current runtime.
