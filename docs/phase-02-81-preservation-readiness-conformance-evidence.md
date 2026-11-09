# Phase 02.81 — Preservation Readiness Assessment & Conformance Evidence Plan

**Status:** Execution plan; no prototype tests executed in this commit.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.79 preservation architecture and Phase 02.80 toolchain selection.

## 1. Objective

Before coding the preservation worker, define measurable readiness gates using current digital-preservation practice. Phase 02.81 adds an assessment baseline and independent conformance test sources so the prototype cannot declare itself successful based only on its own tests.

## 2. New research: NDSA Levels of Digital Preservation v2.1

The National Digital Stewardship Alliance (NDSA) lists Levels of Digital Preservation v2.1 as released in March 2026. Version 2.1 adds an environmental-sustainability focus and includes a matrix, implementation guidance, working definitions, sustainability guide, and assessment tool.

Reference:
- https://www.ndsa.org/activities/levels-of-digital-preservation/

Decision:
- Use NDSA Levels v2.1 as a program-readiness assessment framework, not a technical certification.
- Establish a baseline for storage, fixity, information security, metadata, and content.
- Record each control as not_started, partial, implemented, tested, or independently_evidenced.
- Do not convert an NDSA level into a single "verified" badge for an individual music object.

## 3. Independent test suites

### BagIt
Use RFC 8493 as the normative format specification and the Library of Congress BagIt Conformance Suite as independent fixture corpus:
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://github.com/LibraryOfCongress/bagit-conformance-suite

The conformance suite distinguishes valid and invalid bags, with optional warning and OS-specific cases. It also warns that Git line-ending conversion can cause BagIt validation failures; preserve exact fixture bytes and test on the target OS/filesystem.

### OCFL
Use the official OCFL 1.1 validation codes and official fixtures:
- https://ocfl.io/1.1/spec/validation-codes.html
- https://github.com/OCFL/fixtures
- https://ocfl.io/1.1/spec/

Record every fixture's expected classification and actual validator result. A validator must distinguish ERROR, WARNING, and INFO; do not collapse warnings into passes without a documented policy.

### Fixity and integrity monitoring
The Library of Congress recommends establishing fixity as early as possible and recording integrity information at both individual-file and aggregate levels:
- https://www.loc.gov/programs/digital-collections-management/inventory-and-custody/data-integrity-management/

Therefore the prototype should record:
- file-level digest and verification outcome;
- BagIt payload/tag manifest digests;
- OCFL object inventory/content digests;
- package/object-level aggregate result;
- timestamp, tool/version, agent, and source object ID.

### Security and recovery
Digital Preservation Coalition guidance links access control, action logging, audit, fixity monitoring, redundancy, repair, and recovery as complementary controls:
- https://www.dpconline.org/handbook/technical-solutions-and-tools/information-security
- https://www.archives.govt.nz/manage-information/how-to-manage-your-information/digital/best-practice-guidance-on-digital-storage-and-preservation

The prototype must separate read, write, move, and delete permissions; preserve logs for actions; and test restore from a replica rather than merely checking that a backup copy exists.

## 4. Preservation readiness baseline

Assess the pilot against these workstreams:

| Workstream | Minimum prototype evidence |
|---|---|
| Storage | Original bytes stored; object ID and location recorded |
| Fixity | SHA-256 at intake; re-read digest after write; repeatable check |
| Transfer | BagIt package validates against RFC 8493 and conformance fixtures |
| Repository | OCFL object validates against official fixture corpus |
| Security | Parser has read-only source access; archive mutation is restricted |
| Audit | Append-only ingest, validation, fixity, restore and failure events |
| Metadata | PREMIS object/event/agent/rights links schema-validated |
| Recovery | Replica restore produces matching original bytes and digest |
| Rights | Unknown rights explicitly block public distribution |
| Sustainability | Storage, software, and environmental trade-offs documented |

## 5. Prototype test sequence

1. Create a synthetic MIDI fixture and record its SHA-256 and byte length.
2. Create a BagIt package; validate it with bagit-python.
3. Run the official BagIt conformance suite; retain per-fixture outcomes.
4. Run deliberate payload tampering, missing-file, extra-file, and tag-manifest corruption tests.
5. Create an OCFL 1.1 object using the selected candidate implementation.
6. Run the official OCFL good/bad/warn fixture corpus; retain per-code outcomes and coverage gaps.
7. Create a metadata-only second version; prove version 1 content is unchanged.
8. Generate PREMIS 3.0 XML and validate against official XSD; run semantic relationship assertions.
9. Copy the object to an independent replica and restore into a clean directory.
10. Recalculate source and restored-file hashes; record all evidence in the preservation event ledger.

## 6. Pass/fail policy

- **PASS:** expected result matches actual result and machine-readable evidence is retained.
- **FAIL:** unexpected result, checksum mismatch, lost payload, broken version history, failed restore, or missing mandatory metadata.
- **WARN:** standards fixture is classified as warning or a validator reports a documented non-fatal limitation; warnings remain visible.
- **NOT TESTED:** no execution evidence exists. Documentation alone is not a pass.
- **NOT APPLICABLE:** only with a written rationale and owner approval.

No aggregate "verified" status may be issued if a mandatory control is FAIL or NOT TESTED.

## 7. Exit criteria

- NDSA v2.1 baseline assessment completed for the pilot scope.
- BagIt official conformance fixture results retained.
- OCFL official fixture results retained, including unsupported validation codes.
- PREMIS XSD and semantic validation pass.
- Tamper tests detect all deliberate changes.
- Restore test reproduces exact original bytes.
- Security permissions prevent parser mutation of source objects.
- Rights status is explicit and public distribution is blocked while unknown.
- Every result is tied to exact source commit, tool version, fixture hash, and test run.

## 8. Decision

Use NDSA v2.1 to measure program maturity; use RFC 8493/BagIt conformance fixtures, OCFL official validation fixtures, and PREMIS XSD to test technical correctness; use Library of Congress fixity guidance to shape monitoring. Proceed to a local synthetic-fixture worker only after this acceptance matrix is agreed. No production readiness or standards conformance is claimed by this plan.
