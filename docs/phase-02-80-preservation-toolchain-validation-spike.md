# Phase 02.80 — Preservation Toolchain Selection & Validation Spike

**Status:** Research-backed execution plan; no dependencies or runtime code added.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.79 PREMIS + BagIt + OCFL architecture.

## 1. Objective

Choose a low-cost, testable toolchain for a local synthetic-fixture prototype before selecting cloud storage, adding dependencies to production, or ingesting real cultural heritage material.

## 2. Updated standards status

- OCFL's latest published specification is still designated v1.1. The editors published patch revision **v1.1.1** on 7 November 2024. The object/storage-root conformance declaration remains v1.1; v1.1.1 provides clarifications, including filesystem case-sensitivity guidance and fixity distinctions.
- Do not label the OCFL object declaration "1.1.1"; use the version required by the published specification (v1.1), while documenting that the implementation follows the v1.1.1 patch text.
- BagIt 1.0 is specified by RFC 8493. The Library of Congress bagit-python implementation supports creation and validation and defaults to SHA-256 and SHA-512 manifests.
- OCFL Python tooling (ocfl-py) provides object/root manipulation and validation for v1.1, but publishes an implementation status matrix for errors and warnings. It must be treated as a candidate implementation to test, not assumed to be a complete normative oracle.
- PREMIS 3.0 official XML schemas are available from the Library of Congress; XML output can be validated against those schemas.

## 3. Candidate toolchain

### BagIt
Candidate: Library of Congress bagit-python.
- Python library and CLI.
- Create and validate BagIt packages.
- Reports checksum mismatch, missing file, unexpected file and manifest errors.
- Use SHA-256 and SHA-512 manifests in the prototype.
- Pin a reviewed release and its transitive dependencies before use.

Official repository: https://github.com/LibraryOfCongress/bagit-python

### OCFL
Candidate: ocfl-py as a Python prototype/reference implementation.
- Supports OCFL object and storage-root operations and validation.
- Review its documented error/warning implementation status.
- Run official good/bad/warn fixture corpus and compare results with expected outcomes.
- Do not claim full OCFL conformance based solely on a successful local object creation.

Repository: https://github.com/zimeon/ocfl-py
Documentation: https://ocfl-py.readthedocs.io/en/latest/

Alternative: ocfl-java supports OCFL 1.0/1.1 and may be considered if the Python candidate fails the required conformance tests. Do not add both runtimes to the initial prototype.

Repository: https://github.com/OCFL/ocfl-java

### PREMIS
Use the official PREMIS 3.0 XSD from Library of Congress as the validation authority for XML serialization.
- Validate generated PREMIS XML against the official schema.
- Add semantic checks for required event/object/agent/rights relationships; XSD validation alone does not prove repository policy correctness.
- Do not invent a PREMIS application profile until the minimum metadata requirements are agreed.

Schema repository: https://github.com/LibraryOfCongress/premis-v3-0

## 4. Prototype architecture recommendation

For the first low-cost spike:
- Use a local filesystem sandbox with synthetic MIDI fixture files only.
- Run a small Python preservation worker/CLI separately from the existing web application.
- Keep the web application responsible for requesting ingest and displaying results; it must not write directly into the immutable object store.
- Do not provision cloud object storage, multi-region replication, or a production database schema during this spike.
- Keep source fixtures and test outputs in a disposable test directory, never the live collection.

The Python worker is a prototype boundary, not a commitment to make Python the production runtime. The existing application can later call a stable CLI/API boundary or replace the worker after toolchain evaluation.

## 5. Required spike tests

### BagIt tests
1. Build a bag from a synthetic MIDI fixture.
2. Validate the untouched bag.
3. Flip one payload byte and confirm checksum mismatch.
4. Remove a payload file and confirm missing-file detection.
5. Add an unmanifested payload file and confirm unexpected-file detection.
6. Corrupt a tag manifest and confirm tag validation failure.
7. Confirm source bytes outside the bag remain unchanged.

### OCFL tests
1. Create a v1.1 object using the selected tool.
2. Validate it with the candidate validator.
3. Validate official OCFL good/bad/warn fixtures and record all unsupported validation codes.
4. Create a second version containing metadata-only correction.
5. Verify version 1 content remains unchanged.
6. Corrupt a content file and verify the validator/fixity check detects it.
7. Test case-sensitive and case-collision filenames on the target filesystem.
8. Export/restore the object to a clean directory and verify content digests.

