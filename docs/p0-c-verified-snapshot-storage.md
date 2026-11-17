# P0-C — Verified Snapshot Storage

Status: IMPLEMENTED ON FEATURE BRANCH; LOCAL TEST EXECUTION AND CI VALIDATION PENDING

## Scope

`src/verified_snapshot_store.py` introduces a local, single-host content-addressed
store for production artifacts. It keeps artifact identity (`artifact_id`)
separate from byte identity (`sha256`).

## Ingestion and publication

1. Resolve the source and enforce containment under the caller-supplied allowed root.
2. Open the resolved regular file and read it once.
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
- Symlinked storage entries are rejected; source-file descriptor metadata is
  compared before and after ingest to detect observed mutation.
- Trusted metadata reads are capped at 16 KiB before JSON parsing to bound
  metadata-driven memory consumption.

## Security boundary

This is a local storage primitive, not a complete production artifact service.
It is not encrypted, remotely replicated, signed, or protected from a privileged
host administrator. The snapshot root and its parent directories must be
writable only by the trusted service identity; this implementation does not
provide protection against a hostile process with write access to the store.
Directory fsync is used on POSIX; Windows directory fsync
is skipped and no-follow guarantees depend on platform support. Filesystem
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
