# Phase 03.02 — Approval-bound Recovery Contract & Preservation Standards Mapping

**Status:** Architecture and safety contract documented; no recovery mutation engine enabled.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## 1. Latest verified baseline

Documentation commit `6b6fab97444402a150c2462a954210a63ef1bc8b` completed all observed workflows successfully: OIA Tests, Preservation Gate A, OIA Validation, and MIDI Fixture Integrity.

Code commit `9090dd2e7305231edfc5ed946abc271acc9cf029` completed full OIA tests (644 passed), Linux and Windows Preservation Gate A, 31 targeted tests per platform, and 5/5 pinned LOC fixtures per platform. The planner's accepted-only and staging-only states, tamper detection, traversal rejection, read-only behavior, and eight process-kill checkpoints passed.

PR #217 remains OPEN / DRAFT. These results do not prove power-loss or device-level crash consistency.

## 2. Research and standards findings

### Crash consistency
- MC³ (2026 COMPSAC) proposes model checking for full-stack filesystem crash consistency, including directory management and garbage collection. It motivates a later filesystem/VM-level test layer beyond application process-kill tests.
- 2026 ISP RAS differential fuzzing compares explicitly persisted files during normal execution with the same filesystem state after simulated crashes; the paper reports finding crash-consistency bugs in popular Linux filesystems.
- PoWER (OSDI 2025) formalizes recoverability preconditions on writes and models media corruption detection. It supports making write ordering and recovery preconditions explicit.
- Fawkes (SOSP 2025) uses context-aware fault injection and recovered-state verification to expose DBMS durability bugs; its lesson is to verify post-recovery data relationships, not merely that a process restarts.

### Preservation standards
- BagIt / RFC 8493 is the packaging and transfer layer: payload plus checksum manifests and tag files.
- OCFL 1.1 is a separate storage-layout/versioning layer. It emphasizes rebuildability, parsability, immutable version directories, inventory digests, and storage diversity. Do not conflate BagIt conformance with OCFL conformance.
- PREMIS 3.0 defines four entities: Objects, Events, Rights, and Agents. Intellectual Entities were part of PREMIS 2.2, not the PREMIS 3.0 data model. Recovery, validation, fixity check, migration, and restore should eventually be mapped to PREMIS Events with outcomes and responsible Agents.
- The 2025 NDSA Fixity Survey Report, published 30 April 2026, summarizes 89 responses; 94% reported using fixity information, while capture/verification frequency, recording locations, and algorithms varied. This supports an explicit KMH fixity policy rather than assuming one universal cadence.

References:
- MC³: https://ieeexplore.ieee.org/abstract/document/11645445/
- Differential crash-consistency fuzzing: https://www.mathnet.ru/eng/tisp1121
- PoWER: https://www.microsoft.com/en-us/research/publication/power-never-corrupts-tool-agnostic-verification-of-crash-consistency-and-corruption-detection/
- Fawkes: https://doi.org/10.1145/3731569.3764841
- BagIt overview / RFC 8493 context: https://msi.dublincore.org/standards/bagit/
- OCFL 1.1: https://ocfl.io/1.1/spec/
- PREMIS 3.0: https://www.loc.gov/standards/premis/v3/
- 2025 NDSA Fixity Survey announcement: https://www.ndsa.org/2026/04/30/2025-ndsa-fixity-survey-report-published.html

## 3. Architecture decision

Keep the preservation layers separate:

1. **BagIt intake package** — preserve the original opaque bytes and verify package manifests.
2. **Recovery journal and receipt** — record transaction intent and observed execution outcomes.
3. **OCFL storage object (later, optional adoption)** — provide versioned, rebuildable long-term storage layout after a separate design and conformance decision.
4. **PREMIS preservation events** — record ingest, fixity check, crash detection, recovery approval, recovery execution, validation, and restore as preservation events.
5. **Fixity policy** — define initial capture, post-transfer verification, scheduled verification, restore verification, algorithm policy, and escalation thresholds.

## 4. Operator-approved recovery contract

Recovery execution MUST remain disabled until all of the following are designed and tested:

- A recovery proposal is canonicalized and assigned a SHA-256 plan digest.
- The proposal binds to the exact journal bytes/digest, object ID, source digest and length, candidate path, candidate content digest, and observed filesystem identity metadata.
- Operator approval explicitly references the exact plan digest and a named action; approval of one plan cannot authorize a later changed plan.
- Before mutation, the executor re-runs the planner and rejects stale approvals if any journal, candidate, path, digest, or state has changed.
- Only allowlisted actions are executable: `finalize_receipt_for_verified_accepted_bag` or `promote_verified_staging_bag`.
- Never overwrite an existing accepted object, delete a source, or infer that a reservation is stale from age alone.
- Use an idempotency key derived from object ID + journal digest + action + plan digest; repeated execution must return the prior result or a safe no-op.
- Record an append-only approval and execution audit event with actor, timestamp, plan digest, action, preconditions, outcome, post-action BagIt validation, and post-action fixity.
- If any precondition is ambiguous, fail closed to manual investigation.

