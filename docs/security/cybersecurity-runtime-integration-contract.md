# Cybersecurity Registry ↔ Live Runtime Integration Contract

**Status:** Partial pilot implementation — not production-ready.  
**Applies to:** cybersecurity registry, command metadata resolver adapter, runtime guard, and `src/live_runtime_bridge.py`.  
**Release posture:** HOLD until the acceptance criteria below are implemented and independently verified.

## Current verified boundary

The cybersecurity registry exposes `authorize_execution(record, action)` and `run_authorized_action(record, action, executors)`. The latter checks an action-to-executor mapping and authorization before invoking its selected callable. The local JSONL registry is a pilot adapter, not tamper-proof/WORM storage.

`LiveRuntimeBridge.execute()` checks commands explicitly classified as `cybersecurity_remediation` before normal state transitions. A missing or denying guard blocks the command; even when the guard allows it, the bridge raises a `PermissionError` until a dedicated asset-scoped remediation executor is configured. The generic OIA/LLM runtime is not called for that cybersecurity command path. Non-cybersecurity commands retain the general runtime path.\n\n`src/cybersecurity_command_metadata.py` now provides a typed resolver adapter that checks metadata shape and binds its command ID to the console command ID. This is only a contract/helper: the metadata provider must still be implemented by trusted application code using authenticated server-side context. The adapter itself does not authenticate metadata, compare all asset/approval fields against a registry record, or enable execution.

## Required integration boundary

1. **Explicit action classification.** A command may enter the cybersecurity guard only when a trusted runtime component classifies it as a supported security-sensitive action. Do not infer an actionable remediation solely from free-form objective text.
2. **Trusted record resolution.** The typed resolver adapter is available, but the trusted metadata provider and its authenticated server-side source are not yet wired into the live runtime. Resolve the assessment record from a trusted registry/repository using an immutable record reference or version. Do not accept a caller-supplied record as proof of its own authority.
3. **Validate before side effects.** Validate the complete record against the canonical schema, then verify source evidence, applicability, decision, asset identity, owner, exact approval scope, approval time window, and rollback plan before transitioning the command to an executable state or invoking an executor.
4. **Fail closed.** Missing registry records, schema failures, unverifiable sources, unknown applicability, `hold`, unsupported actions, mismatched asset/action scope, expired approvals, and missing executors must block execution without invoking any executor.
5. **Trusted executor registry.** Action-to-executor mappings must be constructed by trusted application code, not request data. Each executor must independently enforce least-privilege access to the approved asset. A Python dictionary alone is not a trust boundary.
6. **Preserve non-security workflows deliberately.** Define which commands require this guard. Do not silently treat every general OIA console command as a cybersecurity remediation, and do not imply that unrelated commands are security-gated unless the policy explicitly requires it.
7. **Audit the decision and outcome.** Emit an append-only audit event linking registry record/version, asset, requested action, approval/approver, command ID, execution ID, executor identity, decision/reason, timestamps, and outcome/evidence references. Record denials as well as successful calls. Do not store secrets in audit events.
8. **Independent outcome QA.** A successful executor return is not proof that remediation succeeded. Require before/after evidence and an independent verification step before marking the execution as successful or admitting learning.

## Acceptance criteria

- [x] Current guard tests cover a missing/denying registry record and verify the generic runtime is not called.\n- [ ] A security-sensitive command with no registry record is blocked before runtime/executor side effects in the full production-integrated path.
- [ ] A schema-invalid or tampered record is blocked and its executor is not called.
- [ ] Pending, denied, expired, future-dated, or out-of-scope approval is blocked.
- [ ] Unknown applicability and `hold` are blocked even if an executor exists.
- [ ] A different asset or action cannot reuse an approval.
- [ ] An unregistered/non-callable executor is blocked.
- [ ] A valid, unexpired, exact-scope approval calls only the registered executor for that action and asset.
- [ ] Denial and execution outcomes are correlated to command/execution IDs in audit evidence.
- [x] Current integration tests exercise `LiveRuntimeBridge.execute()` and assert the generic runtime spy is not called for a denied cybersecurity command.\n- [ ] Full production-integrated tests cover authenticated metadata provider, asset-scoped executor, durable audit, idempotency, and independent outcome verification.
- [ ] Existing non-security runtime tests remain green and command policy is explicit.
- [ ] Independent reviewer inspects code, tests, CI and audit evidence before the PR leaves Draft.
- [ ] Production storage, concurrent writes, retention, secret handling, access controls, and tamper-evident/WORM requirements are assessed separately.

## Verification rule

Passing schema QA and unit tests proves only those checked properties at the tested commit. It does not prove production enforcement, external CVE validity, remediation, or production readiness. Keep PR and release status on HOLD until the integration acceptance criteria are met.
