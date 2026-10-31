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

## 3. Scoped generation procedure

Only after verifying the exact current workflow content and the binary:

```bash
/tmp/gh-actions-lock .github/workflows/test.yml
git diff -- .github/workflows/test.yml .github/workflows/actions.lock
```

Review every generated action commit as a dependency code change. Confirm the generated owner/repository identity fields and that the resolved commits are the intended upstream repositories. Do not accept unexpected repository identity changes.

Then run:

```bash
/tmp/gh-actions-lock --verify
```

Capture command output, exit status, exact branch/head SHA, and the subsequent GitHub Actions run/job results. `--verify-local` is only an offline coverage check; it is not provenance verification.

## 4. Coverage boundaries and compensating controls

- The caller's lockfile does not pin remote reusable workflow references at `jobs.<job_id>.uses`; independently require full 40-character commit SHAs.
- The reusable workflow source repository must onboard and lock its own action dependencies.
- Local `./` actions need explicit migration/handling and review.
- Container images need immutable `@sha256:` digests.
- Lockfiles pin dependency code resolution; they do not prove that the pinned code is safe.
- Do not use `--accept-moved` in automation.
- Protect lockfile changes with CODEOWNERS and required code-owner review.
- Dependabot updates should regenerate lockfile entries for already-onboarded workflows.

## 5. Acceptance gates

- [ ] Re-fetch workflow; confirm expected baseline or review drift.
- [ ] Download v0.4.0 Linux amd64 asset.
- [ ] Independently verify SHA-256 against the release API digest.
- [ ] Record binary version and help output.
- [ ] Generate lockfile for `.github/workflows/test.yml` only.
- [ ] Review workflow rewrite and complete lockfile diff.
- [ ] Run `--verify` and record exit status/output.
- [ ] Run existing workflow on the candidate branch and capture exact-head CI evidence.
- [ ] Review dependency changes; obtain required reviewers.
- [ ] Only then consider enabling repository/organization Require lockfile policy.

## 6. Current decision

**GO:** prepare and execute an isolated, one-workflow pilot.  
**HOLD:** lockfile enforcement, broad workflow migration, and production rollout until all acceptance gates have evidence.

## 7. Execution truth

This document and its preparation branch are committed planning artifacts only. The CLI has not been installed or executed in this environment. No `actions.lock` has been generated, no workflow has been rewritten, and no CI run has been triggered by this preparation step.
