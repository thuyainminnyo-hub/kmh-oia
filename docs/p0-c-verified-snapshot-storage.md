# P0-C — Verified Snapshot Storage

Status: IMPLEMENTED ON FEATURE BRANCH; exact-head GitHub CI verified on commit `424cd2a6d29fb30fbd0a725e6d84c55dc6154ac4` (594 repository tests passed; Tests and Validation workflows passed).

## Scope

`src/verified_snapshot_store.py` introduces a local, single-host content-addressed
store for production artifacts. It keeps artifact identity (`artifact_id`)
separate from byte identity (`sha256`).

## Ingestion and publication

1. Normalize the source path lexically and enforce containment under the caller-supplied allowed root without resolving source symlinks.
2. Open the allowed root as a directory descriptor, traverse each intermediate component relative to its parent descriptor with `O_DIRECTORY | O_NOFOLLOW`, then open the final file with `O_NOFOLLOW`; validate the opened descriptor with `fstat()` before reading.
3. Hash and copy the same byte stream into a staging file; compare descriptor identity,
   size, and nanosecond timestamps before and after ingestion to reject observed
   concurrent source mutation.
4. Flush and fsync the staged file.
5. Publish the digest-addressed blob with an atomic hard link that does not
   overwrite an existing blob. If the digest already exists, re-read and verify it.
6. Atomically publish the artifact metadata record, then fsync its directory.
7. Reject symlinked blob and metadata entries on trusted reads; blob verification
   streams data in bounded chunks rather than loading the entire file into memory.

The implementation deliberately fails closed if atomic hard-link publication is
not supported. It does not fall back to a potentially overwriting copy operation.

## Retrieval and recovery

- `verify(reference)` checks the metadata record and recomputes the blob digest
  and byte count.
- `get_verified(reference)` returns bytes only after verification and checks
  the bytes again after reading.
- `recover()` trusts only metadata records whose referenced blobs pass digest
  and size verification. Orphan blobs and staging files are not admitted.
- Concurrent writers deduplicate by digest; metadata identity remains unique.
- Symlinked source-file and intermediate-directory components are rejected during descriptor-relative traversal; storage entries are also rejected on trusted reads.
- Source-file descriptor metadata is compared before and after ingest to detect observed mutation.
- Source ingestion fails closed on platforms without the required `O_NOFOLLOW`, `O_DIRECTORY`, and descriptor-relative `open` support.
- Trusted metadata reads are capped at 16 KiB before JSON parsing to bound
  metadata-driven memory consumption.

## Security boundary

This is a local storage primitive, not a complete production artifact service.
It is not encrypted, remotely replicated, signed, or protected from a privileged
host administrator. The snapshot root and its parent directories must be
writable only by the trusted service identity; this implementation does not
provide protection against a hostile process with write access to the store.
Directory fsync is used on POSIX; Windows directory fsync is skipped. Source ingestion requires no-follow descriptor-relative open support and fails closed when unavailable. Filesystem
symlink protections, durability, and hard-link semantics must be validated on
the actual deployment filesystem before production use.

## Verification

```bash
python -m unittest tests.test_verified_snapshot_store -v
python -m unittest discover -s tests -v
```

Tests cover content identity, concurrent deduplication, path escape, empty/missing
inputs, duplicate artifact IDs, corrupted blobs, metadata substitution, symlink
rejection, and recovery. Tests are not considered passed until executed on the
exact feature-branch revision and CI reports success.
