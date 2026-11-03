# Phase 02.10.16 — MLCW Disposable Dual-Lock Pilot

Status: OWNER-APPROVED PILOT / EXECUTION IN RUNNER REQUIRED
Scope: disposable branch only. No merge, production deployment, global graph merge, or promotion of inferred graph edges is authorized.

## Frozen baseline

- Repository: thuyainminnyo-hub/kmh-oia
- Baseline PR: #184 (must remain unchanged)
- Baseline commit: 0270137bce4a4bc213026f9b629d9524aacd5c33
- Pilot branch: pilot/mlcw-dual-lock-2026-11-04
- Target workflow: .github/workflows/mlcw-studio-ci.yml
- Studio package directory: case-studies/education/my-little-creative-world/studio

## Preflight invariants

1. Confirm the checked-out branch is exactly pilot/mlcw-dual-lock-2026-11-04.
2. Confirm HEAD is the frozen baseline before any pilot changes.
3. Confirm the worktree is clean.
4. Do not run commands against main or PR #184's head branch.
5. Do not enable repository, organization, or enterprise-wide Require lockfile enforcement.
6. Do not commit credentials, tokens, secrets, or local environment files.

## Runner procedure

Run from a clean disposable checkout with Node.js 22, npm, GitHub CLI authenticated with the minimum required repository permissions, and network access to npm and GitHub.

### A. Capture baseline evidence

```bash
git status --short
git rev-parse HEAD
node --version
npm --version
gh --version
```

Save the outputs in the pilot evidence bundle.

### B. Generate npm lockfile

```bash
cd case-studies/education/my-little-creative-world/studio
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Review package-lock.json and ensure it contains the complete dependency graph. Do not hand-edit it.

Then validate a clean install:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm test
npx playwright install --with-deps chromium
npm run test:e2e
```

Record exit codes, Node/npm versions, test summaries, and any warnings. If install or tests fail, stop and preserve logs; do not claim PASS.

### C. Generate and verify GitHub Actions lockfile

Return to the repository root:

```bash
cd -
gh extension install github/gh-actions-lock
gh actions-lock .github/workflows/mlcw-studio-ci.yml
gh actions-lock --verify .github/workflows/mlcw-studio-ci.yml
```

Review the complete diff, including any workflow reference rewrites and .github/workflows/actions.lock. Review each resolved action's owner/repository identity and commit SHA against trusted upstream sources. Never edit actions.lock manually.

The extension is pre-1.0/public-preview software; record its exact installed version and retain command output. If the installed version's help does not support the scoped verify syntax, stop and use the installed `gh actions-lock --help` as authoritative; do not guess flags.

### D. Coverage and non-covered inputs

- Confirm whether the workflow contains remote reusable workflow calls at jobs.<job_id>.uses.
- Inspect local ./ actions and their nested dependencies.
- Inspect container image references and require sha256 digests where applicable.
- Record runner image, Node version, Playwright version, and browser version separately; actions.lock does not lock these inputs.
- Treat --verify-local as coverage-only, not provenance verification.

### E. Evidence bundle and acceptance

Capture:
- baseline SHA and branch name;
- generated package-lock.json and actions.lock diffs;
- exact CLI/tool versions;
- npm ci exit code;
- unit and Playwright test summaries;
- actions-lock verify output;
- action provenance review notes;
- runner/browser versions;
- final git diff and worktree status.

PASS only if clean install, unit tests, browser tests, lockfile verification, provenance review, and independent review all pass. Otherwise mark BLOCKED or FAIL with root cause. Do not convert missing evidence into PASS.

## Stop conditions

Stop immediately if:
- branch or baseline SHA differs from the values above;
- a command requests production credentials or elevated permissions;
- a dependency resolves to an unexpected repository identity or commit;
- lockfile generation proposes unrelated workflow changes;
- tests fail or evidence is incomplete.

## Release boundary

This pilot authorizes isolated testing and review only. It does not authorize merging PR #184, merging the pilot branch, changing main, activating Require lockfile enforcement, deploying production, or modifying global/canonical graph data. A separate fresh Owner Approval is required for any such action.
