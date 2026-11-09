# Phase 02.76 — SMF Conformance Test Matrix & Parser Boundary Rules

**Status:** Research-backed test specification; no parser implementation changed.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.72 browser/Python parity; Phase 02.74 raw event preservation; Phase 02.75 canonical event contract.

## 1. Why this phase exists

The MIDI live byte-stream protocol and Standard MIDI File (SMF) event encoding are related but not interchangeable. Reusing a live MIDI byte-stream state machine for SMF without accounting for SMF's event grammar can create false parser behavior. The conformance suite must explicitly distinguish:
- live MIDI transport messages;
- channel messages stored in an SMF track;
- SMF SysEx events (F0/F7 forms);
- SMF Meta Events (FF type length payload);
- opaque chunks and unknown Meta Event types.

The MIDI Association's MIDI 1.0 Detailed Specification is the normative source for MIDI messages; the MIDI Association's Standard MIDI Files page is the normative source for the file format. The MIDI Field Guide and Mido documentation are secondary implementation references, not substitutes for the specification.

## 2. Confirmed SMF rules to encode as tests

1. **Chunk framing:** Each chunk has a four-byte type and four-byte big-endian length. Parsing must remain within the declared chunk boundary.
2. **Header length:** Read the required header fields and honor a header length greater than six bytes by skipping/preserving extension bytes; do not assume the header payload is exactly six bytes.
3. **Track delta times:** Every track event begins with a delta-time VLQ. Preserve raw delta and calculate absolute tick per track.
4. **Running status:** Running status is supported for channel messages within an MTrk track and spans delta-time values. The first channel event requiring status must provide it.
5. **Cancellation in SMF:** SMF Meta Events and SMF SysEx events cancel running status. Do not confuse this with live MIDI real-time-byte handling.
6. **Unknown Meta Events:** Read their VLQ length and skip/retain exactly that payload; never guess a length or parse payload bytes as a new event.
7. **SysEx packet forms:** F0 and F7 events have length-prefixed payloads. F7 may represent an escape event, not necessarily the continuation/terminator of a preceding F0 message. Preserve exact bytes and avoid merging packets unless a separate, tested assembly layer is specified.
8. **End of Track:** Every MTrk track is expected to end with FF 2F 00. It is a track event, not merely a file terminator. Reject or explicitly classify missing/malformed EOT according to the strict-ingestion policy.
9. **Chunk extension handling:** Unknown chunks must be handled using their declared length when the chosen SMF compatibility policy allows them. Preserve unknown chunk bytes even if the semantic parser skips them.
10. **Format-specific semantics:** Format 0 has one track; Format 1 stores simultaneous tracks and conventionally places tempo/time-signature map in the first track; Format 2 represents independent patterns and must not be silently interpreted as Format 1.
11. **VLQ bounds:** Delta-time VLQs are limited to four bytes in SMF. Test 0, 127, 128, 16383, 16384, and 0x0FFFFFFF plus malformed/truncated sequences.
12. **Tempo conversion:** Tempo is microseconds per quarter note. Tick-to-time conversion must use the applicable tempo map and PPQN division; SMPTE division is a separate timing mode and must not be treated as PPQN.

## 3. Critical correction: live MIDI versus SMF

Some MIDI live-stream rules discuss System Real-Time bytes interleaved with other messages and their effect on running status. SMF's track-event grammar does not store ordinary live System Real-Time bytes as normal track events; SMF has its own F0/F7 SysEx event representation and FF Meta Event representation. Therefore:
- Do not add a generic “real-time byte does not cancel running status” test to an SMF track parser unless the byte is inside a defined SMF escape payload.
- Do add separate live-stream parser tests if/when KMH implements a Web MIDI transport adapter.
- Keep SMF and live-stream parser conformance suites separate.

## 4. Required test matrix

### Chunk and header
- MThd length 6, greater than 6, less than 6.
- Declared chunk length exactly fits, exceeds file, or overlaps following chunk.
- Unknown chunk between header and track, and between tracks, with byte-preservation check.
- Wrong chunk order and duplicate/missing MThd classifications.

### Track grammar
- Multiple MTrk chunks; declared track count matches and mismatches.
- Empty/short track payload.
- EOT at final event; missing EOT; malformed EOT length; data after EOT.
- Truncated delta VLQ; five-byte VLQ; max legal four-byte VLQ.

### Channel event decoding
- All channel voice status families: Note Off, Note On, Polyphonic Key Pressure, Control Change, Program Change, Channel Pressure, Pitch Bend.
- One-data-byte and two-data-byte message lengths.
- Running status across nonzero delta times.
- Running status cancellation after Meta and F0/F7 SysEx.
- Channel change and status change.
- Note On velocity zero normalized as note-off in the note projection while preserving raw status/data.

### Meta and SysEx
- Known Meta types with correct and incorrect lengths.
- Unknown Meta type with 0, 1, multi-byte VLQ and long payload lengths.
- F0 complete SysEx, F7 escape, F7 continuation packet, empty payload, truncated payload.
- Preserve unknown manufacturer-specific SysEx without interpreting it as MTS.
- MTS Universal SysEx messages get a separate decoder and fixtures only after raw preservation passes.

### Timing and ordering
- Tempo changes at tick zero and mid-track.
- Simultaneous events in one track preserve encoded order.
- Same-tick events across tracks retain track-local order and do not invent an undocumented global ordering.
- Format 1 tempo map in track 0; nonconforming placement classified explicitly.
- PPQN and SMPTE division use separate conversion paths.

## 5. Differential test policy

- Python and browser implementations consume identical fixture bytes from one shared fixture corpus.
- Compare source hash, chunk boundaries, event indexes, delta ticks, absolute ticks, raw bytes, running-status provenance, decoded event class, and parse diagnostics.
- Use Mido as a secondary oracle for common valid channel/note/timing cases only.
- Do not use Mido reserialization as proof of byte-preservation.
- For cases where libraries differ in malformed-file recovery, KMH's explicit policy plus source-byte preservation is authoritative; document divergence rather than hiding it.

## 6. Implementation order

1. Complete Phase 02.74 Gate A: exact source-byte and chunk preservation.
2. Implement canonical raw event records from Phase 02.75.
3. Add the missing channel voice event families and raw Meta/SysEx preservation.
4. Extract browser parser and run exact shared fixtures.
5. Only then implement RPN/pitch bend state reconstruction and MTS decoding.

## 7. Acceptance criteria

- Each normative rule above has at least one positive and/or negative fixture.
- Test names identify whether the input is SMF or live MIDI transport.
- Python/browser outputs match for supported SMF cases.
- Unknown data remains byte-recoverable.
- Malformed files have deterministic rejection codes and byte offsets.
- Note-only API compatibility is retained.
- No claim of full SMF conformance until the complete supported-scope matrix passes.

## 8. References

- MIDI Association, MIDI 1.0 Detailed Specification: https://midi.org/midi-1-0-detailed-specification
- MIDI Association, Standard MIDI Files: https://midi.org/standard-midi-files
- MIDI Field Guide, Standard MIDI Files (secondary guide): https://midi.community/docs/smf/
- Mido, MIDI files and timing: https://mido.github.io/mido/files/midi.html
- Microsoft Learn, MIDI file creation overview: https://learn.microsoft.com/en-us/windows/win32/multimedia/creating-midi-files

## Decision

Phase 02.76 is a conformance-test specification, not an implementation claim. Start execution with the chunk/source-byte archive and raw event preservation. Keep live MIDI parsing out of the SMF parser scope.
