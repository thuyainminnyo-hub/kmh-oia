# Phase 02.82 — Evidence-Preserving Ingest Worker: Implementation Blueprint

**Status:** Implementation blueprint grounded in current repository inspection; no runtime code added in this commit.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.79 preservation architecture, Phase 02.80 toolchain spike, Phase 02.81 readiness matrix.

## 1. Repository facts inspected

The current branch already contains:
- deterministic synthetic MIDI golden fixtures in `tests/test_midi_parser_golden.py`;
- a fixture inventory and expected SHA-256 values in `tests/fixtures/midi_golden_manifest.json`;
- `scripts/midi_fixture_evidence.py` for runtime fixture hash evidence;
- `scripts/midi_independent_oracle.py` for Mido cross-checks;
- a GitHub Actions workflow `.github/workflows/midi-fixture-evidence.yml`.

These assets should be reused as synthetic inputs. Do not create or download copyrighted music files for the first preservation prototype.

The current repository does not yet contain a BagIt/OCFL/PREMIS preservation worker. The existing fixture evidence scripts are not a preservation archive and must not be described as one.

## 2. Research corrections to carry into implementation

### OCFL digest roles
OCFL uses a primary content-addressing digest of SHA-512 or SHA-256 and recommends SHA-512. Additional fixity digests are recorded separately in the inventory fixity block. Do not describe the two digest roles as interchangeable:
- BagIt payload and tag manifests: SHA-256 initially, with SHA-512 also evaluated.
- OCFL inventory content-addressing: SHA-512 preferred.
- Independent preservation receipt: retain SHA-256 as a separately scoped intake/fixity value.
- OCFL inventory sidecar: use the same algorithm declared by the inventory and compute the sidecar only after the inventory is final.

References:
- https://ocfl.io/1.1/spec/
- https://ocfl.io/1.1/implementation-notes/
- https://www.loc.gov/programs/digital-collections-management/inventory-and-custody/data-integrity-management/

### PREMIS evidence
PREMIS 3.0 models Objects, Events, Rights, and Agents. Event outcome details can preserve validation anomalies and pointers to logs. XSD validation checks XML structure; application-level checks must additionally verify that events link to the intended objects and agents.
- https://www.loc.gov/standards/premis/v3/
- https://www.loc.gov/standards/premis/schemas.html

### BagIt conformance
Use RFC 8493 and the Library of Congress BagIt Conformance Suite. The suite includes valid, invalid, warning, and OS-specific cases. Preserve fixture bytes exactly; Git line-ending conversion can invalidate test bags.
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://github.com/LibraryOfCongress/bagit-conformance-suite

## 3. Worker boundary

Create a standalone Python CLI/worker, isolated from the web runtime:

`python -m scripts.preservation_ingest --source <path> --object-id <id> --workspace <path>`

The CLI should:
- accept one source file and an explicit object identifier;
- copy source bytes into a new staging area without modifying the input;
- reject path traversal, symlink source files, duplicate object IDs, and writes outside the configured workspace;
- calculate source byte length and SHA-256 before packaging;
- create a BagIt package with exact payload bytes;
- validate the bag using the selected BagIt library and/or conformance harness;
- emit a machine-readable JSON receipt and structured log;
- leave the staged source and failure report intact when validation fails, under the prototype's controlled test retention policy.

Do not let the worker parse MIDI. Preservation intake must be format-agnostic and treat payload as opaque bytes.

## 4. Proposed output layout

```text
workspace/
  staging/
    <object-id>/
      source.bin
      intake-receipt.json
      bag/
        bagit.txt
        bag-info.txt
        manifest-sha256.txt
        tagmanifest-sha256.txt
        data/
          source/original.mid
  reports/
    <object-id>/
      bag-validation.json
      ingest-events.json
```

This is a prototype workspace layout, not an OCFL object layout. Do not call it an OCFL repository until a standards-conformant OCFL object and storage root are created and independently validated.

## 5. Minimum receipt schema

- schema: `kmh.preservation-intake-receipt.v1`
- object_id
- source_filename (display metadata only; never trusted as path)
- source_byte_length
- source_sha256
- bagit_version
- bag_manifest_algorithms
- bag_validation_status
- bag_validation_tool and version
- ingest_timestamp_utc
- worker_version / source commit
- result: accepted, accepted_with_warnings, rejected, or not_tested
- diagnostics and evidence artifact references

Do not include sensitive depositor details in fixture receipts. Add rights metadata only from explicit input; otherwise set rights status to `unknown`.

## 6. Test plan

### Positive cases
1. Ingest one valid synthetic MIDI fixture.
2. Confirm source file bytes and staged payload bytes are identical.
3. Confirm SHA-256 and byte length in receipt.
4. Confirm BagIt manifests validate.
5. Confirm the input source file remains unchanged.
6. Repeat the same ingest with a new object ID and confirm deterministic payload digests.

### Negative/security cases
1. Missing source file.
2. Source is a symlink.
3. Source path resolves outside allowed input root.
4. Object ID already exists.
5. Attempted path traversal in object ID.
6. Tampered payload after manifest creation.
7. Missing payload file.
8. Unexpected unmanifested payload.
9. Corrupt tag manifest.
10. Insufficient write permission / interrupted write.

Every failure must produce a stable error code and a durable diagnostic receipt; no invalid object may be marked accepted.

## 7. Later gates — not part of the first worker

### Gate B — OCFL
Only after BagIt intake passes:
- create OCFL object/storage root using the selected implementation;
- use OCFL v1.1 declaration;
- use SHA-512 as the OCFL primary digest unless a documented interoperability reason selects SHA-256;
- keep the independent intake SHA-256 as separate fixity evidence;
- validate against official OCFL fixtures;
- prove metadata-only v2 does not mutate v1.

### Gate C — PREMIS
- serialize Object, Event, Agent, and Rights entities;
- validate against official PREMIS 3.0 XSD;
- add semantic link and chronology tests;
- preserve validation output/log references in event outcome detail.

### Gate D — Recovery
- restore from a physically or logically independent replica;
- verify exact source digest and byte length;
- record restore as a PREMIS event;
- do not count a simple second copy as a successful restore test.

## 8. Acceptance criteria for Gate A

- A valid synthetic source can be ingested without modifying the original.
- The source SHA-256 and byte length match the staged payload.
- BagIt validation passes with machine-readable evidence.
- Tampering, missing files, extra files, and manifest corruption are detected.
- Unsafe paths and symlink inputs are rejected.
- Every result is tied to source commit, tool version, and fixture hash.
- No OCFL, PREMIS, production, real-collection, or rights-clearance claim is made before those gates pass.

## 9. Decision

Implement Gate A only, using the existing synthetic MIDI golden fixture set. Keep the preservation worker format-agnostic and independent from the MIDI parser. Do not begin OCFL or PREMIS runtime integration until BagIt package creation, validation, tamper detection, and immutable source handling have repeatable evidence.
