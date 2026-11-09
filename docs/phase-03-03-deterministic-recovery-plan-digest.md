# Phase 03.03 — Deterministic Recovery Plan Digest

**Status:** Plan-digest implementation and regression test committed; exact-commit CI pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Verified preservation standards

- PREMIS 3.0's official Data Dictionary landing page and PREMIS 3 OWL page describe four entities: Objects, Events, Rights, Agents. The Library of Congress hierarchical semantic-unit page currently displays a five-entity description including Intellectual Entities; this is inconsistent with the main PREMIS 3.0 Data Dictionary landing page and PREMIS 3 OWL page. For KMH's entity-count statement, follow the Data Dictionary and 3.0 ontology (four entities) and record this documentation inconsistency rather than silently mixing PREMIS 2.2 and 3.0 descriptions.
- RFC 8493 requires BagIt creation/validation tools to support SHA-256 and SHA-512 and recommends SHA-512 by default for newly created bags.
- Current KMH intake already creates both `manifest-sha256.txt` and `manifest-sha512.txt`, plus corresponding tag manifests; tests assert both files and `manifest_algorithms == ['sha256', 'sha512']`. This is implemented, not a future task.
- OCFL 1.1.1 is the current patch clarification for OCFL 1.1; the storage declaration remains `ocfl_1.1`. OCFL is a storage layout/versioning specification, not a replacement for BagIt packaging or PREMIS event metadata.
- TCR4CAP v0.2 was published 2026-09-08 for public comment, with comment period ending 2026-10-15. Treat as community guidance for content authenticity/provenance in LAM collections, not as a finalized conformance standard.

## Phase 03.03 implementation

Added to `plan_ingest_recovery()`:
- Read pending journal bytes once and calculate `journal_sha256` over the exact raw bytes.
- Add candidate directory identity evidence (device, inode, mode, mtime_ns) for verified candidate Bags.
- Serialize plan data deterministically with UTF-8, sorted keys, compact separators, and SHA-256 to produce `plan_sha256`.
- Include journal digest, candidate identity, BagIt result, payload SHA-256/length, and proposed action in the digest-bound plan.

Added regression test `test_recovery_plan_digest_is_deterministic_and_binds_journal_bytes`: repeated reads produce the same digest; changing raw journal bytes changes journal and plan digests; subsequent repeated reads remain deterministic.

Commits:
- Plan digest implementation: `d354bebf84e38bb54425999e2d1ca27cccecc2b8`
- Plan digest regression test: `733c7ac7ea814ecf73ed1aa8157456c7ebebb05b`

## Safety limitations

- This adds plan identity, not operator authentication or authorization.
- It does not execute recovery or mutate preservation objects.
- Directory identity metadata is platform-specific and can be reused; it is supplementary evidence, not a cryptographic identity guarantee.
- Approval must bind to the exact `plan_sha256` and the executor must recompute/revalidate immediately before any future mutation.
- If plan output includes diagnostics from platform-specific OS errors, canonical digest reproducibility is guaranteed only for unchanged observed state on the same implementation/platform; cross-platform identical digests are not promised.
- Exact-commit CI is pending. No PASS is claimed for these new commits yet.

## References

- PREMIS 3.0 Data Dictionary: https://www.loc.gov/standards/premis/v3/
- PREMIS 3.0 ontology: https://www.loc.gov/standards/premis/ontology/owl-version3.html
- PREMIS hierarchical listing (contains conflicting five-entity wording): https://www.loc.gov/standards/premis/v3/premis-hierarchical-3-0.html
- RFC 8493: https://www.rfc-editor.org/rfc/rfc8493.html
- OCFL 1.1 specification: https://ocfl.io/1.1/spec/
- OCFL release notes: https://ocfl.io/news/
- TCR4CAP: https://www.digitizationguidelines.gov/guidelines/tcr-cap.html

## Next steps

1. Verify exact-commit CI and inspect Linux/Windows test logs.
2. Add approval record schema bound to plan digest and an explicit allowlisted action.
3. Add stale-plan rejection by recomputing plan before execution.
4. Implement idempotency and append-only audit receipts before enabling any mutation.
5. Continue filesystem/VM crash tests and independent replica restore before any power-loss or production claims.

PR #217 remains OPEN / DRAFT. Gate A remains open pending broader acceptance criteria.