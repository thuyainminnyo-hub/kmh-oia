# SEC-04 / SEC-05 Remediation Design V1

Status: DESIGN ONLY — implementation not authorized.
Repository: thuyainminnyo-hub/kmh-oia
Base: main @ 132d6a09a6b91030835c07e5ff129eeeb79c4fba
Branch: security/sec04-sec05-remediation-v1-2026-11-06
Scope: SEC-04 input boundary; SEC-05 execution deadline/resource controls.
Constraints: synthetic-only; disposable branch; preserve existing branches and PRs; no merge, deployment, production execution, or changes to runtime source.

## Decision record

This approval authorizes design artifacts only. It does not authorize source-code implementation, dependency changes, CI workflow changes, secrets, production access, or external side effects. Proposed defaults below are provisional and require owner review before implementation.

## SEC-04 — Input boundary

### Design
- Validate the request before context assembly, serialization, persistence, or agent invocation.
- Enforce both Unicode character count and UTF-8 encoded byte count on the canonical decoded string.
- Provisional limits: 32,768 Unicode code points and 65,536 UTF-8 bytes. These are design defaults, not production-approved limits.
- Reject empty and whitespace-only input.
- Reject malformed text encoding at the transport boundary; do not silently repair invalid byte sequences.
- Apply consistent normalization only if the product contract requires it; normalization must be specified before measuring the canonical value.
- Do not log raw rejected payloads. Emit bounded metadata: request correlation ID, observed byte/character counts, configured limit, rejection reason, and timestamp.
- Ensure rejection occurs before ContextAssembly and before any tool/agent execution.
- Treat structured payload limits (nesting depth, arrays, object fields) as a separate parser-boundary requirement if/when structured input is accepted.

### Acceptance criteria
1. At-limit input is accepted.
2. One-character and one-byte-over-limit cases are rejected deterministically.
3. Unicode multibyte input is measured consistently in characters and bytes.
4. Empty/whitespace-only and malformed transport encoding are rejected.
5. Oversized input does not reach context assembly, agent, tool executor, state mutation, or external adapters.
6. Logs contain no raw payload or secrets.
7. Validation behavior is deterministic and documented.

## SEC-05 — hard execution deadline and resource controls

### Design
- Do not rely on checking elapsed time only before/after a synchronous call.
- Run untrusted or potentially blocking work behind an isolated worker/process boundary.
- Parent supervisor owns the deadline and worker lifecycle; worker cannot extend its own deadline.
- On deadline: request graceful termination, wait a bounded grace interval, then force terminate/kill and reap the process. Verify no child process remains.
- Use bounded IPC messages and bounded stdout/stderr capture; avoid unbounded buffering.
- Define configurable per-task wall-clock deadline, concurrency cap, and (where supported) CPU/memory/process limits. Values remain unset pending workload profiling and owner approval.
- Propagate cancellation and ensure no automatic retry for unknown/non-idempotent external side effects.
- Record worker start/end, deadline, exit status, termination reason, resource-limit outcome, and correlation IDs without recording secrets.
- Treat process creation latency and platform-specific process-tree cleanup as explicit limitations; use process groups/job objects or platform-equivalent controls where required.
- Do not claim hard CPU/memory isolation unless enforced by OS/container controls and verified on the target platform.

### Acceptance criteria
1. Normal synthetic worker completes and returns a bounded result.
2. Hung/infinite-loop worker is terminated by supervisor deadline.
3. Child process is reaped; no orphan/zombie remains.
4. Cancellation stops work within documented bounds.
5. Worker crash and malformed/oversized IPC fail closed.
6. Concurrency/resource limits are enforced or explicitly reported unsupported on the target platform.
7. Timeout does not trigger blind retry of a side-effecting operation.
8. Evidence is sufficient to independently reconstruct the worker lifecycle.

## Threats and residual risks
- Character count and byte count differ for multibyte Unicode.
- A process boundary alone is not a complete CPU/memory sandbox.
- Killing a worker cannot reverse external side effects already committed.
- Process-tree termination differs across operating systems.
- Timeout guarantees exclude platform process-creation delays unless separately bounded.
- Logging and telemetry can themselves become resource-exhaustion or data-leak surfaces.

## Rollback
- All design and future implementation work remains on the disposable branch.
- Revert only commits on this branch; never reset or force-push main or existing feature branches.
- If tests fail, stop, preserve artifacts, record failure, and do not merge/deploy.
- External side effects are out of scope; if accidentally observed in a future test, halt and require owner-led reconciliation.

## Governance gates
1. Owner approves design and provisional limits.
2. Implementation approval is separately obtained.
3. Synthetic tests run in isolated environment.
4. Independent reviewer verifies source diff, test output, and evidence manifest.
5. Human approval required before any merge; deployment requires a separate authorization.
