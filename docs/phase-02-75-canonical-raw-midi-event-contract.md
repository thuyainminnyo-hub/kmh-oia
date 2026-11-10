# Phase 02.75 — Canonical Raw MIDI Event Contract & Evidence Model

**Status:** Design specification only; no runtime implementation.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.72 parser parity research; Phase 02.73 expressive-pitch research; Phase 02.74 tuning-aware architecture.

## 1. Objective

Define a lossless, versioned event contract shared by Python and browser parsers. Preserve source bytes and all recognized or opaque events before producing notes, tempo maps, tuning state, or notation.

The goal is not to make both parsers emit only the same note list. They must emit the same canonical source-event facts for the supported format subset, with explicit unsupported/malformed classifications.

## 2. Important standards constraints

- Standard MIDI Files are chunked, timestamped streams. The MIDI Association describes SMF as an interchange format for timestamped MIDI data, including tracks, sequences, tempo, and time-signature information: https://midi.org/standard-midi-files
- SMF track events use delta times; convert to absolute ticks without losing the original delta value or source order. The MIDI File Guide summarizes the chunk structure and the need to use chunk lengths when skipping unknown chunk types: https://midi.community/docs/smf/
- Running Status is a stateful compression mechanism. It must be decoded while retaining enough provenance to distinguish an explicit status byte from an omitted status byte. Real-time messages do not cancel running status in the MIDI byte-stream model, whereas System Common and System Exclusive do; SMF meta-event handling must follow the SMF specification rather than blindly reusing a live MIDI byte-stream parser. Reference: https://midimusic.github.io/tech/midispec.html
- Mido exposes per-track messages with delta ticks and playback iteration with seconds. It is useful as an independent implementation for supported cases, but it is not the byte-preservation authority: https://mido.github.io/mido/files/midi.html

## 3. Canonical data contract

### Source document
- `source_sha256`: SHA-256 of exact uploaded file bytes.
- `source_byte_length`.
- `container_format`: SMF.
- `smf_format`, `declared_track_count`, `division_raw`.
- `parser_name`, `parser_version`, `schema_version`.
- `imported_at` and provenance reference.

### Chunk record
- `chunk_index`, `chunk_type_raw`, `declared_length`.
- `source_byte_offset`, `payload_sha256`.
- `payload_reference` or exact raw payload bytes.
- `recognized`, `parse_status`, `warnings`.
- Preserve unknown chunk type, location, and payload; skipping for semantic parsing must not mean discarding from the archival layer.

### Event record
- `track_index`, `event_index_in_track`.
- `delta_ticks_raw`, `absolute_tick`.
- `event_class`: channel_voice, sysex, meta, system_common_escape, or opaque.
- `status_byte_raw` (nullable when supplied by running status).
- `running_status_source_event_index` (nullable).
- `data_bytes_raw` and `full_event_bytes_raw` (where available).
- `channel` (nullable), `message_kind`, `decoded_fields`.
- `source_byte_offset`, `parse_status`, `warnings`.

### Derived projections
- Notes, tempo map, meter map, program map, controller state, pitch curves, MTS tuning tables, and notation are derived views.
- Each derived view records source hash, parser/schema version, algorithm version, and interpretation assumptions.
- A derived projection must never mutate or replace the source bytes or raw event records.

## 4. Ordering rules

- Preserve event order within each track exactly as encoded.
- Absolute tick is calculated by cumulative delta ticks within that track.
- Do not invent a single total ordering between different tracks when events share the same absolute tick. If a consumer needs playback merge order, apply a named, versioned merge policy and retain original track/event indexes.
- Same-tick event order within one track is semantically meaningful for controller/RPN state reconstruction and must be preserved.
- Tempo map merging for Format 1 is a separate projection governed by the applicable SMF rules; do not let the general event sort silently determine it.

## 5. Hash and evidence model

Use at least three distinct integrity values:
1. Source file SHA-256 — exact original file bytes.
2. Chunk/payload SHA-256 — exact chunk payload bytes.
3. Canonical event JSON SHA-256 — deterministic serialization of decoded event records, including schema version.

Do not confuse these hashes. A canonical event hash proves deterministic interpretation under a schema; it does not prove byte-for-byte preservation. Retain source bytes or a content-addressed immutable object to prove source fidelity.

For fixtures:
- Generate exact raw bytes deterministically.
- Store each fixture ID, byte length, SHA-256, and generator version.
- Hash malformed fixtures too.
- Mido comparisons are read-only; do not save/re-serialize fixtures through Mido as a preservation test because libraries may normalize missing End-of-Track or other representational details.

## 6. Error and unsupported-data policy

Use explicit result states:
- `accepted`
- `accepted_with_warnings`
- `rejected`
- `unsupported_but_preserved`
- `truncated_preserved` (only if policy allows partial archival before rejection)

A parser may reject a file for semantic ingestion while the archival layer still preserves the exact original bytes and diagnostic metadata. Never imply that rejecting a malformed file means the evidence bytes were discarded.

Do not silently discard:
- unknown chunks;
- unknown meta events;
- supported-length but unimplemented channel messages;
- SysEx/MTS payloads;
- system escape payloads.

## 7. Cross-runtime conformance

Python and browser test suites must consume the exact same fixture bytes and compare:
- source hash and byte length;
- chunk indexes, offsets, types, and lengths;
- per-track event count and event order;
- delta and absolute ticks;
- explicit versus running status provenance;
- raw data bytes;
- decoded event classes and fields;
- parse status and warnings.

Use independent parsers as supplementary oracles only where their semantics are documented. The canonical source-byte and fixture hashes remain authoritative for byte integrity.

## 8. Implementation gates

### Gate A — Source and chunk archive
- Preserve uploaded source bytes and compute source hash.
- Preserve all chunk boundaries and unknown chunk payloads.
- Add byte-offset-aware malformed/truncation diagnostics.

### Gate B — Canonical event model
- Implement the versioned event record in Python.
- Keep the existing note API as a compatibility projection.
- Add deterministic fixtures for every supported event family and opaque fallback.

### Gate C — Browser parity
- Extract browser parser into a module.
- Consume shared raw fixtures.
- Match Python event records and diagnostics exactly for supported cases.

### Gate D — Derived state
- Reconstruct RPN, pitch bend, MTS, and MPE state only after raw event parity is established.
- Version every derived interpretation.

## 9. Acceptance criteria

- Exact source bytes are retained and source SHA-256 re-verifies.
- Unknown chunks and unsupported event payloads remain recoverable.
- Per-track event order and source offsets are stable across runtimes.
- Canonical event schema is versioned and deterministic.
- Existing note-only API remains backward-compatible.
- No tuning or notation claim is made from incomplete or inferred source state.

## 10. Non-claims

- This design does not establish full MIDI 1.0 or SMF conformance.
- It does not establish MTS, MPE, MIDI 2.0, or Myanmar notation implementation.
- It does not authorize a merge, release, or deployment.

## Decision

Implement Phase 02.74 Gate A using this contract as the design baseline. Preserve bytes and provenance first; decode and interpret second.
