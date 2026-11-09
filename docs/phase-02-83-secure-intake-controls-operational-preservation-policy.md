# Phase 02.83 — Secure Intake Controls & Operational Preservation Policy

**Status:** Research-backed implementation specification; no runtime code or preservation tests executed.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phases 02.79–02.82.

## 1. New research findings

### 1.1 BagIt implementation version and validation behavior
The Library of Congress `bagit-python` release page currently identifies **v1.9.0** as the latest release. Its change notes include CLI test improvements, path-safety changes (removing environment-variable expansion from unsafe-path checking), and validation process handling. The repository documentation confirms that the library can create and validate bags, supports SHA-256/SHA-512 manifests by default, and reports checksum mismatch, missing payload files, and unexpected payload files.

References:
- https://github.com/LibraryOfCongress/bagit-python/releases
- https://github.com/LibraryOfCongress/bagit-python

Decision:
- Evaluate and pin `bagit==1.9.0` in a locked prototype environment; do not install an unpinned latest version.
- Treat the library's validation as one layer. Run the LOC conformance suite separately.
- Capture the exact package version, Python version, dependency lock/hash, OS and filesystem in every run receipt.

### 1.2 Fixity should be established at intake and at aggregate level
Library of Congress guidance recommends creating fixity as early as possible in acquisition and retaining integrity information at both file and aggregate levels. Integrity checks and their logs should remain auditable for as long as collection content is retained.

Reference:
- https://www.loc.gov/programs/digital-collections-management/inventory-and-custody/data-integrity-management/

Decision:
- Calculate SHA-256 and byte length from the opened source stream before packaging.
- Calculate the staged payload SHA-256 independently after writing and compare.
- Validate BagIt manifests.
- Record file-level and bag-level outcomes; never infer that one file digest proves all package metadata and payload members are intact.
- Preserve logs/results as durable evidence, with run ID, timestamp, agent, software version, and source commit.

### 1.3 Quarantine, copies, periodic fixity, and recovery
Digital Preservation Coalition guidance recommends quarantine for untrusted content, a verifiable file inventory, multiple copies across different locations/media where feasible, periodic fixity checking, and test recoveries of backups. It also notes write-blocking or read-only source controls where applicable.

References:
- https://www.dpconline.org/handbook/getting-started
- https://dpconline.b-cdn.net/handbook/technical-solutions-and-tools/fixity-and-checksums
- https://www.archives.govt.nz/manage-information/how-to-manage-your-information/digital/best-practice-guidance-on-digital-storage-and-preservation

Decision:
- Phase 02.83 Gate A must not be described as a complete preservation service.
- The worker must stage and validate content before acceptance.
- A successful local BagIt validation is not proof of redundancy or recoverability.
- Schedule periodic fixity and restore drills only after a real repository and replica policy are approved.

### 1.4 NDSA v2.1 is a program assessment framework
NDSA v2.1 was released on 23 March 2026 and adds an Environmental Sustainability Guide, including decision points linked to Storage, Integrity, and Content. It also clarifies that Level 4 need not be the goal for every organization or functional area.

References:
- https://www.ndsa.org/activities/levels-of-digital-preservation/
- https://www.ndsa.org/2026/03/23/announcing-version-2_1-of-the-ndsa-levels-of-digital-preservation.html

Decision:
- Use the NDSA assessment tool to identify staged capability improvements.
- Document storage redundancy, access frequency, retention, and energy/cost trade-offs.
- Do not call NDSA a product certification or use it to assert that an individual object is authentic.

## 2. Gate A implementation contract

Create a standalone command:

`python -m scripts.preservation_ingest --source <path> --object-id <id> --workspace <path>`

The worker remains format-agnostic and treats payload as opaque bytes. It must not import or call the MIDI parser.

### Required sequence

