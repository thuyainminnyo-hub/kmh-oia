# Phase 809 — Release Context Binding for Artifact Signing

Date: 2026-10-21

## Delivered

The producer's production mode requires source revision and build run ID to match the current GitHub Actions context (`GITHUB_SHA`, `GITHUB_RUN_ID`). It requires `GITHUB_ACTIONS=true`, limits production signing to `refs/heads/main`, and requires the `workflow_dispatch` event.

The signer measures classifier and policy bytes and rejects missing/empty artifact data **before production run-context checks are evaluated**. This ordering makes the earliest actionable artifact failure deterministic. Production context checks still fail closed on missing or mismatched context.

## Tests

- reject mismatched source SHA
- reject mismatched run ID
- reject missing GitHub Actions marker
- reject feature branch and pull-request event
- reject empty artifacts before reporting context mismatch
- test-only ephemeral key is used; no real production signing secret is stored in the repository

## Remaining gate

These checks prevent accidental context mismatch; they do not authenticate environment variables against a malicious process and do not replace GitHub Environment protection, approval rules, key custody, a protected release workflow, or independent review. They occur after artifact measurement and do not replace source/build provenance.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
