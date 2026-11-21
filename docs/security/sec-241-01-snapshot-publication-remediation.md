# Snapshot publication security — SEC-241-01 / 02 / 03 / 04 / 05 / 06 / 07 / 08

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

## SEC-241-06 — Directory-entry durability and fsync ordering

**Observed behavior:** After no-follow descriptor-relative `mkdir` at initialization and while building the content-addressed blob prefix tree, the prior implementation did not explicitly `fsync` the parent directories of new entries. File-level `fsync` and final blob/metadata directory `fsync` alone do not guarantee new ancestor directory entries survive a crash. See https://man7.org/linux/man-pages/man2/fsync.2.html .

**Confirmed red test:** At `d2f6bdf0d08cf0aa6c99e9a2e6f40f5a2b181d0c`, `test_initialization_fsyncs_parent_of_new_store_directories` and `test_new_digest_subdirectories_fsync_parent_entries` both failed: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44913083004 .

**Draft code remediation:** `a8fa03ebadba302ad17c9a86a5ec912b0c2b24f0` calls `os.fsync(parent_fd)` after confirming the newly created or preexisting child entry via a no-follow open. The parent is synced even on `FileExistsError` to account for a concurrent writer having created a not-yet-durable directory. Any `fsync` error propagates rather than silently claiming success.

**Exact source HEAD CI evidence:** Tests https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44913152826 — SUCCESS, **643 tests OK**, including the two new cases. Validation https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44913152825 — SUCCESS.

**Remaining limitations:** These are deterministic checks of the `fsync` calls. They do **not** constitute a power-loss, storage-controller, network-filesystem, NFS or overlayfs crash-recovery test. The independently approved target-host filesystem contract, resilience to injected `fsync` failures and actual durable recovery evidence are still NOT VERIFIED. Added sync calls can affect performance and supported-filesystem compatibility and require target-host review.

## SEC-241-07 — Metadata directory fsync failure and rollback (draft)

**Observed failure:** The previous metadata publication sequence created the final metadata hard link, then called `os.fsync(metadata_fd)`. If that sync raised an `OSError`, `put_bytes` failed yet the newly created metadata entry remained visible. This is an error-recovery and evidence-admission ambiguity; it is **not** proof that a real disk crash occurred.

**Red-test evidence:** At `e1749d1b8abd7d953d83ff823a9522ed5978f24e`, `test_metadata_fsync_failure_rolls_back_uncommitted_record` failed because the final metadata file remained after an injected directory fsync failure. CI: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44934042809 — FAIL.

**Draft remediation:** Commit `85701e7e9fd75e4bb4e5a4c91c6187e71cef6a23` separates metadata `FileExistsError` collision verification from successful publication. If a newly linked metadata entry fails the durability `fsync`, the code attempts to unlink **only the entry it created** and sync the parent again. If rollback fails, it raises a clear `RuntimeError` indicating rollback was not confirmed; it does not claim success or remove a preexisting collision winner.

**CI evidence:** Tests https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44934112187 — SUCCESS, **644 tests OK**, including the red-then-green regression. A follow-up test at `684acf5b2a933214501b6ff5a7b0cc29b6614549` verifies that a second fsync failure during rollback produces the unconfirmed-durability error; Tests https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44934190852 — SUCCESS, **645 tests OK**. Refer to the exact-head Validation run when it completes.

**Limitations / HOLD:** This is **best-effort rollback**, not a transaction or power-loss atomicity guarantee. A concurrent reader could observe the metadata hard link between publication and unsuccessful sync/rollback, and a real filesystem can fail the compensating unlink or sync. Orphan blobs remain possible after metadata failure. No physical power-loss tests, actual target-mount behavior, crash recovery, customer data, or live production execution is verified. An independent reviewer must assess a transactional evidence-commit protocol or admission rule if no transient visibility of uncommitted metadata is an explicit requirement. See https://man7.org/linux/man-pages/man2/fsync.2.html .

## SEC-241-08 — Readers admit visible metadata before durability sync (CONFIRMED, UNRESOLVED)

