# Phase 02.78 — Preservation Provenance, Fixity & Rights Evidence

**Status:** Architecture specification; implementation not started.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phases 02.74–02.77.

## Objective

Extend the Verified Music Notes Library from byte-preserving ingestion into a preservation-aware evidence repository. Every source object must have verifiable fixity, documented preservation events, accountable agents, rights metadata, and traceable derived representations.

## Primary references

- Library of Congress, PREMIS Data Dictionary v3.0: https://www.loc.gov/standards/premis/v3/
- PREMIS Maintenance Activity and current standard status: https://www.loc.gov/standards/premis/
- PREMIS v3.0 fixity semantic unit: https://www.loc.gov/standards/premis/premis-3-0-final.pdf
- Library of Congress, digital score preservation practices: https://guides.loc.gov/music-notation-preferred-preservation-formats-for-digital-scores/digital-preservation-practices
- MIDI Association, Standard MIDI Files: https://midi.org/standard-midi-files
- MIDI Association, MIDI 2.0 Core Specifications: https://midi.org/midi-2-0-core-specification-collection

## Research conclusions

### 1. Fixity is a recurring event, not a one-time hash field

Record the digest algorithm, digest value, digest originator, timestamp, object identifier, software/agent, and outcome. A later fixity check compares the newly calculated digest with the previously recorded value and records the check as a preservation event.

SHA-256 should be the initial operational digest. Consider a second independent digest only where a documented preservation policy justifies it; do not add algorithms merely for appearance.

### 2. PREMIS provides a suitable conceptual model

Map the repository's own data model to PREMIS concepts:
- Object: original MIDI, score, audio recording, image, transcription, derived MIDI, fixture.
- Event: ingest, validation, fixity check, migration, normalization, transcription, review, rights update, export.
- Agent: person, organization, parser, software build, automated workflow.
- Rights: license, copyright status, permission, access restrictions, attribution requirements.

Do not claim PREMIS conformance merely because field names resemble PREMIS. Claim conformance only after validating the serialization and required semantic units against PREMIS 3.0.

### 3. Preservation and interpretation must remain separate

Original source bytes are immutable. A parser output, normalized MIDI, MusicXML score, notation image, or researcher transcription is a separate derived object with its own hash, software/version, event, and relationship to the source.

A fixity pass proves that bytes match a prior digest. It does not prove that the file is musically correct, authentic, rights-cleared, or accurately transcribed.

### 4. Rights evidence is a first-class requirement

Store rights status as explicit values such as unknown, under_review, permission_granted, public_domain_verified, restricted, or denied. Attach the evidence source, scope, territory, term, attribution, and reviewer. Do not infer public-domain status from age, online availability, or absence of a copyright notice.

## Proposed object and event model

### Object record
- object_id, object_type, format_identifier, protocol_version
- source_sha256, byte_length, media_type
- created_at, ingested_at, source_creator, depositor
- source_location/provenance reference
- rights_status and rights_record_id
- preservation_level, storage_replica references
- parser/schema versions where applicable

### Preservation event
- event_id, event_type, event_datetime
- outcome, outcome_detail, event_detail
- object_id and input/output object IDs
- responsible agent and software version
- algorithm/configuration version
- event evidence, logs, and signature/reference where available

### Relationship
- source object → parsed event representation
- source object → notation/transcription
- source object → normalized or converted file
- source object → derivative audio/image
- derivative → source parent, transformation event, and loss report

## Required implementation gates

### Gate A — Object identity and immutable source
- Store exact source bytes or immutable content-addressed reference.
- Verify SHA-256 immediately after ingest.
- Re-read and re-verify after storage write.
- Prevent derived transformations from overwriting the original.
- Record file format identification separately from filename extension.

### Gate B — Preservation event ledger
- Record ingest, hash calculation, validation, fixity check, and failed check as events.
- Capture event timestamp, agent, software version, outcome, and evidence.
- Make event history append-only; corrections are new events, not silent edits.

### Gate C — Rights and provenance
- Require rights status to be explicit before public distribution.
- Preserve provenance for donor/depositor, performer, recording, score, transcription, and researcher.
- Record access restrictions and attribution requirements.
- Unknown rights must not be treated as permission.

### Gate D — Replication and recovery
- Define at least three copies on two storage media types, with geographic separation where feasible, following Library of Congress guidance.
- Schedule fixity scans and record outcomes.
- Test restore/recovery from a replica.
- Document retention and media-refresh policy.

### Gate E — PREMIS mapping
- Map internal objects, events, agents, and rights to PREMIS 3.0.
- Validate generated PREMIS XML against the official schema if XML serialization is adopted.
- Record mapping/version and validation result.
- Do not claim PREMIS conformance before schema and semantic review.

## Acceptance criteria

- Every ingested object has immutable identity and verified initial digest.
- Every preservation action creates an auditable event.
- Every derivative links to its source and transformation event.
- Rights state and evidence are explicit; unknown is not permission.
- Periodic fixity checks and restore tests produce durable records.
- PREMIS mapping is documented and schema-validated before any conformance claim.
- No merge, release, or deployment is implied by this specification.

## Decision

Prioritize Gate A and Gate B after the canonical raw MIDI event contract is implemented. The repository must be able to prove what it received, whether those bytes changed, and what actions were performed before it claims that an interpretation is verified.
