# EduAutomate Payment Record MVP — Local Smoke Test

Status: LOCAL PROTOTYPE CHECK ONLY — NOT A DEPLOYMENT OR BANK-SETTLEMENT TEST

This runbook is for a disposable local test using synthetic data only. It does not prove bank settlement, external evidence authenticity, a production deployment, or readiness to release. Do not use a real student's personal data, real bank slip, real payment details, or production secrets.

## 1. Prepare a disposable environment

From the repository root, use Python 3.12 and install the prototype requirements:

```bash
python --version
python -m pip install -r requirements-eduautomate-mvp.txt
```

Generate one-time development tokens in the current shell and use a temporary SQLite file outside the repository:

```bash
export EDUAUTOMATE_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export EDUAUTOMATE_ADMIN_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export EDUAUTOMATE_ADMIN_ACTOR_ID="local-smoke-admin"
SMOKE_DIR="$(mktemp -d)"
export EDUAUTOMATE_DB_PATH="$SMOKE_DIR/payments.sqlite3"
```

These tokens are for this local smoke test only. Never commit them, paste them into GitHub/Notion, or reuse them in production.

## 2. Start on localhost only

In the same shell:

```bash
uvicorn src.eduautomate_payment_api:app --host 127.0.0.1 --port 8000
```

Keep this process bound to `127.0.0.1`; do not change it to `0.0.0.0` or expose the port publicly. In a second terminal, set the three token/actor variables to the values from the first terminal and set `EDUAUTOMATE_DB_PATH` to the same temporary file path. Then run the following checks.

## 3. Check health and create one synthetic payment record

Health endpoint:

```bash
curl -fsS http://127.0.0.1:8000/healthz
```

Create a pending record with synthetic IDs and a placeholder integer amount. The meaning of `amount_minor` for MMK has not been approved; this value is **only a smoke-test fixture**, not a real currency amount:

```bash
IDEMPOTENCY_KEY="smoke-$(python -c 'import secrets; print(secrets.token_hex(12))')"
CREATE_BODY='{"student_id":"smoke-student-placeholder","amount_minor":100,"currency":"MMK","purpose":"smoke_test_only","execution_id":null}'
CREATE_RESPONSE="$(curl -fsS -X POST http://127.0.0.1:8000/v1/payments \
  -H "X-API-Token: $EDUAUTOMATE_API_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  --data "$CREATE_BODY")"
printf '%s\n' "$CREATE_RESPONSE"
PAYMENT_ID="$(printf '%s' "$CREATE_RESPONSE" | python -c 'import json,sys; print(json.load(sys.stdin)["payment_id"])')"
```

Expected: HTTP 201 and a payment response with `status: "pending"`. The `execution_id` is intentionally null so the test does not fabricate OIA execution attribution.

## 4. Confirm read-authentication and idempotency

A read request without the API token must return HTTP 401:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  "http://127.0.0.1:8000/v1/payments/$PAYMENT_ID"
```

Read with the token; expected HTTP 200:

```bash
curl -fsS "http://127.0.0.1:8000/v1/payments/$PAYMENT_ID" \
  -H "X-API-Token: $EDUAUTOMATE_API_TOKEN"
```

Repeat the create call from step 3 using the **same** `IDEMPOTENCY_KEY` and same `CREATE_BODY`. It should return the same `payment_id`. Reusing the key with a different payload should return HTTP 409.

## 5. Exercise the internal admin decision path (synthetic only)

This optional test records an internal admin decision on the synthetic record. The evidence reference below is a **fake test fixture**, not a bank slip or bank-confirmed transaction:

```bash
curl -fsS -X POST "http://127.0.0.1:8000/v1/payments/$PAYMENT_ID/admin-decision" \
  -H "X-Admin-Token: $EDUAUTOMATE_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"decision":"confirm","note":"Synthetic local smoke test only","evidence_reference":"smoke-test-fixture-only"}'
```

Expected: HTTP 200 and `status: "confirmed"` with the configured actor label. Here `confirmed` means only that this local prototype recorded an admin attestation. It is **not** external bank verification. The state transition is one-way in this prototype; repeating a decision for the same payment should return HTTP 409.

## 6. Stop and capture the result

- Stop Uvicorn with Ctrl+C.
- Record the smoke-test date/time, commit SHA, Python version, and pass/fail result in the implementation notes.
- Do not attach the temporary database, token values, real student information, or real bank documents to the repository.
- The disposable test directory may be removed after the server is stopped: `rm -rf "$SMOKE_DIR"`.

## What this does and does not prove

A successful local smoke test proves only that this prototype served requests against a temporary local SQLite file for the tested commit. It does not prove the intended production volume is mounted, that data persists after a production restart, that the admin's personal identity is independently authenticated, that any real payment settled, or that an external provider receipt is authentic.

The separate KMH OIA target-host replay runbook still requires the actual deployment host, intended persistent volume, a smoke report, UTC timestamp, and exact commit SHA. Keep `EXEC-SUN-TRAVEL-005` and the production release decision on HOLD until their own evidence requirements are independently satisfied.
