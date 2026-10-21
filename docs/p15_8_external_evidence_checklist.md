# P15.8 External Evidence Submission Checklist

This checklist defines the evidence package required to close the P15.8 gate for one exact release ID.

## Required evidence categories

### 1. telemetry
Provide:
- environment identity
- exact release ID
- observation start/end timestamps
- raw or directly exported telemetry samples
- monitoring/alert configuration reference
- alert exercise result, if an alert was tested
- operator/source identity

### 2. performance
Provide:
- exact release ID
- workload definition and version
- execution environment
- raw measurements
- baseline/reference measurements
- comparison method
- review/decision record
- operator/source identity

### 3. rollback_drill
Provide:
- release ID before rollback
- target/recovery release ID
- environment
- trigger/reason
- operator
- start/end timestamps
- observed outcome
- post-rollback health evidence
- rollback record or run log reference

### 4. authorization
Provide:
- exact release ID
- named approver
- authorization scope
- decision
- decision timestamp
- expiry or conditions
- linked approval record

### 5. incident_exercise
Provide:
- exact release ID
- environment
- exercise scenario
- on-call/operator ownership
- escalation path
- start/end timestamps
- observed response outcome
- incident/exercise record reference

## Closure rules

- Every artifact must identify the same exact release ID supplied to EvidenceClosureController.evaluate.
- Evidence must be externally supplied and attributable; repository-generated placeholder values do not close the gate.
- Missing or unavailable evidence remains Not evidenced.
- Do not infer live telemetry, production performance, executed rollback, human authorization, or an operational incident exercise from repository tests/controllers.
- Once all five categories are supplied, construct an EvidenceBundle and run P15.8 closure validation.
- A complete bundle may be validated only after exact release-ID matching succeeds.

## Phase 307 — trusted outcome-to-learning release gate

The five P15.8 evidence categories above remain required for release closure. For a release that enables trusted outcome-linked learning, also attach the following phase-specific evidence; this section does not treat repository tests as external evidence.

### Trusted provider authenticity
- Provider name, environment, endpoint/API version, and source-record identity.
- Authentication/signature verification contract from the provider's authoritative documentation.
- Redacted configuration reference identifying how credentials are supplied; never include credential values.
- Exact adapter revision and verifier configuration, including provider allowlist and receipt freshness limits.
- A non-production verification run showing pass and reject cases (wrong signature/provider, stale receipt, mismatched execution/source, and replay).

### External outcome attribution
- Exact runtime execution ID, provider source-record ID, receipt/content identifier, and trace ID.
- The raw or directly exported provider outcome record, with timestamp and attribution showing it belongs to the cited execution.
- An explicit description of the expected business outcome and how the evidence establishes it; internal QA PASS and caller-supplied booleans are not external outcome evidence.
- A matching evidence-admission result and an independently re-verified receipt on the learning boundary.

### Learning and adaptation governance
- Exact code commit SHA, policy version, test results, and evidence IDs.
- Recorded result proving a mismatched or rejected receipt produced no trusted learning write or adaptation proposal.
- For a trusted poor outcome, evidence that any adaptation stays PROPOSED until a separately authorized approval is recorded.
- Named human reviewer and decision for the prerequisite learning-admission PR and the dependent trusted-learning PR.

### Operational proof and final decision
- Target environment identity, deployment commit, storage/replay-store configuration reference, health/smoke result, monitoring evidence, recovery/backup check, and rollback owner/procedure.
- For multi-host claims, a concurrency/replay test against the actual shared transactional store and target topology; a same-host SQLite test is not sufficient.
- Record each criterion as PASS, FAIL, BLOCKED, or NOT RUN with a direct evidence link.
- Release stays HOLD while any mandatory evidence is missing, any human review is absent, or a check is merely inferred from repository code/CI.

## Current status

At this checkpoint the repository contains the deterministic P15.8 closure controller, but no external evidence is being asserted by this checklist. Production readiness and final handoff remain blocked until the five categories are actually supplied and validated.
