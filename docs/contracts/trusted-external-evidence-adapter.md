# Trusted External Evidence Adapter — Implementation Contract

Status: NEXT IMPLEMENTATION TASK / DESIGN CONTRACT

## Goal
Replace caller-supplied claims with a trusted adapter that obtains and validates source receipts before external outcome evidence can be admitted.

## Required interface
Define a provider adapter contract with:
- `provider_name`
- `fetch_receipt(source_record_id)`
- `verify_receipt(receipt)`
- `match_execution(receipt, execution_id)`
- `normalize_observation(receipt)`

The adapter must return a typed result. A record is eligible for learning admission only when:
1. A provider-side receipt is fetched by the generic `TrustedSourceReceiptVerifier` through an allowlisted, configured adapter.
2. The adapter's receipt authenticity/integrity check passes according to the provider's supported mechanism (for example, signed webhook verification, authenticated API response plus provider record lookup, or another documented method).
3. The receipt's stable provider record ID is preserved.
4. The evidence explicitly references the KMH OIA `execution_id`, or a versioned attribution record explains the linkage.
5. The raw provider observation is stored separately from interpretation.
6. The admission decision and reason are audit logged with a trace ID.

## Fail-closed rules
- Missing provider credentials/configuration: NOT_ADMITTED.
- Provider unreachable or timeout: NOT_ADMITTED; retry status may be recorded separately.
- Invalid signature or receipt: NOT_ADMITTED.
- Unknown provider/source: NOT_ADMITTED.
- No attributable execution ID: NOT_ADMITTED.
- Caller-supplied booleans alone never authenticate a source.
- A successful internal QA result is not a substitute for an external receipt.
- Admission does not mean rule change is auto-applied; changes still pass the governance/experiment path.

## Security boundaries
- Keep credentials in a secret manager; never commit secrets.
- Allowlist provider hosts and record types to reduce SSRF and source-confusion risk.
- Use timeouts, bounded retries, idempotency keys, and replay protection where supported.
- Record provider, timestamp, record ID, verification method/version, and content hash for auditability.
- Do not claim cryptographic verification where the provider offers no verifiable mechanism.

## Implementation sequence
1. Add provider-adapter protocol and typed `TrustedSourceReceipt` / `ReceiptVerificationResult`.
2. Implement one provider-specific adapter only after the source is selected and credentials/API contract are available.
3. Add fake-adapter tests for valid receipt, invalid signature, missing attribution, timeout, replay, and unknown provider.
4. Replace boolean admission inputs with verifier-produced result in the runtime bridge.
5. Run all unit tests and repository validation; review actual CI logs.
6. Keep `EXEC-SUN-TRAVEL-005` on HOLD until a genuine measurement source is selected and verified.

## Current repository boundary
A generic `TrustedSourceReceiptVerifier` protocol and deterministic fake-adapter tests exist. The runtime can call an injected adapter and the gate admits only when the verifier result passes. No real provider-specific adapter, production credentials, or provider API integration exists yet. Fake-adapter tests validate code paths, not an actual provider's authenticity mechanisms. The `source_authenticated` and `attribution_verified` runtime arguments are retained only for compatibility and are ignored as proof.
