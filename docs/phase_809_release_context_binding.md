# Phase 809 — Release Context Binding for Artifact Signing

Date: 2026-10-21

## Delivered

The producer's production mode now requires its source revision and build run ID to match the current GitHub Actions context (`GITHUB_SHA`, `GITHUB_RUN_ID`). It requires `GITHUB_ACTIONS=true`, limits production signing to `refs/heads/main`, and requires the `workflow_dispatch` event. Missing or mismatched context fails closed before artifact measurement and signing.

## Tests

- reject mismatched source SHA
- reject mismatched run ID
- reject missing GitHub Actions marker
- reject feature branch and pull-request event
- test-only ephemeral key is used; no real production signing secret is stored in the repository

## Remaining gate

These checks help prevent accidental context mismatch. They do not authenticate environment variables against a malicious process or replace GitHub Environment protection, approval rules, key-custody policy, a protected release workflow, or independent review.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
