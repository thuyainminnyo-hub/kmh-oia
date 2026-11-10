# Phase 02.79 — Preservation Package & Repository Architecture (PREMIS + BagIt + OCFL)

**Status:** Architecture decision and implementation plan; no storage runtime implementation.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phases 02.74–02.78.

## 1. Architecture decision

Use three complementary standards with clearly separated responsibilities:

- **BagIt 1.0 (RFC 8493):** ingest/transfer package and checksum manifests.
- **OCFL 1.1:** long-term repository object layout, immutable version history, inventory and fixity.
- **PREMIS 3.0:** preservation metadata describing objects, events, agents, and rights.

Do not make all three standards compete to be the source of truth for the same field. Define authoritative ownership and explicit mappings.

## 2. Standards evidence

### BagIt 1.0
RFC 8493 defines a hierarchical package containing tag files, payload files, and manifests. Payload is treated as opaque bytes; a bag is valid when complete and all manifest checksums verify. BagIt supports reliable storage and transfer but is not an Internet Standards Track RFC.
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://www.loc.gov/preservation/digital/

### OCFL 1.1
OCFL is an application-independent, human- and machine-parsable repository layout. It supports versioning, content inventories, digest sidecars, optional additional fixity digests, and logs. The specification is designed for diverse filesystem and object-storage environments.
- https://ocfl.io/1.1/spec/
- https://ocfl.io/latest/spec/

### PREMIS 3.0
PREMIS defines preservation metadata concepts for Objects, Events, Rights, and Agents. Fixity checks and preservation actions can be represented as events linked to the affected objects.
- https://www.loc.gov/standards/premis/v3/
- https://www.loc.gov/standards/premis/premis-3-0-final.pdf

### Australian archival practice
The National Archives of Australia describes bitstream preservation, original retention, fixity checks, audit trails, persistent object identifiers, redundant backups, and restore testing as elements of digital preservation.
- https://www.naa.gov.au/about-us/who-we-are/accountability-and-reporting/archival-policy-and-planning/digital-preservation-policy

## 3. Responsibility boundaries

| Concern | Authoritative mechanism | Notes |
|---|---|---|
| Ingest package completeness | BagIt validation | Validate tag files, payload inventory, and checksums |
| Exact original bytes | Immutable source object in OCFL | Never overwrite the original |
| Object version history | OCFL inventory/version directories | Every new state is a new version |
| File fixity in repository | OCFL inventory digest and optional fixity blocks | Verify stored content against recorded digest |
| Preservation action history | PREMIS events | Include actor/software, time, outcome, evidence |
| Rights and permissions | PREMIS Rights + linked evidence | Unknown is not permission |
| Parser output/transcription | Separate OCFL content object | Link to source and transformation event |
| Transfer receipt | BagIt package + ingest event | Keep package identity and validation report |

## 4. Proposed ingest workflow

1. Receive source file and depositor/context metadata.
2. Capture exact bytes in a quarantine/staging area; do not parse or normalize in place.
3. Calculate SHA-256 and byte length.
4. Build a BagIt package containing the original payload and metadata tags.
5. Validate BagIt manifests and completeness.
6. Identify file format and inspect for malware according to the repository security policy.
7. Assign a persistent object ID.
8. Create OCFL object version 1 containing the original file and required descriptive/technical metadata.
9. Generate PREMIS ingest, fixity, validation, and agent records.
10. Verify the OCFL inventory and re-read the stored original to recalculate its digest.
11. Replicate according to the approved storage policy and record replication/restore evidence.
12. Only after archival acceptance, submit a read-only reference to parsers for derived analysis.

A failed validation must not silently destroy the received bytes. Preserve the quarantine package and diagnostic record under a controlled retention policy, while preventing untrusted content from entering the trusted collection.

## 5. Proposed object structure (illustrative)

### BagIt transfer package

```text
bag/
  bagit.txt
  bag-info.txt
  manifest-sha256.txt
  tagmanifest-sha256.txt
  data/
    source/original.mid
    metadata/depositor.json
```

### OCFL repository object

