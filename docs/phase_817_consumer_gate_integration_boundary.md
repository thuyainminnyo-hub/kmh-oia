# Phase 817 — Separate Consumer Gate from Legacy Evidence Factory

Date: 2026-10-22

## Change

The Phase 816 consumer release gate is retained as a standalone API, but the legacy `ProductionEvidenceRuntimeConfig` factory will not silently require new release-bundle fields from existing callers. The factory remains focused on provider allowlisting and durable SQLite receipt replay protection; it has not yet been production-wired to authenticate a deployed runtime bundle.

## Why

Exact-head CI for Phase 816 revealed eight regressions in the existing production-evidence runtime factory: existing callers do not yet pass release bundle/attestation paths, producer metadata or trust-root keys. Turning those fields into mandatory factory requirements broke provider validation and restart/replay tests before the intended consumer gate could be composed.

## Status

This correction restores the prior factory contract rather than weakening bundle verification. Runtime bundle acceptance must be introduced through a separate bootstrap API or a deliberate migration of all callers with real signed evidence and a provisioned trust root. Tests must pass at the exact commit before this phase is considered verified. **Production HOLD.**
