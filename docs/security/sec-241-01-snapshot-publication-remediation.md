# Snapshot publication security — SEC-241-01 / 02 / 03 / 04 / 05

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

## Root ancestor trust-policy implementation (draft)

At source commit `f75b08b2f0c0e9254f356befdf431ddfa0a34ac0`, the no-follow publication opener checks each ancestor using its **opened directory descriptor**. Untrusted ancestor owners and group/other-writable directories **without** the sticky bit fail closed. The store root and its blob/staging/metadata children require ownership by the process effective UID and no group/other write permissions.

Trusted sticky parents such as root-owned `/tmp` may be accepted to preserve standard POSIX temp-directory compatibility. This is not a general claim that sticky directories are a secure place for multi-tenant evidence: the directory owner, process owner, privileged actors, filesystem ACLs, mount semantics, and same-UID processes still matter. This code makes **no automatic chmod/chown changes** to existing deployment directories.

Targeted CI evidence for `f75b08b2f0c0e9254f356befdf431ddfa0a34ac0`:
- Tests: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44911815626 — SUCCESS, 638 tests OK.
- Validation: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44911815572 — SUCCESS.
- The test log explicitly confirms `test_rejects_nonsticky_writable_store_ancestor` and `test_allows_sticky_writable_ancestor_for_private_store` passed.

**Remaining gate:** Independent review must confirm this owner/mode/sticky policy against actual service accounts, ACLs, NFS/shared mounts, parent directory ownership, and real production storage. These local POSIX tests do not establish production filesystem compatibility or release authorization.

## SEC-241-04 — Secure initialization (new)

**Confirmed red test:** At `96c8f1cfd574a646fd93f2c417591115e63b7dec`, `test_initializer_does_not_create_store_under_untrusted_parent` failed with `PermissionError not raised`. Initialization had already created directories through `Path.mkdir()` before the publication-time trust checks.

**Draft remediation:** `ba02abcef8dafeb7f6e11393f1390247156c86fb` replaces path-based initialization with `_initialize_store_directories()`, traversing from the filesystem root using pinned parent descriptors. It checks each existing ancestor's trust before `os.mkdir(..., dir_fd=parent_fd, mode=0o700)`, opens each new/existing directory with `O_DIRECTORY | O_NOFOLLOW`, validates private ownership/modes, and does not automatically `chmod` or `chown` existing deployment paths.

**Exact-head verification:** Tests https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44912132860 — SUCCESS, **639 tests OK**, including the new initializer regression. Validation https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44912132912 — SUCCESS.

This verifies the explicit test fixture, not all possible initialization races, symlinked configuration aliases, ACL/mount behavior, or the actual production environment. **Independent owner/security review is still required.**

## SEC-241-05 — Configured root symlink aliases (draft)

**Confirmed behavior:** The previous initializer used `Path(root).expanduser().resolve()`, which followed symlinks in the caller-supplied root path **before** the no-follow directory traversal. Consequently the original configured path's symlink components could be accepted as a resolved target.

**Red-test evidence:** At `331200e09c973a271aeaace3c4cccb65e2e2a63f`, `test_initializer_rejects_configured_root_symlink` and `test_initializer_rejects_configured_ancestor_symlink` both failed with `AssertionError: ... not raised`: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44912831321 .

**Draft remediation:** At `bc54661dc4d136a02e63c0a4150f578f474a16d2`, the initializer uses `os.path.abspath(Path(root).expanduser())` rather than `Path.resolve()`. This preserves symlink components for the existing `O_DIRECTORY | O_NOFOLLOW` descriptor-relative initialization checks. The Tests workflow log reports **641 tests OK** and both targeted regressions PASS: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44912883594 .

**Compatibility warning:** Intentionally configured symlink paths to the snapshot store now fail closed. Before deployment, the owner must inspect existing configuration and explicitly provision the real approved path rather than silently permit a symlink alias. Do not alter production symlinks, mount points, or storage contents automatically. Confirm the final exact-head Validation workflow separately.

**Remaining limitations:** Passing fixtures do not prove real host ACL/mount compatibility, absence of same-UID adversaries, or independent security approval.

## Release gates

- [x] No-follow descriptor-relative publication implementation committed to draft branch.
- [x] Targeted symlink, pinned reuse, metadata-failure and concurrent publication tests passed at the source HEAD listed above.
- [x] Targeted POSIX root/ancestor permission and secure-initialization guards tested on CI.
- [ ] Root ownership, permissions, filesystem ACL/mount behavior, and ancestor threat model approved for deployment.
- [ ] Broader concurrent/multi-process stress and supported-platform verification.
- [ ] Independent exact-head security review approval.
- [ ] Authorized live ComfyUI run with output integrity, immutable evidence, independent QA, and explicit owner production release approval.

**NO MERGE · NO DEPLOY · PRODUCTION HOLD.**
