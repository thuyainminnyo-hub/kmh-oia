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

The GitHub Oct 28, 2026 announcement describes the platform lockfile feature as generally available. However, the upstream `github/gh-actions-lock` README still explicitly labels the extension Public Preview and pre-1.0. Treat these as distinct claims: platform feature GA does not mean the CLI extension itself has left preview. Pin and evaluate the exact CLI release before production use. The upstream README documents installation through the authenticated GitHub CLI extension mechanism. The official GitHub CLI manual supports pinning a binary extension to an exact release tag with `--pin`; install the reviewed tag explicitly:

```bash
gh extension install github/gh-actions-lock --pin v0.4.0
```

Record `gh extension list`, the extension's reported version, and `gh actions-lock --help`. Confirm the installed extension is pinned to `v0.4.0`. The separate Linux release-asset download/checksum procedure above is an alternative artifact-verification path; do not mix a standalone downloaded binary with `gh actions-lock` extension commands. The upstream README documents `gh actions-lock --no-fix` as a read-only, online report mode. Prefer this as the first CLI behavior check after installation. `gh actions-lock --verify` is also read-only and performs online verification, but it requires an existing lockfile to verify; do not run it as a pre-generation acceptance check when `.github/workflows/actions.lock` does not yet exist. `--verify-local` is offline coverage-only and does not verify provenance. `gh actions-lock` and `--relock` write changes and remain gated on explicit review.

Coverage limitations from the current upstream README:

- GitHub's Oct 28, 2026 GA changelog says the platform feature includes reusable workflow references, but the current detailed GitHub Docs page says lockfiles do not pin `jobs.<job_id>.uses`; the current CLI README also says remote reusable workflows are not locked. Upstream CLI issue #179 documents the gap, including a case where `--verify` may pass despite an unlocked reusable workflow call. Treat the changelog wording as ambiguous/inconsistent with the detailed implementation guidance; do not claim reusable-workflow pinning from the caller's lockfile.
- Local `./...` actions are not followed or locked; handling them requires an explicit supported migration or ignore decision, with review.
- Container images are not locked; use immutable `@sha256:` digests.
- A lockfile is not a security review of the pinned dependency itself.

For this target workflow, the baseline inventory found no reusable workflow calls, local actions, or container declarations, so the current discrepancy does not block the narrowly scoped `test.yml` pilot. It does block claiming repository-wide reusable-workflow coverage. Re-fetch and inspect the exact candidate workflow before running the tool, and stop if the inventory has drifted.

## 4. Scoped generation procedure

Only after installing the pinned CLI extension, re-fetching and reviewing the exact current workflow content, and confirming the baseline has not drifted, start with this read-only inspection:

```bash
gh actions-lock --no-fix .github/workflows/test.yml
```

Review the report and resolve every warning/error. Because the lockfile does not exist yet, do not treat `gh actions-lock --verify` as a pre-generation check. Only after the dependency report is reviewed and the write step is explicitly approved, generate only the target workflow:

```bash
gh actions-lock .github/workflows/test.yml
git diff -- .github/workflows/test.yml .github/workflows/actions.lock
```

Review every generated action commit as a dependency code change. Confirm the generated owner/repository identity fields and that the resolved commits are the intended upstream repositories. Do not accept unexpected repository identity changes. Then run `gh actions-lock --verify` after generation and record its output and exit status.

Capture command output, exit status, exact branch/head SHA, and the subsequent GitHub Actions run/job results. `--verify-local` is only an offline coverage check; it is not provenance verification.

## 5. Coverage boundaries and compensating controls

- The GA changelog's reusable-workflow wording conflicts with the detailed GitHub Docs and current CLI README/issue tracker. Operationally, assume remote reusable workflow calls are NOT pinned by the caller's lockfile or checked by CLI `--verify` until GitHub clarifies and tested evidence proves otherwise.
- Pin remote reusable workflow references to full 40-character commit SHAs; separately assess the reusable workflow source repository's own action dependencies and lockfile.
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
- [ ] Install the extension with `gh extension install github/gh-actions-lock --pin v0.4.0`; record `gh extension list`, `gh actions-lock --help`, and the installed release tag.
- [ ] If independently auditing the standalone Linux binary, verify its SHA-256 against the release API digest before execution.
- [ ] Generate lockfile for `.github/workflows/test.yml` only.
- [ ] Review workflow rewrite and complete lockfile diff.
- [ ] After generation, run `gh actions-lock --verify` and record exit status/output; do not run it as a pre-generation check when no lockfile exists.
- [ ] Run existing workflow on the candidate branch and capture exact-head CI evidence.
- [ ] Review dependency changes; obtain required reviewers.
- [ ] Inventory and onboard every workflow that will be in the Require lockfile policy target scope; this repository currently has four workflow files, while this pilot covers only `test.yml`.
- [ ] Add `.github/workflows/actions.lock` to CODEOWNERS and verify required code-owner review / branch rules are configured.
- [ ] Evaluate the Require lockfile policy against the exact target set and confirm no targeted workflow remains un-onboarded.
- [ ] Only then consider changing Require lockfile policy from Evaluate to Active. Active policy blocks targeted workflows that are not onboarded.

## 7. Current decision

**GO:** prepare and execute an isolated, one-workflow pilot.  
**HOLD:** lockfile enforcement, broad workflow migration, and production rollout until all acceptance gates have evidence. A one-workflow pilot is not repository-wide readiness; do not activate Require lockfile across this repository while three workflows remain outside the pilot.

## 8. Reusable workflow coverage — operational interpretation

GitHub's Oct 28, 2026 GA changelog wording appears to include reusable workflow references, but the detailed GitHub Docs explicitly state that a caller's lockfile does not pin `jobs.<job_id>.uses`. The current `github/gh-actions-lock` README also lists remote reusable workflows as unsupported, and upstream issue #179 documents that the CLI can skip such calls without a finding, allowing `--verify` to pass despite the gap. Follow the detailed implementation guidance operationally: pin remote reusable workflow references to full 40-character commit SHAs, and onboard the reusable workflow source repository separately so its own dependencies are covered. Do not rely on the caller's lockfile or CLI `--verify` for remote reusable workflow coverage. The `test.yml` pilot baseline contains no remote reusable workflow calls, so this limitation does not block the narrow pilot.

## 9. Execution truth

This document and its preparation branch are committed planning artifacts only. The CLI has not been installed or executed in this environment. No `actions.lock` has been generated, no workflow has been rewritten, and no CI run has been triggered by this preparation step.
