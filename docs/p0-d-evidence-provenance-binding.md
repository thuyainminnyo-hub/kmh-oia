# P0-D — Evidence Provenance Binding

## Scope
P0-D binds each production evidence record to (1) the execution identity carried by its immutable ProductionJob, (2) the provider execution identifier returned by the adapter, and (3) a verified P0-C content-addressed snapshot. It does not implement model execution, semantic image QA, remote storage, signing, encryption, or production deployment.

## Dependency strategy
This is a stacked feature branch based on `feature/p0-c-verified-snapshot-storage`. The P0-C PR must be independently reviewed and merged before this branch is retargeted to `main`. No merge is performed by this change.

## Provenance contract
- Execution identity is canonical JSON with sorted keys, SHA-256 keyed; delimiter collisions are avoided.
- ProductionJob carries an ExecutionIdentityContext (identity, command ID, execution ID, originating job ID). The job validates that the context job ID matches its own ID; evidence creation rejects missing or cross-job contexts.
- Provider attribution comes only from AdapterResult / ProductionJob. A legacy caller-supplied provider ID is accepted only when exactly equal to the adapter-reported value; it cannot fill or override attribution.
- Snapshot ingestion uses P0-C VerifiedArtifactStore. The evidence manifest records snapshot storage key, artifact ID, digest, size, verification version, execution ID, command ID, and canonical identity key.
- Artifact ID is deterministically bound to the job ID (`job-<job_id>`); the manifest constructor rejects a snapshot reference belonging to a different job.
- Audit events include the complete provenance binding and remain hash chained.
- QA decisions require a prior evidence event matching both job ID and digest; the QA event links to the evidence event hash, snapshot reference, execution ID, and identity key. A second/conflicting QA decision for the same evidence event is rejected.
- Evidence manifests themselves remain `pending`; QA decisions are separate append-only audit events, not mutable evidence-manifest status. Evidence integrity is not semantic quality approval.
- QA remains `pending`; evidence integrity is not a semantic quality approval.

## Failure behavior
Missing execution context, provider-ID substitution, invalid/out-of-root artifacts, snapshot write/verification errors, or audit failures fail closed: no evidence result is returned and the job is marked failed by the pipeline.

## Tests
Focused adversarial coverage includes delimiter collision, missing identity context, adapter provider-ID substitution, missing provider attribution, job-scoped snapshot references, snapshot corruption, cross-artifact reference substitution, audit provenance fields, and pending-only QA.

## Limitations / review points
- The snapshot store is local and single-host; P0-C explicitly does not provide encryption, remote replication, or protection against privileged host administrators.
- The execution identity context is supplied by the job creator; this change binds and preserves it but does not authenticate the caller or independently attest identity.
- Provider IDs are only as trustworthy as the adapter boundary.
- The audit hash chain detects modification only when its expected head is retained independently; it is not a signed remote audit service.
- No live ComfyUI execution or production workload is claimed.
- Independent review and exact-head CI are required before any merge decision. Production remains HOLD.
