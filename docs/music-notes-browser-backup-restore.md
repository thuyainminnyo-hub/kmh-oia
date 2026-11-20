# VIS-DATA-001 — Music Notes browser backup and restore

## Scope and governance

Draft-PR-only development for a local JSON candidate-library restore feature in the existing Music Notes static page. No production release, website deployment, DNS/repository visibility changes, merge, or new repository is authorized. Production remains HOLD.

## Backup and restore procedure

1. **Before migration:** Open the old Music Notes website in the same browser profile where candidate records are saved. Click **Export JSON backup** and verify a complete download exists.
2. Keep the original MIDI files separately. JSON backups contain candidate metadata, note events and a recorded source digest, **not original MIDI bytes**.
3. Open a reviewed version of Music Notes with the **Restore Candidate Backup** control. Select the previously exported JSON file.
4. Confirm the reported candidate count before restoring. The backup is validated before database writes; no server upload is performed.
5. All candidates are added in **one IndexedDB transaction**. If any candidate ID conflicts with an existing record, the entire transaction aborts and prior records are left unchanged. No overwrite is permitted.
6. After a successful restore, refresh the library, export a new backup and compare the record count, IDs, and candidate fields to the original backup.
7. If duplicate IDs are reported, retain both original backups; resolve IDs in a reviewed backup copy only after checking provenance and record identity.

## Backup format

- Database: `kmh-music-intelligence`, version `1`; store: `candidates`; primary key: `song_id`.
- Backup schema: `schema_version: 1`, `library_type: kmh_music_intelligence_browser_candidates`, `songs: [...]`.
- Input limits: nonempty `.json` file up to 5 MiB, maximum 500 candidates, maximum 100,000 note events, plus nested-content limits.
- Unsupported schemas, malformed notes/timings, duplicate backup IDs, prototype-polluting object keys and invalid record structures are rejected before writes.
- Records remain marked `candidate`; the original MIDI `source_sha256` is historical metadata and cannot be independently validated without the MIDI file bytes.

## Required QA before publication

- Source JavaScript parses; validation tests actually execute (do not count skipped tests as a pass).
- Valid v1 export restores into a fresh browser profile and re-exported records compare equal.
- Malformed JSON, schema mismatch, unsafe keys, invalid notes, oversized input and existing-key collisions fail safely; existing data remains intact.
- Confirmation cancellation writes nothing.
- IndexedDB transaction completion is required before success is shown.
- Manual browser tests confirm MIDI import, preview, save, export, restore, browser restart and recovery.
- Independent review of cross-origin migration, customer instructions, IP exposure and any public deployment is required separately.

## Rollback

For a future separately authorized web release, restore the previous approved static HTML artifact only after verifying browser data is preserved. Do not clear IndexedDB automatically. Maintain an independently verified downloadable backup before any migration. A website rollback does not authorize reopening the proprietary KMH OIA core.

## Evidence

- Base branch: `main` at commit `132d6a09a6b91030835c07e5ff129eeeb79c4fba`.
- Development branch: `feat/vis-data-001-music-notes-json-restore`.
- This document specifies development and QA only, not production readiness or Owner deployment approval.
