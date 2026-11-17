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

The implementation deliberately fails closed if atomic hard-link publication is
not supported. It does not fall back to a potentially overwriting copy operation.

## Retrieval and recovery

- `verify(reference)` checks the metadata record and recomputes the blob digest
  and byte count.
- `get_verified(reference)` returns bytes only after verification and checks
  the bytes again after reading.
- `recover()` trusts only metadata records whose referenced blobs pass digest
  and size verification. Orphan blobs and staging files are not admitted.

## Security boundary

This is a local storage primitive, not a complete production artifact service.
It is not encrypted, remotely replicated, signed, or protected from a privileged
host administrator. Directory fsync is used on POSIX; Windows directory fsync
is skipped. Filesystem durability and hard-link semantics must be validated on
the actual deployment filesystem before production use.

## Verification

```bash
python -m unittest tests.test_verified_snapshot_store -v
python -m unittest discover -s tests -v
```

Tests are not considered passed until executed on the exact feature-branch
revision and CI reports success.