### PREMIS tests
1. Generate a minimal ingest event with object and agent links.
2. Generate fixity check event with digest algorithm, expected/actual values and outcome.
3. Generate validation failure event.
4. Generate rights record with unknown status.
5. Validate XML against official PREMIS 3.0 XSD.
6. Confirm semantic links and event chronology with independent application-level assertions.

## 6. Evidence artifacts

The spike must produce:
- fixture source SHA-256 and byte length;
- BagIt package and validation report;
- OCFL object inventory and validator report;
- PREMIS XML and XSD validation result;
- tamper-test results;
- version 1 vs version 2 comparison;
- restore/recovery report;
- tool versions, pinned dependencies, OS/filesystem details and command logs.

All reports must identify the exact source commit and fixture hashes. Do not report a test as passed unless its output is retained.

## 7. Exit criteria

- Candidate BagIt package validates and all deliberate tamper tests fail as expected.
- OCFL object passes the selected validator and the official fixture corpus coverage gaps are documented.
- Version 1 remains intact after metadata-only version 2 creation.
- PREMIS XML passes official XSD validation and application-level relationship checks.
- Restore reproduces exact source bytes and hashes.
- No production storage, real music ingest, or deployment occurs during the spike.

## 8. Risks and controls

- Validator incompleteness: document unsupported OCFL error/warning codes; supplement with official fixtures and independent validation.
- Filesystem case sensitivity: test the actual target filesystem; avoid case-colliding paths.
- Hash confusion: distinguish BagIt payload hashes, OCFL content-addressing digests and OCFL fixity digests; record algorithms and scopes separately.
- Overengineering: do not add a second production database or cloud service before the local spike passes.
- Rights risk: synthetic fixtures only until source rights and permissions are reviewed.

## Decision

Start with BagIt-Python + OCFL-PY + official PREMIS XSD in a local synthetic-fixture spike. Keep the Python worker isolated from the production web runtime. If OCFL-PY's documented validation gaps fail the acceptance tests, evaluate OCFL-Java as the single alternative. No production dependency or deployment is approved by this specification.


## Phase 02.80 — Toolchain Research Correction & Candidate Revalidation (2026-11-09)

This addendum supersedes any stale reading of the old `ocfl-py 1.1.1` PyPI page.

### Updated evidence

- Current PyPI project metadata lists `ocfl-py 2.1.0`, released 2026-06-26. Its current project description states that it implements OCFL v1.1 while retaining v1.0 support; it is a beta implementation and documents validator error/warning coverage. The old 1.1.1 page carries a historical v1.0 "work in progress" description and must not be used to characterize the current release.
  - https://pypi.org/project/ocfl-py/
  - https://github.com/zimeon/ocfl-py
- OCFL's official site confirms v1.1.1 is a patch clarification to v1.1; object and storage-root version declarations remain v1.1. The 1.1.1 changes clarify case-sensitive filesystem handling and distinguish content-addressing digests from fixity digests.
  - https://ocfl.io/news/
  - https://ocfl.io/1.1/spec/change-log.html
- OCFL publishes official validation codes and fixture objects; the selected implementation must be run against the official good/bad/warn corpus, not merely its own tests.
  - https://ocfl.io/1.1/spec/validation-codes.html
  - https://github.com/OCFL/fixtures
- The Library of Congress BagIt Python project supports package creation and validation, including checksum mismatch, missing payload file, and unexpected payload file detection. Its documented defaults include SHA-256 and SHA-512 manifests.
  - https://github.com/LibraryOfCongress/bagit-python
- PREMIS 3.0 official schema is available from the Library of Congress; XSD validation must be supplemented with semantic checks for object/event/agent/rights relationships.
  - https://www.loc.gov/standards/premis/schemas.html
  - https://github.com/LibraryOfCongress/premis-v3-0

### Updated decision

Keep `bagit-python` as the BagIt candidate. Keep `ocfl-py 2.1.0` as the first OCFL candidate, but treat it as a beta reference implementation until its reported validator coverage and official fixture results are recorded. Do not use the historical 1.1.1 package page as the current capability statement.

Before choosing a fallback, compare:
1. `ocfl-py 2.1.0` against official OCFL v1.1 good/bad/warn fixtures.
2. `ocfl-java` from the OCFL organization against the same fixture corpus.
3. A documented independent implementation only if its license, maintenance, and fixture results are inspectable.

No tool is yet approved for production. Pin exact versions and dependency hashes only after the prototype tests pass.
