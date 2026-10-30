# Phase 1011.9 — Transitive Action Dependency Assurance

## Objective

Extend Phase 1011.8's direct full-SHA pinning with GitHub's workflow dependency lockfile so direct and transitive action dependencies are recorded with verified commit and source-repository identity.

## Implementation

- Generate `.github/workflows/actions.lock` using the official `github/gh-actions-lock` GitHub CLI extension.
- Pin the extension to the immutable `v0.4.0` release.
- Upload the generated lockfile as a CI artifact for independent review before committing it.
- Verify committed lockfile provenance and freshness with `gh actions-lock --verify`.
- Verify offline workflow coverage with `gh actions-lock --verify-local`.
- Retain the separate reusable-workflow SHA audit and the Phase 1011.7 container digest scanner.

## Scope boundaries

The lockfile covers direct and transitive action dependencies and records upstream repository identity. It does not lock cross-repository reusable workflow calls or container images. Local path actions require separate treatment; no local composite action manifests were present in the Phase 1011.8 audit. The lockfile is not a source-code safety, vulnerability, or license approval.

## Bootstrap procedure

1. Push this workflow branch to trigger the bootstrap run.
2. Inspect the generated `kmh-oia-actions-lockfile` artifact and its workflow coverage.
3. Commit the generated lockfile only after verifying every dependency, repository identity, and workflow entry.
4. Confirm PR CI executes both online provenance verification and offline coverage verification.

## Upstream references

- GitHub workflow dependency lockfiles: https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles
- Locking action dependencies: https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies
- Official lockfile extension: https://github.com/github/gh-actions-lock
- Immutable v0.4.0 release: https://github.com/github/gh-actions-lock/releases/tag/v0.4.0

## Release policy

Keep the PR Draft and release HOLD until the generated lockfile is reviewed, committed, and independently verified. SBOM quality, license reconciliation, reusable workflow governance, container provenance, and main-branch artifact attestations remain separate gates.
