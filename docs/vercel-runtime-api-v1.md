# KMH OIA — Vercel Runtime API v1

Status: IMPLEMENTED ON A FEATURE BRANCH; CI AND DEPLOYMENT NOT YET VERIFIED

## Purpose

Expose a small HTTP boundary for the existing deterministic KMH OIA Python runtime. This is a preview/integration surface, not a production release and not a remote ComfyUI, image-generation, CAD, or manufacturing executor.

## Deployment

Vercel detects FastAPI applications from a supported Python entrypoint. This project exports `app` from `src/index.py` and pins the Python runtime at `3.12`.

The FastAPI dependency is pinned in `requirements.txt`. Vercel's Python runtime serves the application as a Function; no custom web server or shell process is started by the application.

## Routes

| Method | Route | Purpose | Access |
|---|---|---|---|
| GET | `/health` | Liveness response | Public; no secret data |
| GET | `/ready` | Safe readiness/configuration facts | Public; no secret values |
| POST | `/v1/executions` | Restricted deterministic runtime call | API key + explicit feature flag |

The execution request accepts:
- `goal`: non-empty text, maximum 4,000 characters
- `session_id`: optional, maximum 128 characters
- `tool_name`: exactly `echo`

Unknown fields and other tool names are rejected. The endpoint does not expose shell, network, ComfyUI, provider, or production adapters.

## Required environment variables

- `KMH_OIA_API_KEY`: secret used by the `X-KMH-OIA-API-Key` request header.
- `KMH_OIA_EXECUTION_ENABLED`: explicit feature flag; unset/false by default.

The feature gate cannot open without both a configured API key and `KMH_OIA_EXECUTION_ENABLED=true`. The secret is never included in health/readiness responses or returned errors. The key is compared using constant-time comparison.

Configure environment variables in the Vercel project settings; never commit them to Git. Keep the execution flag disabled for the first deployment. Add a restricted key only after the deployment owner has reviewed the preview access model.

## State and evidence boundary

- Each request calls the existing deterministic runtime with request-local in-memory state.
- This API does not provide durable state, cross-instance idempotency, event persistence, or a tamper-evident audit ledger.
- The response includes a generated execution identifier and the existing runtime trace events. Those events are response evidence, not independently immutable audit records.
- No external tool or provider side effect is reachable through this route.
- `/ready` reports `production_release_authorized=false` by design.

## Verification

Run locally with Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m unittest tests.test_vercel_runtime_api -v
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

Then deploy as a Vercel Preview and verify:
1. `GET /health` returns HTTP 200.
2. `GET /ready` reports a closed execution gate.
3. `POST /v1/executions` without a configured key is rejected.
4. With a configured key but no feature flag, the endpoint remains disabled.
5. Only after explicit owner-controlled enablement does the echo-only deterministic route execute.

## Release gates still open

- Full repository tests and validation on the exact commit.
- Vercel Preview build and HTTP smoke tests.
- Authentication/rate-limit and abuse review.
- Durable event ledger and shared-store idempotency.
- Human approval and explicit production release.
- Independent real-runtime / provider evidence for any external execution claim.

Production remains HOLD until those gates are independently evidenced.