An approval file or CLI flag alone is not an authentication system. Actor identity and authorization must be supplied by a trusted operating environment before claiming authenticated approval.

## 5. Phase 03.02 implementation sequence

1. Harden planner input handling: reject symlinked report directories and journal files; read journal bytes once; bind journal digest into the plan.
2. Produce deterministic canonical plan output and `plan_sha256` with stable field ordering and no volatile timestamps in the digest input.
3. Capture candidate identity and content evidence; explicitly handle duplicate journals for one object and conflicting accepted/staging candidates.
4. Add approval record schema bound to `plan_sha256`, action, actor, and approval time; validate authorization policy separately.
5. Add stale-plan rejection by recomputing the plan immediately before any mutation.
6. Implement one allowlisted action at a time, with idempotency and atomic receipt/audit handling.
7. Add crash injection around every recovery mutation and verify post-recovery data state.
8. Only then map outcomes to PREMIS 3.0 Events and assess whether OCFL 1.1 storage adoption is justified.

## 6. Acceptance criteria

- No mutation without explicit approval bound to an unchanged plan digest.
- No stale approval can execute after candidate/journal changes.
- Duplicate execution is idempotent.
- Every successful recovery has verified BagIt manifests, source SHA-256 and byte length, receipt, and audit event.
- Failed or ambiguous recovery leaves source evidence and journals intact.
- Linux and Windows CI pass for supported application-level semantics; platform-specific durability claims remain separate.
- Filesystem/VM power-loss tests are required before making power-loss durability claims.

## 7. Scope boundaries

No recovery mutation engine is implemented by this phase document. No authenticated operator identity, complete PREMIS/OCFL conformance, independent replica recovery, rights clearance, physical power-loss testing, or production readiness is claimed. Gate A remains open pending broader preservation acceptance criteria; PR #217 remains OPEN / DRAFT.

## Standards correction and additional research (2026-11-10)

PREMIS 3.0 official Library of Congress page confirms four data-model entities: Objects, Events, Rights, Agents. Intellectual Entities appear in the PREMIS 2.2 model, not PREMIS 3.0. The corrected wording above is authoritative for this project.

The PREMIS Event record is useful for KMH because it supports event identifier/type/date, optional detail, outcome and outcome detail, links to Agents and links to Objects. This can represent preservation intake, fixity validation, crash detection, approval, recovery execution, and post-recovery verification.

RFC 8493 specifies BagIt tools MUST support SHA-256 and SHA-512; it SHOULD enable SHA-512 by default for new bags. Existing KMH SHA-256 use is valid, but the roadmap should add SHA-512 manifest support/verification and define migration/dual-manifest policy rather than silently changing algorithms.

NDSA Levels of Digital Preservation v2.1 (March 2026) adds environmental sustainability decision guidance. Use it as an organizational assessment framework, not a software conformance certificate. Its guidance explicitly notes Level 4 need not be the goal for every functional area.

FADGI TCR4CAP v0.2 (published 2026-09-08; public-comment period ended 2026-10-15) is a tiered framework for content authenticity and provenance in library, archives and museum collections, with particular relevance to AI-impacted audiovisual content. Treat it as an emerging guidance framework, not a finalized standard. For historic music recordings and associated provenance, it may inform collection-level authenticity review, but does not replace fixity or preservation metadata.

Research references:
- PREMIS 3.0: https://www.loc.gov/standards/premis/v3/
- PREMIS 3.0 Event semantic units: https://www.loc.gov/standards/premis/v3/premis-hierarchical-3-0.html
- PREMIS 2.2 entity model: https://www.loc.gov/standards/premis/v2/
- RFC 8493: https://www.rfc-editor.org/rfc/rfc8493.html
- NDSA Levels v2.1: https://www.ndsa.org/activities/levels-of-digital-preservation/
- NDSA v2.1 announcement: https://www.ndsa.org/2026/03/23/announcing-version-2_1-of-the-ndsa-levels-of-digital-preservation.html
- 2025 Fixity Survey: https://zenodo.org/records/22099730
- FADGI TCR4CAP: https://www.digitizationguidelines.gov/guidelines/tcr-cap.html

Implementation implications:
1. Add BagIt SHA-512 manifest support and validate both SHA-256 and SHA-512 manifests where dual manifests are present.
2. Add a KMH Fixity Policy: ingest verification, post-transfer verification, periodic scheduled verification, pre/post-recovery verification, algorithm transition, alert severity and audit retention.
3. Map PREMIS Events to stable event types and capture eventOutcome/eventOutcomeDetail, eventDetail, linkingObjectIdentifier and linkingAgentIdentifier.
4. Use NDSA Levels v2.1 for a gap assessment across Storage, Integrity, Control, Metadata and Content, including environmental sustainability considerations.
5. Keep TCR4CAP as a provenance/authenticity guidance input for audiovisual historical sources; do not represent it as formal compliance.