```text
object-root/
  0=ocfl_object_1.1
  inventory.json
  inventory.json.sha512
  v1/
    inventory.json
    inventory.json.sha512
    content/
      source/original.mid
      metadata/object.json
      preservation/premis.xml
      evidence/ingest-report.json
```

This is a conceptual layout; final path names and PREMIS serialization must be validated against the selected OCFL and PREMIS schemas.

## 6. Hash policy

- SHA-256 is the initial ingest and transfer digest for the BagIt payload.
- OCFL uses its selected digest algorithm consistently for the object inventory and content manifest; select SHA-512 for the initial OCFL profile unless compatibility testing reveals a constraint.
- Preserve the original SHA-256 in descriptive/preservation metadata even if OCFL's primary digest is SHA-512.
- Do not compare unlike digest algorithms or imply they are interchangeable.
- Record each digest's algorithm, scope, value, calculation time, software/agent, and verification outcome.
- A matching digest demonstrates byte-level fixity relative to the recorded digest, not authenticity of authorship, musical correctness, rights clearance, or transcription accuracy.

## 7. Versioning and immutability policy

- Original source bytes are immutable.
- Corrected metadata creates a new OCFL version; record why and who approved it.
- Parser output, normalized MIDI, MusicXML, PDF notation, audio render, and human transcription are separate derived objects or versioned content with explicit source relationships.
- Never silently replace an earlier transcription. Supersede it with a new version and review event.
- Record migration/normalization tools, versions, parameters, outputs, and loss reports.
- Keep logs and PREMIS events append-only at the application level; repository versioning provides the underlying historical states.

## 8. Rights and access gates

- Rights status must be explicit: unknown, under_review, permission_granted, public_domain_verified, restricted, or denied.
- Record evidence, rights holder/claimant where known, scope, territory, term, attribution, and reviewer.
- Preservation copy permissions and public dissemination permissions may differ.
- Do not publish a file solely because it is technically accessible or already online.
- Quarantine and malware scanning are security controls, not rights determinations.

## 9. Implementation sequence

### Gate A — BagIt ingest prototype
- Build one deterministic BagIt package from a synthetic MIDI fixture.
- Validate the package with a standards-aware validator.
- Test tampered payload, missing manifest entry, extra payload file, and invalid tag manifest.
- Preserve original source bytes.

### Gate B — OCFL object prototype
- Create one OCFL 1.1 object from the validated package.
- Validate inventory and digest sidecar.
- Create version 2 for a metadata-only correction without changing the original source bitstream.
- Verify version 1 remains unchanged.

### Gate C — PREMIS event mapping
- Serialize ingest, fixity, validation, agent, and rights records.
- Validate XML against the official PREMIS 3.0 schema if XML is selected.
- Map each event to its OCFL object/version and supporting evidence.

### Gate D — Recovery and audit
- Copy object to an independent replica.
- Verify content and inventory fixity.
- Restore from replica into a clean location.
- Compare source digest and event history.
- Record every outcome.

### Gate E — Music parser integration
- Expose immutable source object references to parsers.
- Store parser output as separate derived objects.
- Link each output to source hash, parser version, schema version, and run event.
- Do not allow parser workers to mutate archival source content.

## 10. Acceptance criteria

- BagIt package passes independent validation.
- OCFL object passes a conformant validator.
- Original bytes remain identical through ingest and repository storage.
- New metadata/derived versions do not overwrite source bytes.
- PREMIS events link source, derived objects, agents, and outcomes.
- Rights are explicit and checked before access/distribution.
- Replica restore and fixity checks are demonstrated with evidence.
- No standards-conformance claim is made without validation by appropriate validators.

## 11. Non-claims

- No BagIt, OCFL, or PREMIS runtime is implemented by this document.
- No storage provider, replication topology, or retention period is selected.
- No real music source has been ingested or rights-cleared.
- No merge, release, or deployment is authorized.

## Decision

Prototype BagIt first for transfer validation, then OCFL for persistent object/version storage, then PREMIS event mapping. Keep this infrastructure independent of the MIDI parser so the same preservation layer can protect MIDI, audio, scores, images, and research documents.
