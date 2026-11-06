# AI Engineering Control Plane v1

**Status:** Architecture integration baseline — review required; runtime wiring is not claimed.  
**Owner scope:** Integrate into KMH OIA core.  
**Operating constraints:** Phone-first authoring/operation; free-tier-first; fail closed; evidence before promotion.

## 1. Purpose

Treat AI-generated code and agent actions as untrusted proposals. KMH OIA remains responsible for deterministic authorization, bounded execution, observable outcomes, cost accounting, and evidence-gated learning.

This document extends the existing runtime path rather than introducing a parallel orchestration runtime:

`User Goal → Input Gateway → OIA Core → Context Assembly → Workflow → Agent → State → Tool Security → Governed Tool → Evaluation → Response → Trace`

## 2. Integration map

| Capability | Existing KMH OIA boundary | Required control |
|---|---|---|
| Agentic coding / orchestration | OIA Core, Workflow, Agent | Plans are proposals; tools execute only through governed boundaries |
| Deterministic guardrails | SecurityPolicy / ToolSecurityPolicy | Explicit allowlist, schema validation, bounded arguments, deny-by-default |
| Execution | ToolExecutor / ToolRegistry | Timeouts, idempotency where applicable, scoped permissions, no implicit shell |
| Verification | Evaluation / QA | Unit, contract, integration, security and regression evidence; generated output is never self-approved |
| Observability | Tracer / TraceEvent | Correlation IDs, stage timings, status, redacted metadata, error categories |
| Runtime economics | Model adapter boundary (to be designed) | Budget before call, token/latency accounting, cache policy, context limits, routing policy |
| Learning governance | OperatingLoopRecord / EvidenceAdmissionGate | Observed ≠ verified ≠ outcome-linked; admission and decision change remain separately gated |

## 3. Non-negotiable invariants

1. **No direct model-to-core mutation.** Model output is untrusted data until parsed, validated, authorized and evaluated.
2. **Deny by default.** Unknown tools, malformed payloads, missing permissions, exceeded budgets and unavailable policy checks fail closed.
3. **No hidden execution.** Every side effect must pass through a governed tool boundary and produce a traceable execution record.
4. **No self-certification.** The model that generated an artifact cannot be the sole authority that approves it.
5. **Evidence states are distinct.** Internal trace/QA is not external outcome evidence. Learning admission does not automatically authorize a policy or production change.
6. **Cost is a control, not a post-hoc metric.** A request must have a budget and a bounded context before a paid inference call.
7. **Fallback is explicit.** A fallback must be policy-approved, observable, bounded and recorded; no silent provider/model downgrade.
8. **Secrets and personal data are excluded from traces** unless a separately reviewed, minimal and protected requirement exists.

## 4. Runtime AI cost contract

Before any run-time inference call, the future model gateway must record or enforce:

- task class and data classification;
- approved provider/model route and fallback order;
- maximum input/output tokens and request timeout;
- per-request and per-session budget;
- cache eligibility and cache-key privacy rules;
- actual provider, model, usage, latency and estimated cost when returned;
- stop conditions for budget exhaustion, repeated failure and provider unavailability.

**Free-tier-first rule:** Prefer deterministic local logic and existing non-AI code. Use a free/local model only when its availability, license, privacy and device resource profile are verified. Never describe a service as free without checking its current limits and terms. Paid inference is disabled unless the owner explicitly configures and approves a budget.

## 5. Verification and promotion gates

| Gate | Minimum evidence | Failure behavior |
|---|---|---|
| G0 — Design | Architecture review, threat model, interface contracts | Hold implementation |
| G1 — Unit/contract | Positive and adversarial tests for policy, schemas and budget | Block merge |
| G2 — Integration | Trace proves every model/tool action traverses the control plane | Block execution |
| G3 — Reliability | Timeout, malformed output, provider outage, retry and fallback tests | Fail closed; no promotion |
| G4 — Cost | Reproducible token/latency/cost benchmark with declared workload | Budget remains disabled |
| G5 — Learning | Evidence admission, reviewer/policy decision, regression comparison | Keep learning NOT_ADMITTED |
| G6 — Production | Exact-head CI, security review, operational runbook, owner approval | HOLD |

A passing unit test is evidence only for the behavior it exercises. Mocked provider or device tests do not establish live provider/device behavior.

## 6. Phone-first and free-tier operating profile

- Author and review changes from Android browser/GitHub mobile where practical.
- Use Termux for local Python/test commands when a local execution environment is available.
- Keep the baseline deterministic and runnable without model credentials.
- Do not require a desktop GPU, paid API, always-on server or paid database for the first integration slice.
- Keep local state and artifacts scoped; do not put credentials in repository files, screenshots, logs or chat.
- Use GitHub Actions only for bounded CI checks; CI success is not a substitute for live Android or production validation.

## 7. Phased implementation plan

| Phase | Deliverable | Acceptance evidence | Current status |
|---|---|---|---|
| A — Architecture baseline | This integration contract mapped to existing OIA boundaries | Reviewed document + contract tests | Drafted in this branch |
| B — Guardrail contracts | Provider-neutral typed request/response, route allowlist, data classification and token/cost budget admission | Adversarial unit tests on exact PR head | Implemented in branch; CI verification pending |
| C — Trace & evaluation | Correlated trace fields, redaction and independent evaluator contract | Trace assertions + redaction tests | Not started |
| D — Model gateway | Provider-neutral adapter, deterministic routing, bounded budgets | Fake-provider tests + usage accounting | Not started |
| E — Resilience | Timeout, retry ceilings, circuit-breaker/fallback policy | Fault-injection tests | Not started |
| F — Learning integration | Evidence-gated learning candidate review with execution-ID binding, root-cause classification, regression gate and owner approval | Adversarial unit tests + exact-head CI | Implemented; exact-head CI PASS |
| G — Controlled pilot | Gateway-backed Agent adapter wired through existing OIARuntime Agent seam; model tool proposal remains subject to autonomy policy and GovernedTool | Fake-provider end-to-end test, denied-tool test, exact-head CI | Integration slice implemented; live provider/device pilot pending |

