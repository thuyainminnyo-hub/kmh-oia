# SEC-04 / SEC-05 Synthetic Regression Test Plan V1

Status: TEST PLAN ONLY — tests have not been executed.
Authorization: design-only approval; no runtime/source/test-code changes authorized.
Environment: disposable branch; synthetic data only.
Merge/deploy/production: prohibited.

## SEC-04 — Input boundary matrix

| ID | Synthetic input | Expected result | Required evidence |
|---|---|---|---|
| S04-01 | Empty string | Reject | exception/result and no downstream stage |
| S04-02 | Whitespace-only | Reject | exception/result and no downstream stage |
| S04-03 | Valid input below both limits | Accept | accepted character/byte counts |
| S04-04 | Exactly 32,768 Unicode code points and <=65,536 UTF-8 bytes | Accept | measured counts |
| S04-05 | 32,769 Unicode code points | Reject | measured count and reason |
| S04-06 | Exactly 65,536 UTF-8 bytes | Accept if character limit also passes | measured counts |
| S04-07 | 65,537 UTF-8 bytes | Reject | measured count and reason |
| S04-08 | Multibyte Unicode at byte boundary | Deterministic accept/reject per both limits | code-point and UTF-8 byte counts |
| S04-09 | Malformed transport byte sequence | Reject at transport decoder | decoder error; no repair |
| S04-10 | Oversized input | No ContextAssembly, Agent, Tool, State, or external adapter invocation | spy counters remain zero |
| S04-11 | Rejected payload contains synthetic secret marker | Do not log payload/marker | captured logs contain bounded metadata only |

## SEC-05 — Worker deadline/resource matrix

| ID | Synthetic worker behavior | Expected result | Required evidence |
|---|---|---|---|
| S05-01 | Finite quick worker | Complete | bounded result and lifecycle events |
| S05-02 | Sleep beyond deadline | Supervisor terminates worker | deadline, termination reason, exit status |
| S05-03 | Infinite loop | Worker terminated within defined tolerance | wall-clock timestamps |
| S05-04 | Cooperative cancellation | Stop within documented bound | cancellation propagation |
| S05-05 | Child process spawned then worker times out | Process tree cleaned/reaped | no remaining child PID |
| S05-06 | Worker crashes | Fail closed; no blind retry | exit code and error event |
| S05-07 | Oversized IPC/stdout/stderr | Reject/truncate safely within configured bound | observed byte counts |
| S05-08 | Concurrency cap exceeded | Reject/queue according to approved policy | active worker count |
| S05-09 | CPU/memory limit requested on unsupported platform | Explicitly report unsupported; do not claim isolation | platform capability record |
| S05-10 | Side-effecting operation times out | No automatic retry absent idempotency/compensation contract | retry count = 0 |
| S05-11 | Worker returns after deadline | Result discarded; timeout remains terminal | supervisor decision record |
| S05-12 | Repeated timeout/crash | Retry budget enforced; stop on exhaustion | attempt count and terminal state |

## Execution protocol

1. Obtain separate implementation authorization after design review.
2. Implement only on this disposable branch; no runtime integration by default.
3. Run focused synthetic tests, then full unit suite.
4. Capture exact commit SHA, interpreter/platform versions, commands, exit codes, stdout/stderr, and test summary.
5. Independently review source diff and test evidence.
6. Stop on any unexpected external side effect, orphan process, test failure, or evidence gap.
7. No merge, deployment, or production execution without separate explicit approval.

## Evidence manifest template

- Branch:
- Base commit:
- Test commit:
- Python version:
- OS/platform:
- Command:
- Exit code:
- Focused test results:
- Full suite result:
- Worker cleanup evidence:
- Log redaction evidence:
- Independent reviewer:
- Human decision:
