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

## Verification checkpoint — 2026-10-30

The official extension generated and uploaded the machine-generated lockfile. The committed lockfile was then verified in pull-request CI using both online and offline verification modes.

- Lockfile schema version: v0.0.3.
- Workflows onboarded: 8.
- Locked action references: 8 unique versioned dependency entries.
- Source repository identities: owner_id and repo_id recorded for each dependency.
- Remote action references covered by the lockfile in the independent scanner: 32.
- Independent scanner findings/errors: 0 / 0.
- Scanner decision: PASS / REVIEW_READY.
- `gh actions-lock --verify`: PASS.
- `gh actions-lock --verify-local`: PASS.
- KMH OIA unit tests: 494 passed.
- Repository validation, deployment evidence, reusable-workflow audit, Prompt Library QA, SBOM generation and validation: PASS.
- Main-branch source/SBOM attestation job: skipped on PR event by design.

The initial bootstrap exposed an important integration detail: the extension canonicalizes workflow references to exact version tags recorded in the lockfile. The workflow files were aligned to those lockfile references; subsequent PR runs passed. The custom action scanner was updated to require exact workflow-path coverage plus structurally valid commit and source-repository identity entries when a lockfile exists. The official online verifier independently checks upstream provenance.

Evidence:
- Lockfile generation run: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070089568
- Lockfile artifact: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070089568/artifacts/12983853452
- Lockfile verification run: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070092433
- Action audit artifact: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070092431/artifacts/12982914106
- PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/169

The extension release is pinned to v0.4.0. Its repository describes the extension as pre-1.0, so keep the version pinned and review extension updates deliberately. The GitHub lockfile platform feature is generally available, but a lockfile does not approve dependency safety or replace source/license review.

PR #169 remains Draft/unmerged. Container digest/provenance, reusable workflow identity and SHA review, SBOM/license reconciliation, and main-branch artifact attestation verification remain separate governance gates. Release remains HOLD until those gates are independently evidenced.

## SBOM and license review finding — 2026-10-30

The PR's SPDX evidence artifact was downloaded and inspected independently:

- SPDX format: SPDX-2.3.
- Package entries: 25.
- Unique name/version pairs: 11.
- Recognized dependency manifests: `requirements.txt` only.
- License `NOASSERTION` entries: 25.
- Evidence review status: `REVIEW_REQUIRED`.
- The repository's requirements file explicitly describes itself as minimal CI/tooling dependencies, not a complete application/runtime dependency declaration.

Therefore the SBOM generation/structural-validation CI job passed, but license assurance and full dependency coverage have not passed. Do not describe this result as license compliance. Phase 1011.10 should first establish the actual runtime dependency manifests/lockfiles, reconcile each package's declared/concluded license against authoritative package metadata and project policy, classify unknown/NOASSERTION packages, and preserve an exception/approval record where needed.

Supply-chain artifact: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070332239/artifacts/12983004243
Action dependency audit artifact: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41070332269/artifacts/12985066133

The latest PR head at this checkpoint is `498c33139526c1485092ee61887aa12f540cdbc9`. Lockfile verification, action audit, 494-test suite, reusable workflow audit, Prompt Library QA, repository validation/deployment evidence, and SBOM generation/structural validation all passed. The main-branch attestation job was skipped because this was a pull-request event. PR #169 remains Draft/unmerged; release remains HOLD.
