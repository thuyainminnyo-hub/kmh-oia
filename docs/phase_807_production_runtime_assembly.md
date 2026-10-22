# Phase 807 — Production Runtime Assembly Contract

Date: 2026-10-21

## Delivered
Added `src/production_runtime_assembly.py` to join the production trust-root loader, verified artifact bundle, `TrustedDecisionLearningService`, and `GovernedDecisionOrchestrator` in one fail-closed bootstrap path.

The factory requires the real queue, console, runtime bridge, receipt verifier, memory store, SQLite learning repository, classifier/policy artifact paths, signed attestation, format-specific byte loaders, production trust environment, and a mandatory `policy_runtime_binder`. It does not return an assembly if artifact trust, loading, service creation, or policy binding fails.

## Verification
- Ephemeral Ed25519 integration test binds verified byte payloads to the learning service and governed orchestrator.
- Missing policy binder fails before either artifact loader runs.
- Policy-binder exceptions fail closed and no assembly is returned.
- These are contract tests with ephemeral keys and test loaders; they do not establish production key provisioning or a real artifact-format implementation.

## Required deployment integration
A production application must supply its actual immutable classifier/policy artifacts, format loaders, release attestation, public trust-root config, receipt verifier, and policy binder that installs/uses the loaded policy inside the production execution path. This repo has no real release keys or format-specific loaders, so normal production traffic is not wired by these tests alone.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97


## Phase 808 follow-up

Added `scripts/create_runtime_artifact_attestation.py` and `src/runtime_artifact_io.py` for signed attestation production and strict JSON parsing. The producer uses a protected environment-provided Ed25519 seed and never stores it in source. A protected release workflow and real signing/trust keys are still deployment prerequisites.
