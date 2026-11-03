# Phase 02.10.16 — MLCW Disposable Dual-Lock Pilot

Status: OWNER-APPROVED PILOT / RUNNER EXECUTION REQUIRED
Scope: disposable branch only. No merge, production deployment, global graph merge, or promotion of inferred graph edges is authorized.

## Frozen baseline and pilot branch

- Repository: thuyainminnyo-hub/kmh-oia
- Baseline PR: #184 (must remain unchanged)
- Frozen baseline commit: 0270137bce4a4bc213026f9b629d9524aacd5c33
- Pilot branch: pilot/mlcw-dual-lock-2026-11-04
- Runbook-only commit at pilot setup: e58c227809c74a4e10e51f4c1d58c1af45c7e89f
- Target workflow: .github/workflows/mlcw-studio-ci.yml
- Studio package directory: case-studies/education/my-little-creative-world/studio

The pilot branch already contains the runbook commit above. Therefore, do NOT expect HEAD to equal the frozen baseline. The required invariant is that the frozen baseline is the merge base and that the only pre-execution change relative to it is this approved runbook.

## Preflight invariants

1. Confirm the checked-out branch is exactly pilot/mlcw-dual-lock-2026-11-04.
2. Confirm `git merge-base HEAD 0270137bce4a4bc213026f9b629d9524aacd5c33` returns exactly the frozen baseline SHA.
3. Confirm `git diff --name-only 0270137bce4a4bc213026f9b629d9524aacd5c33..HEAD` lists only this runbook before generated pilot outputs.
4. Confirm the worktree is clean before starting.
5. Do not run commands against main or PR #184's head branch.
6. Do not enable repository, organization, or enterprise-wide Require lockfile enforcement.
7. Do not commit credentials, tokens, secrets, or local environment files.

## Runner procedure

Run from a clean disposable checkout with Node.js 22, npm, GitHub CLI authenticated with minimum required repository permissions, and network access to npm and GitHub.

### A. Capture baseline evidence

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git merge-base HEAD 0270137bce4a4bc213026f9b629d9524aacd5c33
git diff --name-only 0270137bce4a4bc213026f9b629d9524aacd5c33..HEAD
node --version
npm --version
gh --version
```

Save outputs in the pilot evidence bundle. Stop if the merge-base or changed-file list differs from the invariants above.

### B. Generate npm lockfile

```bash
cd case-studies/education/my-little-creative-world/studio
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Review package-lock.json and ensure it contains the complete dependency graph. Do not hand-edit it.

Then validate a clean install with lifecycle scripts disabled:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm test
npx playwright install --with-deps chromium
npm run test:e2e
```

Record exit codes, Node/npm versions, test summaries, and warnings. Disabling lifecycle scripts may prevent packages that rely on install-time builds from functioning. If a test fails for that reason, stop and record the evidence; do not silently rerun with scripts enabled. Any script-enabled install requires a separate review of package lifecycle scripts and fresh explicit authorization.

### C. Generate and verify GitHub Actions lockfile

Return to the repository root:

```bash
cd -
gh extension install github/gh-actions-lock
gh --version
gh extension list
gh actions-lock --help
gh actions-lock .github/workflows/mlcw-studio-ci.yml
gh actions-lock --verify .github/workflows/mlcw-studio-ci.yml
```

Record the installed extension revision/version and full command output. The extension is pre-1.0/public-preview software; its help output is authoritative if CLI flags differ. Stop rather than guessing unsupported flags.

Review the complete diff, including any workflow reference rewrites and .github/workflows/actions.lock. Review each resolved action's owner/repository identity and commit SHA against trusted upstream sources. Never edit actions.lock manually.

### D. Coverage and non-covered inputs

- Confirm whether the workflow contains remote reusable workflow calls at jobs.<job_id>.uses.
- Inspect local ./ actions and their nested dependencies. The extension does not follow local path actions; a local action with remote dependencies can block generation unless handled through the documented migration/ignore options after review.
- Inspect container image references and require sha256 digests where applicable.
- Record runner image, Node version, Playwright version, and browser version separately; actions.lock does not lock these inputs.
- Treat --verify-local as coverage-only, not provenance verification.
- A reusable workflow's dependencies must be locked in the repository where that reusable workflow is defined.

### E. Evidence bundle and acceptance

Capture:
- baseline SHA, pilot branch name, HEAD, and merge-base;
- generated package-lock.json and actions.lock diffs;
- exact CLI/tool and extension versions;
- npm ci exit code;
- unit and Playwright test summaries;
- actions-lock verify output;
- action provenance review notes;
- runner/browser versions;
- final git diff and worktree status.

PASS only if clean install, unit tests, browser tests, lockfile verification, provenance review, and independent review all pass. Otherwise mark BLOCKED or FAIL with root cause. Do not convert missing evidence into PASS.

## Stop conditions

Stop immediately if:
- branch or merge-base differs from the values above;
- unexpected files are already changed before execution;
- a command requests production credentials or elevated permissions;
- a dependency resolves to an unexpected repository identity or commit;
- lockfile generation proposes unrelated workflow changes;
- tests fail or evidence is incomplete;
- install scripts would need to be enabled without a separately reviewed and approved plan.

## Release boundary

This pilot authorizes isolated testing and review only. It does not authorize merging PR #184, merging the pilot branch, changing main, activating Require lockfile enforcement, deploying production, or modifying global/canonical graph data. A separate fresh Owner Approval is required for any such action.
