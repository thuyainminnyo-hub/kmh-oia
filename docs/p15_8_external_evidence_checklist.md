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

## Current status

At this checkpoint the repository contains the deterministic P15.8 closure controller, but no external evidence is being asserted by this checklist. Production readiness and final handoff remain blocked until the five categories are actually supplied and validated.
