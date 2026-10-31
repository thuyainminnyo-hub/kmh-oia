# GitHub Actions Lockfile Pilot — KMH OIA

**Status:** preparation branch only; lockfile generation and CI verification are still pending.  
**Target workflow:** `.github/workflows/test.yml`  
**Repository:** `thuyainminnyo-hub/kmh-oia`

## 1. Verified baseline

Fetched from the default branch before creating this pilot branch:

- Workflow blob SHA: `1894b673f33c98c66fffe32f9b15539d41d9f9f3`
- `actions/checkout@v4`: 2 references
- `actions/setup-python@v5`: 2 references
- `actions/upload-artifact@v4`: 1 reference
- No remote reusable workflow calls (`jobs.<job_id>.uses`) found.
- No local `uses: ./...` actions found.
- No `container:` image declarations found.

Re-fetch and compare the workflow before generating a lockfile; the baseline SHA above is not proof that the file is unchanged on this branch.

A fresh inventory of `main` on 2026-10-31 found four workflow files: `nist-seed-reproduction.yml`, `prompt-library-schema-qa.yml`, `test.yml`, and `validation.yml`. All four currently use `actions/checkout@v4` and `actions/setup-python@v5`; `test.yml` and `validation.yml` also use `actions/upload-artifact@v4`. The three non-target workflows were inventoried and showed no remote reusable-workflow calls, no local `uses: ./...` references, and no `container:` declarations. Their current workflow blob SHAs are available from the GitHub API and must be re-fetched before any generation. This pilot intentionally scopes generation to `test.yml`; it does not mean the other three workflows are onboarded.

## 2. Tool version pin

GitHub Releases API identified immutable release `v0.4.0`:

- Release: https://github.com/github/gh-actions-lock/releases/tag/v0.4.0
- Release ID: `422397068`
- Tag: `v0.4.0`
- Linux amd64 asset: `linux-amd64`
- Asset size: `9416866` bytes
- Published asset digest: `sha256:f9da98f2a6e9e0ae77deadf9a2319a8a86bb002b541cc3203b247cc59fb04842`

The digest is the GitHub Releases API asset digest. Before installation, independently calculate SHA-256 of the downloaded bytes and compare it to this value. Do not execute the binary if the digest differs. Also inspect `--version` and `--help` after verification.

Example for a trusted Linux amd64 maintainer checkout:

```bash
set -euo pipefail
curl -fsSL \
  https://github.com/github/gh-actions-lock/releases/download/v0.4.0/linux-amd64 \
  -o /tmp/gh-actions-lock
printf '%s  %s\n' \
  'f9da98f2a6e9e0ae77deadf9a2319a8a86bb002b541cc3203b247cc59fb04842' \
  /tmp/gh-actions-lock | sha256sum --check
chmod 0755 /tmp/gh-actions-lock
/tmp/gh-actions-lock --version
/tmp/gh-actions-lock --help
```

Do not assume this Linux asset is suitable for macOS or Windows maintainers; select the matching platform asset and verify its own published digest.

## 3. Upstream CLI maturity and read-only inspection

The current upstream README does not state a Public Preview label or a maturity guarantee. The latest inspected release is `v0.4.0` (pre-1.0 versioning), so treat CLI behavior and lockfile compatibility as version-sensitive and pin the evaluated release. Official installation is through the authenticated GitHub CLI extension mechanism:

```bash
gh extension install github/gh-actions-lock
```

The upstream README documents `gh actions-lock --no-fix` as a read-only, online report mode. Prefer this as the first CLI behavior check after installation. `gh actions-lock --verify` is also read-only and performs online verification; `--verify-local` is offline coverage-only and does not verify provenance. `gh actions-lock` and `--relock` write changes and remain gated on explicit review.

Coverage limitations from the current upstream README:

- Remote reusable workflows referenced by `jobs.<job_id>.uses` are not locked by this tool.
- Local `./...` actions are not followed or locked; handling them requires an explicit supported migration or ignore decision, with review.
- Container images are not locked; use immutable `@sha256:` digests.
- A lockfile is not a security review of the pinned dependency itself.

For this target workflow, the baseline inventory found none of those constructs. Re-fetch and inspect the exact candidate workflow before running the tool, and stop if the inventory has drifted.

## 4. Scoped generation procedure

Only after installing the pinned CLI extension, re-fetching and reviewing the exact current workflow content, and confirming the baseline has not drifted, start with read-only inspection:

```bash
gh actions-lock --no-fix .github/workflows/test.yml
gh actions-lock --verify
```

If both checks are understood and pass, explicitly approve the write step and generate only the target workflow:

```bash
gh actions-lock .github/workflows/test.yml
git diff -- .github/workflows/test.yml .github/workflows/actions.lock
```

Review every generated action commit as a dependency code change. Confirm the generated owner/repository identity fields and that the resolved commits are the intended upstream repositories. Do not accept unexpected repository identity changes. Re-run `gh actions-lock --verify` after generation.

Capture command output, exit status, exact branch/head SHA, and the subsequent GitHub Actions run/job results. `--verify-local` is only an offline coverage check; it is not provenance verification.

## 5. Coverage boundaries and compensating controls

- The caller's lockfile does not pin remote reusable workflow references at `jobs.<job_id>.uses`; independently require full 40-character commit SHAs.
- The reusable workflow source repository must onboard and lock its own action dependencies.
- Local `./` actions need explicit migration/handling and review.
- Container images need immutable `@sha256:` digests.
- Lockfiles pin dependency code resolution; they do not prove that the pinned code is safe.
- Do not use `--accept-moved` in automation.
- Protect lockfile changes with CODEOWNERS and required code-owner review.
- Dependabot updates should regenerate lockfile entries for already-onboarded workflows.

## 6. Acceptance gates

- [ ] Re-fetch workflow; confirm expected baseline or review drift.
- [ ] Download v0.4.0 Linux amd64 asset.
- [ ] Independently verify SHA-256 against the release API digest.
- [ ] Record the verified release digest, extension version, and `gh actions-lock --help` output.
- [ ] Generate lockfile for `.github/workflows/test.yml` only.
- [ ] Review workflow rewrite and complete lockfile diff.
- [ ] Run `--verify` and record exit status/output.
- [ ] Run existing workflow on the candidate branch and capture exact-head CI evidence.
- [ ] Review dependency changes; obtain required reviewers.
- [ ] Inventory and onboard every workflow that will be in the Require lockfile policy target scope; this repository currently has four workflow files, while this pilot covers only `test.yml`.
- [ ] Add `.github/workflows/actions.lock` to CODEOWNERS and verify required code-owner review / branch rules are configured.
- [ ] Evaluate the Require lockfile policy against the exact target set and confirm no targeted workflow remains un-onboarded.
- [ ] Only then consider changing Require lockfile policy from Evaluate to Active. Active policy blocks targeted workflows that are not onboarded.

## 7. Current decision

**GO:** prepare and execute an isolated, one-workflow pilot.  
**HOLD:** lockfile enforcement, broad workflow migration, and production rollout until all acceptance gates have evidence. A one-workflow pilot is not repository-wide readiness; do not activate Require lockfile across this repository while three workflows remain outside the pilot.

## 8. Execution truth

This document and its preparation branch are committed planning artifacts only. The CLI has not been installed or executed in this environment. No `actions.lock` has been generated, no workflow has been rewritten, and no CI run has been triggered by this preparation step.