**Controlled test evidence:** In `test_reader_does_not_admit_metadata_before_commit_sync`, the publishing writer is paused at the final metadata-directory `fsync` *after* `artifact_id.json` is hard-linked. During that pause, `get_verified(reference)` successfully returns the snapshot, instead of rejecting it as uncommitted. The red-test commit `6f5feca64df1ed598649bfdbf0762cc2a829801f` failed exactly this assertion: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/44934513803 (646 tests, one failure). No crash or real storage outage was simulated.

**Tracking:** Commit `fe8900e28a3f1362549dd55ade7281286b72b2b8` intentionally marks this *still-failing* test `@unittest.expectedFailure`. It remains an **OPEN security gate and must not be described as passing** merely because the overall CI suite may complete successfully. Remove this marker and demand a true PASS at the approved remediation HEAD.

**Why SEC-241-07 rollback is insufficient:** Undoing a metadata link *after* an `fsync` error cannot revoke data a concurrent reader has already returned. Atomic namespace visibility and crash durability are separate properties; a plain `link()` or `rename()` does not imply that the containing directory entry has been durably synchronized.

### Reviewer decision required before production-code protocol changes

The owner/security reviewer must select and explicitly specify the **admission boundary**, acceptable compatibility/migration behavior, and target-filesystem model. Candidate designs for review (not implementations):

1. **Durable metadata + explicit commit/admission record:** Make `get_verified` reject metadata lacking a validated commit record. Create or expose that record only after the underlying metadata and blob have been durably synced. Examine marker publication/fsync failure, no-overwrite semantics, marker-to-metadata identity, cross-process idempotency, and legacy records without commit markers. A commit marker visible before its own directory `fsync` may still disappear after a crash, so distinguish acknowledgment semantics from pre-sync read safety.
2. **Cross-process publication/read coordination:** Use a verified shared locking/transactional mechanism that readers and writers both honor and that supports the actual target filesystem. Review crash recovery and what happens when the writer dies while holding the lock. A thread-only mutex is insufficient for independent workers; lock semantics may differ on NFS/other mounts.
3. **Transactional store or append-only evidence ledger:** Consider an explicit committed-state index with recovery rules if the existing file-layout protocol cannot express the required guarantees. Require a data migration/replay plan; do not silently reinterpret old entries as committed.

### Acceptance criteria (NOT VERIFIED)

- [ ] The pre-commit reader test passes **without** `expectedFailure` at the exact reviewed HEAD.
- [ ] A simulated metadata `fsync` failure cannot cause the public reader API to acknowledge uncommitted evidence, including during rollback.
- [ ] Concurrent writers of identical and conflicting artifact IDs have deterministic safe outcomes, no overwrite, and no success before admission.
- [ ] The commit/admission indicator cannot be forged, followed through symlinks, or mismatched against the immutable metadata and blob.
- [ ] Crash states before/after each durability barrier have explicit replay/recovery rules; no destructive orphan cleanup without owner approval.
- [ ] Existing metadata records and third-party consumers are handled by an explicit compatibility decision, not an automatic migration.
- [ ] Multi-process target-filesystem evidence, independent exact-head security QA, and owner authorization are attached.

**Decision: SEC-241-08 OPEN / FAIL (expected-failure regression). No merge or deployment.**

## Release gates

- [x] No-follow descriptor-relative publication implementation committed to draft branch.
- [x] Targeted symlink, pinned reuse, metadata-failure and concurrent publication tests passed at the source HEAD listed above.
- [x] Targeted POSIX root/ancestor permission and secure-initialization guards tested on CI.
- [ ] Root ownership, permissions, filesystem ACL/mount behavior, and ancestor threat model approved for deployment.
- [ ] Broader concurrent/multi-process stress and supported-platform verification.
- [ ] SEC-241-08 admission-policy regression PASS (currently expected failure; NOT VERIFIED).
- [ ] Independent exact-head security review approval.
- [ ] Authorized live ComfyUI run with output integrity, immutable evidence, independent QA, and explicit owner production release approval.

**NO MERGE · NO DEPLOY · PRODUCTION HOLD.**