## 8. Explicit non-goals for this baseline

- No model provider is selected or called.
- No paid API, API key, hosted database or telemetry vendor is introduced.
- No automatic code merge, deployment, policy change or learning promotion is authorized.
- No existing security, evidence-admission, execution-identity or audit gate is bypassed.
- No claim of production readiness is made.

## 9. Decision record

**Decision:** Integrate AI engineering controls into the existing KMH OIA runtime boundaries; do not create a second orchestration core.

**Rationale:** Reuse existing security, trace, evaluation and evidence-admission seams; minimize duplication and preserve deterministic local operation.

**Phase B implementation checkpoint:** `src/ai_contracts.py` defines typed task/data classifications, strict mapping parsing, route allowlisting, request/session token limits, cost limits and fail-closed admission. `tests/test_ai_contracts.py` adds adversarial and boundary tests. No provider call or runtime wiring is included. Exact-head CI is required before Phase B can be marked verified.

**Next engineering slice:** After Phase B CI passes, review whether the contract should be wired to the existing governed-tool boundary or remain a dedicated model-gateway preflight. Add trace correlation and redaction tests before any live provider connection.

**Promotion rule:** Build → Connect → Run → Verify. Each phase remains HOLD until its own evidence is available.


## 10. Phase F implementation checkpoint

Added `src/learning_governance.py` and `tests/test_learning_governance.py`.

The reviewer consumes the existing `EvidenceAdmissionResult` from `EvidenceAdmissionGate`; it does not duplicate trusted-source verification. A candidate records execution/decision/trace identifiers, artifact digest, expected and actual outcome, typed root-cause category, and proposed change. Review remains HOLD unless evidence is ADMITTED and OUTCOME_LINKED and both baseline and candidate regression checks pass. Passing checks produce REVIEW_REQUIRED until a non-empty owner approval identifier is supplied. Approval only marks the candidate eligible for a separate governed promotion step; no active standard, policy, prompt, route or runtime configuration is mutated here.

The unit tests cover missing/unadmitted evidence, missing regression, candidate regression failure, baseline failure, owner approval, missing artifact digest and invalid regression counts. Files were fetched back from the branch before CI.

**Important limitation:** The current evidence-admission result does not itself carry the execution identifier as a typed field; the candidate-to-admission execution binding still needs an explicit comparison in a future integration layer. The existing trusted receipt gate remains the authority for admission. Do not treat caller-supplied expected/actual text as external proof.

**Current Phase F status:** Execution-bound evidence admission and reviewer checks are implemented. Exact-head CI PASS at code/test head `eedff53368c6a8a25aa73c3772a05a627c37c442`. Owner approval identity authentication remains a separate required control. No learning promotion or production policy mutation is authorized.


## 11. Phase F execution-binding hardening

The evidence admission result now carries the execution ID that was checked against the trusted receipt verification result. The learning reviewer requires this ID to equal the candidate's execution ID; mismatch remains HOLD. Regression tests cover the mismatch and assert that the admission result preserves the matched execution ID.

This closes the previously documented candidate-to-admission execution binding gap. It does not make the caller-supplied expected/actual outcome descriptions authoritative, and it does not authenticate owner approval IDs. Owner identity/authority must be verified by the separate approval workflow before any promotion action.

The code/test changes are in the current branch and require exact-head CI. No live runtime/model integration or promotion is claimed.


## 12. Phase G controlled runtime integration slice

Added `src/model_gateway_agent.py`, a `GatewayBackedAgent` adapter that implements the existing Agent interface and invokes the provider-neutral ModelGateway. It serializes goal/context as JSON, carries the OIA session ID in internal request/trace metadata without sending that ID in the model prompt, and accepts only a strict JSON object with exactly `tool_name`, `input_text`, and `reason`. Invalid JSON, extra fields, empty fields or gateway denial fail closed.

The existing `OIARuntime` already accepts an injected Agent. The live runtime bridge now passes `tool_name=None`, so the Agent's proposed tool is considered; it still passes through the existing AutonomyPolicy and GovernedTool security boundary. The model cannot execute a tool directly.

Added `tests/test_model_gateway_agent.py` and `tests/test_model_gateway_runtime_integration.py`. The integration tests use a fake local provider and verify a successful low-risk echo workflow plus blocking of an unlisted tool. The run is internal/mock evidence only: the LiveRuntimeBridge still records external evidence as OBSERVED and learning admission remains false without a trusted external receipt.

Exact PR head `eedff53368c6a8a25aa73c3772a05a627c37c442`:
- KMH OIA Tests #1712 / run 41563702409: SUCCESS; 539 tests passed; performance-baseline passed.
- KMH OIA Validation #1631 / run 41563702423: SUCCESS; repository-validation, tests, performance-evidence and deployment-evidence-bundle passed.

**Phase G status:** Controlled fake-provider integration slice implemented and exact-head CI PASS. No live provider, Android-device execution, real external side effect, durable budget ledger, or production rollout is claimed. PR remains Draft/HOLD pending independent review.