1. Validate the object ID against a narrow allowlist (e.g. ASCII letters, digits, hyphen, underscore; fixed maximum length).
2. Resolve and validate the configured source root and workspace root.
3. Open the source safely without following symlinks where supported; compare file identity/metadata before and after streaming to detect source replacement or mutation during capture.
4. Stream source bytes once into a newly created staging file while calculating SHA-256 and byte length.
5. Flush and close the staged file; re-open it read-only and independently recalculate SHA-256 and length.
6. Compare source-stream and staged-file digest/length; fail closed on mismatch.
7. Build the BagIt package from the staged copy, never from the live source path.
8. Validate the bag using bagit-python 1.9.0 and capture structured diagnostics.
9. Run the LOC BagIt Conformance Suite in a separate CI job, preserving exact fixture bytes and platform details.
10. Write a machine-readable receipt and mark the object accepted only after every mandatory Gate A check passes.

### Atomicity and collision rules

- Create the per-object staging directory atomically with exclusive creation; never reuse an existing object ID.
- Use a temporary sibling directory and atomic rename for final acceptance on the same filesystem, where supported.
- Do not claim a cross-filesystem rename is atomic.
- Never overwrite an existing accepted object.
- On failure, preserve a quarantined diagnostic bundle under a distinct run ID; do not leave a partially accepted object.
- Do not delete source or quarantine material automatically in the prototype.

### Path and permission rules

- Treat source filename as display metadata, not as a path component.
- Reject path separators, traversal components, absolute paths, NUL bytes, symlink sources, and special files.
- Use resolved, workspace-contained paths and exclusive file creation.
- Do not assume path checks alone prevent time-of-check/time-of-use races; operate on opened file descriptors and verify identity where the platform permits.
- Separate read access to source/staging from write access to archive acceptance areas.
- The MIDI parser and downstream analysis receive read-only references only.

## 3. Receipt schema

Required fields:
- schema: `kmh.preservation-intake-receipt.v1`
- run_id, object_id
- source_name (display only)
- source_byte_length, source_sha256
- staged_byte_length, staged_sha256
- bagit_version, manifest_algorithms
- validation_tool, validation_tool_version, validation_status
- started_at_utc, completed_at_utc
- worker_version, source_commit
- os, filesystem, python_version
- result: accepted, rejected, quarantined, not_tested
- stable error_code and diagnostics
- evidence artifact paths and hashes

Rights must default to `unknown`; no public-distribution flag may be set by Gate A.

## 4. Required test matrix

| Case | Expected outcome |
|---|---|
| Valid synthetic MIDI fixture | accepted |
| Source mutates during copy | rejected/quarantined |
| Source is symlink | rejected |
| Source is FIFO/device/directory | rejected |
| Path traversal/object ID traversal | rejected |
| Duplicate object ID | rejected without overwrite |
| Staged byte differs from source stream | rejected |
| Payload byte tampered after bag creation | validation failure |
| Payload missing | validation failure |
| Unexpected payload added | validation failure |
| Tag manifest corrupted | validation failure |
| Interrupted write | quarantined, never accepted |
| Re-run with a new object ID | identical payload digest |

## 5. Acceptance and claim policy

Gate A is complete only when:
- source and staged bytes match exactly;
- source file remains unchanged;
- BagIt package passes library validation;
- tampering, missing, unexpected, and corrupted-tag cases are detected;
- all failure cases fail closed;
- receipts and logs are machine-readable and tied to exact tool/build context.

Gate A does **not** establish:
- OCFL conformance;
- PREMIS conformance;
- long-term fixity monitoring;
- independent replica or disaster recovery;
- rights clearance;
- authenticity of authorship;
- correctness of transcription or musical interpretation;
- production readiness or NDSA certification.

## 6. Decision

Proceed with Gate A implementation using the existing deterministic synthetic MIDI fixtures. Pin `bagit==1.9.0` only after dependency/license review and conformance tests. Keep OCFL, PREMIS, replica storage, periodic fixity, and rights-aware publication as subsequent gates. No production dependency, deployment, or real collection ingest is approved by this specification.
