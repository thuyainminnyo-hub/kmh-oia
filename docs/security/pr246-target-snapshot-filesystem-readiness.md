# PR #246 — Target-host snapshot filesystem readiness (read-only evidence handoff)

**State: NOT RUN ON TARGET HOST / NOT VERIFIED. Production HOLD.**

This checklist is for the **approved target host**, service account, and deployed snapshot-store path. GitHub Actions runs test disposable runner filesystems; they do not verify the target's storage mounts, ACLs, service identity, or durability. This document is not permission to access a target host or modify production storage.

## 1. Scope, approval, and evidence custody

Before collecting evidence, an authorized operator must identify:
- Target environment and host/service identity (**keep privately**), intended service effective UID/GID, immutable application commit SHA, intended store root path, and mount/volume owner.
- Expected operating system, Python version, filesystem type, storage persistence/backup and tenant isolation policies.
- The independent reviewer and destination for **private**, access-controlled evidence. Do not commit raw host paths, user/group names, mount sources, secrets, or private data to the public repository.

Run the following **read-only inspection commands** only when authorized and under the same service identity/container/mount namespace used by the actual workload. Set `SNAPSHOT_ROOT` to the real existing store root in the approved shell. **These commands must not create, chmod, chown, mount, unlink, publish, or repair anything.**

```sh
: "${SNAPSHOT_ROOT:?Set an approved existing snapshot root before running}"
date -u +'%Y-%m-%dT%H:%M:%SZ'
id
python -V
python - <<'PY'
import os, platform
print("os=", platform.platform(), "effective_uid=", os.geteuid() if hasattr(os, "geteuid") else "unsupported")
print("O_NOFOLLOW=", bool(getattr(os, "O_NOFOLLOW", 0)))
print("O_DIRECTORY=", bool(getattr(os, "O_DIRECTORY", 0)))
print("dir_fd_support=", {name: getattr(os, name) in os.supports_dir_fd for name in ("open", "mkdir", "link", "unlink")})
print("no_follow_hard_link=", os.link in os.supports_follow_symlinks)
PY
namei -l "$SNAPSHOT_ROOT"
for item in "$SNAPSHOT_ROOT" "$SNAPSHOT_ROOT/sha256" "$SNAPSHOT_ROOT/artifacts" "$SNAPSHOT_ROOT/.staging"; do
    stat -c 'type=%F owner_uid=%u owner_gid=%g mode=%a dev=%d inode=%i' "$item"
    getfacl -p "$item"
done
findmnt --target "$SNAPSHOT_ROOT" -o TARGET,SOURCE,FSTYPE,OPTIONS
```

If `namei`, `getfacl`, `stat`, or `findmnt` is unavailable, mark the corresponding observation **NOT VERIFIED** and use a separately approved equivalent; do not infer PASS. The commands above may reveal internal names, storage sources, or identifiers: retain raw results privately and publish only a reviewed/redacted status.

## 2. Reviewer interpretation

| Question | Acceptance condition |
| --- | --- |
| Exact artifact | Running service/image matches the reviewed immutable SHA (not just a branch name); record the evidence method |
| Root and children | Root, `sha256`, `artifacts`, `.staging` are actual directories owned by the effective service UID, with no group/other write bits |
| Ancestor path | All ancestors are reviewed for symlinks, ownership and writable modes. Trusted sticky directories must have documented owner/namespace assumptions; untrusted or nonsticky writable ancestors are BLOCKED |
| ACLs | Inspect access **and default** ACLs and effective masks, including named-user/group grants. Do not claim that ACLs universally bypass mode bits; resolve the actual effective access policy |
| Filesystem and mounts | Identify filesystem type, actual mount/volume, namespace, NFS/overlay/shared storage, backup and persistence arrangements; inspect applicable fsync/link semantics with the platform owner |
| Supported runtime | Running service Python/OS supports required descriptor-relative/no-follow operations and expected exceptions |
| Other actors | Confirm whether other processes share the service UID, hold privileged capabilities, or can modify root ancestors; decide whether that is in threat-model scope |
| Evidence provenance | UTC timestamp, tested SHA, operator, independent reviewer, observed environment, redaction and private evidence URI recorded |
| Authorization | No deployment or live execution claims until separate release gates and owner authorization are satisfied |

**Important limitations:** `stat` and `getfacl` outputs are observations, not atomic proof against concurrent mutations. POSIX mode checks alone do not establish a complete ACL, privileged-actor, mount or shared-UID threat model. Root-owned sticky directories such as `/tmp` may be permitted by the current code; this is not a blanket production approval for such locations.

## 3. Write/durability tests require separate approval

Read-only inspection **cannot prove** hard-link atomicity, cross-process correctness, directory `fsync` durability, failover, or crash recovery on the actual filesystem. An approved target-host test must use a **dedicated disposable scratch root** on the actual intended mount and independent operators/QA. It must not modify existing customer artifacts or execute a live ComfyUI job without separate owner authorization.

Record: filesystem/mount type, commit SHA, OS/Python version, scenario IDs, command/test version, start/end UTC, error/output, cleanup approval and independent reviewer disposition. Missing evidence is **NOT VERIFIED**, not PASS.

## 4. Decision and next action

- **Code and CI:** PR #246 has targeted tests for directory no-follow, ownership, root substitution, deduplication, and concurrent thread/process publication; confirm the current exact-head CI at review time.
- **Target filesystem:** **NOT VERIFIED** until the operator supplies the evidence described here.
- **Independent security review:** **NOT VERIFIED** until exact-head approval is recorded.
- **Live ComfyUI evidence / external output integrity / immutable audit / owner release:** **NOT VERIFIED / HOLD** until independently satisfied.

**NO MERGE · NO DEPLOY · PRODUCTION HOLD.**

## Reference documentation

- Python directory descriptor and platform capability support: https://docs.python.org/3.12/library/os.html
- Linux directory entry/path modes: https://man7.org/linux/man-pages/man1/namei.1.html
- Linux mount inspection: https://man7.org/linux/man-pages/man8/findmnt.8.html
- Linux POSIX ACL semantics: https://man7.org/linux/man-pages/man5/acl.5.html
- Linux ACL inspection: https://man7.org/linux/man-pages/man1/getfacl.1.html
- Linux fsync and directory durability: https://man7.org/linux/man-pages/man2/fsync.2.html
