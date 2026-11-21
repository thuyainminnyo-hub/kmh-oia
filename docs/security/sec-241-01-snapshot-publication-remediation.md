# Snapshot publication security — SEC-241-01 / SEC-241-02 / SEC-241-03

**Status: OPEN — targeted implementation and CI verification completed; operational trust policy and independent security review NOT VERIFIED.**

This file is an evidence and reviewer handoff, **not** an authorization to merge, deploy, or release. Production remains **HOLD**.

## Scope and implemented controls

The original PR #241 read implementation bounded snapshot files and rejected symlink traversal, while write publication used path-based operations. Draft PR #246 (based on PR #241) adds:

- Descriptor-relative no-follow traversal for the store root and ancestors.
- A pinned root directory descriptor shared by blob, staging, and metadata publication.
- Descriptor-relative temporary-file creation, hard-link publication, and cleanup.
- Pinned-directory bounded verification of existing blob and metadata entries; no path-based re-open in the write-time collision branches.
- Fail-closed checks for required `os.supports_dir_fd`, `os.supports_follow_symlinks`, and `O_NOFOLLOW`/directory flags.
- Tests for symlink replacement, existing entry integrity, root replacement at deduplication, metadata failure injection, and concurrent writers.

## Verified CI evidence

At test commit `6a4f84d74efdc3ce35292a33d7f3528c682021fc`:

- KMH OIA Tests: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44903690812 — SUCCESS.
- KMH OIA Validation: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44903690819 — SUCCESS.
- The unittest log reported **632 tests, OK**, including `test_concurrent_identical_publication_is_consistent` and `test_concurrent_conflicting_artifact_ids_do_not_overwrite`.

These checks are deterministic tests and bounded concurrent fixtures, not proof against all adversarial scheduling or production attacker access.

## Operational trust-model decisions still needed

1. **Ownership and write permissions.** Define a dedicated process/service identity, required owner/group/modes for root, `sha256`, `artifacts`, and `.staging`. In the default conservative model, untrusted users/groups must not have write permission in these directories. Determine whether shared-group writes are ever authorized. Do not silently `chmod` or `chown` existing customer deployments.
2. **Ancestor protection.** Identify who can rename or substitute any store-root ancestor. A directory descriptor pins an object after opening it, but this alone does not guarantee that its pathname remains accessible or controlled. Ensure storage mount/parent directories are provisioned and governed by trusted actors.
3. **Platform contract.** State supported OS/filesystems. Descriptor-relative APIs are platform-dependent. Unsupported configurations must fail closed, not silently fall back.
4. **Evidence identity and durability.** Define owner-approved recovery for blob publication that succeeds before metadata. The orphan blob is not a committed evidence record. Define backup, crash recovery, durability, and retention; no automatic destructive cleanup without authorization.
5. **Threat model.** Document whether other processes or tenants can create, rename, chmod, chown, or replace store components, and whether attackers can modify the running process's credentials or memory. Directory-descriptor hardening does not defend against a fully compromised same-privilege process.
6. **Independent review.** Examine file descriptor lifecycle, collision behavior, concurrent root replacement, filesystem permissions, and realistic storage mounts, with exact-head evidence and severity/disposition. Check PR #147 scope separately.

## Release gates

- [x] No-follow descriptor-relative publication implementation committed to draft branch.
- [x] Targeted symlink, pinned reuse, metadata-failure and concurrent publication tests passed at the source HEAD listed above.
- [ ] Root ownership, permissions, and ancestor threat model approved and enforced.
- [ ] Broader concurrent/multi-process stress and supported-platform verification.
- [ ] Independent exact-head security review approval.
- [ ] Authorized live ComfyUI run with output integrity, immutable evidence, independent QA, and explicit owner production release approval.

**NO MERGE · NO DEPLOY · PRODUCTION HOLD.**
