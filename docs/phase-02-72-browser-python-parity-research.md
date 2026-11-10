# Phase 02.72 — Browser ↔ Python MIDI & Notation Parity Research

**Status:** Research and implementation plan; no browser parser code changed by this document.
**Date:** 2026-11-09
**Branch:** `phase-02-71/midi-golden-fixtures`
**Scope:** Existing browser MIDI parser and Python parser parity, followed by notation-layer separation.

## Executive finding

The browser parser in `apps/music-notes/index.html` is not yet behaviorally equivalent to `src/music_intelligence/midi_parser.py`. Both parse common format 0/1 PPQN note events, but code inspection identifies concrete divergence points. Phase 02.72 should begin with a shared conformance contract and adversarial fixtures, not with UI polish.

## Direct code-inspection findings

| Area | Python parser | Browser parser | Required decision |
|---|---|---|---|
| Meta event cancels running status | Clears running status | Does not clear running status in the Meta branch | Align to SMF rules; add a negative fixture |
| End-of-Track | Requires zero-length EOT and requires it to be the final event | Breaks on EOT without validating zero length or trailing bytes | Enforce identical strict EOT behavior |
| Unknown chunks | Skips unknown chunk types using declared length | Requires every post-header chunk to be MTrk | Decide forward-compatible unknown-chunk policy; align both |
| Format 1 tempo placement | Requires tempo events in first track only | Collects tempo events from every track | Align to selected Format 1 policy and test |
| Note ordering | Sorts by tick, track, channel, pitch | Sorts by tick, track only | Define canonical total ordering |
| Sysex running status | Clears running status | Clears running status | Existing alignment; preserve tests |
| VLQ | At most four bytes | At most four bytes | Existing alignment; preserve boundary tests |
| Unmatched Note Off | Strictly rejected | Silently ignored | Align strictness; add fixture |
| Partial ingestion | Python import validates before writing | Browser parser builds in-memory candidate before IndexedDB write | Keep all-or-nothing behavior and test transaction failure |
| Tempo conversion | PPQN + tempo map, default 500000 μs/quarter | Same general formula | Compare every note start/end time within fixed tolerance |

These findings come from the current branch's browser parser and Python parser source. They are implementation observations, not claims that every divergence is necessarily a standards violation; the Owner must approve the project's strictness/compatibility profile.

## Standards and external reference evidence

1. **MIDI 1.0 Detailed Specification — MIDI Association.** Primary normative reference for SMF and MIDI 1.0 message behavior. Use it to settle running-status, meta-event, track-chunk, and timing rules.
   - https://midi.org/midi-1-0-detailed-specification
2. **MIDI 1.0 message summary — MIDI Association.** Note number is 0–127; Note On/Off and pitch-bend messages are separate message types. This reinforces that a MIDI note number is not itself a complete acoustic pitch/tuning model.
   - https://midi.org/summary-of-midi-1-0-messages
3. **Mido Standard MIDI Files documentation.** Track message `time` values are delta ticks; PPQN and tempo metadata are both required to derive seconds; default tempo is 500000 microseconds per quarter note.
   - https://mido.github.io/mido/files/midi.html
4. **Tone.js MIDI.** A practical JavaScript MIDI parser can expose ticks, seconds, notes, tempos and tracks, making it a useful non-normative cross-check candidate. It should not silently replace KMH's parser or become a production dependency without review.
   - https://github.com/Tonejs/Midi
5. **Web MIDI API / MDN.** Live MIDI-device access is distinct from parsing a user-selected .mid file. Web MIDI is secure-context-only, permission-gated and has limited browser availability. The app should retain ordinary file-input parsing as the reliable baseline and treat device input as an optional capability.
   - https://www.w3.org/TR/webmidi/
   - https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API
6. **Aung & Campbell, “Learning Burmese (Saung Gauk) Music: Pathway Through World Music Pedagogy” (2023).** The abstract describes five primary pitches and two ornamental extras in Saung Gauk music. This is evidence against treating all Burmese musical practice as a simple twelve-semitone Western major scale.
   - https://journals.sagepub.com/doi/10.1177/27527646231185567
7. **Lorenzo Chiarofonte, “Powerful Sounds: Music and Meaning in Burmese Spirit Mediumship” (SOAS thesis, 2020).** Discusses athan/modal categories, pentatonic selection from a heptatonic framework, pitch inflections between Western semitones, and lack of a single standardised rendering in Mahagita practice. Treat as scholarly context, not a universal tuning specification.
   - https://eprints.soas.ac.uk/37915/1/Chiarofonte_2020.pdf

## Crucial notation architecture decision

Keep these layers separate:

1. **Source MIDI facts:** raw MIDI note number (0–127), velocity, track/channel, ticks, tempo map, source SHA-256.
2. **Equal-tempered display layer:** pitch-class spelling and octave convention (the project currently documents MIDI 60 as C4). This is a display convention, not a tuning measurement.
3. **Western key-relative analysis:** current major-key degree engine.
4. **Sargam label layer:** current Sa/Re/Ga/... labels are a Hindustani-style solfege mapping relative to a chosen tonic, not a validated Myanmar traditional notation system.
5. **Myanmar tradition-specific interpretation:** must be a separately researched, versioned profile with named repertoire/instrument context, tuning reference, evidence provenance, and expert-reviewed mappings. Do not silently label a generic Sargam output as Myanmar notation.
6. **Measured/expressive pitch layer:** MIDI pitch-bend, tuning, and performance inflection require separate event capture and a calibration/reference model. A note number alone cannot recover microtonal intonation.

The current `number_notes.py` explicitly says it does not claim to encode Myanmar traditional notation. Preserve that boundary.

## Proposed Phase 02.72 acceptance gates

### Gate A — Parser conformance
- Extract browser parser from inline HTML into a testable module without changing behavior first.
- Use the same canonical synthetic MIDI fixture IDs and bytes as the Python suite.
- Run the exact bytes through both parsers in Node/browser test harness.
- Compare format, PPQN, track count, tempo events, note tuples, and note ordering.
- Compare `start_seconds` and `end_seconds` with a documented tolerance (proposed 1e-9 for deterministic arithmetic; confirm after test).
- Add fixtures for: Meta clears running status; EOT nonzero length; bytes after EOT; unknown chunk; tempo meta in a non-first Format 1 track; orphan Note Off; channel/track tie ordering; malformed chunk boundaries.
- No invalid input may produce a savable partial candidate.

### Gate B — Notation parity
- Move browser `pitchLabel` into a separately testable pure function.
- Generate all 128 MIDI note labels for every supported tonic.
- Compare exact output fields with Python `DualNumberNotesEngine`: pitch name, octave, semitone distance, Western degree, Sargam label, key.
- Test all chromatic classes and octave boundaries, including MIDI 0 and 127.
- Define canonical JSON serialization for comparison.

### Gate C — Product boundary
- Preserve user-selected local file import as baseline.
- Keep Web MIDI device input optional, behind HTTPS and explicit permission.
- Do not request SysEx permission unless a reviewed feature requires it.
- Keep imported records as candidates; no automatic verification or promotion.
- No upload, external service, or paid dependency is introduced by parity testing.

### Gate D — Myanmar notation research
- Do not equate Sargam with Burmese traditional notation.
- Select a narrow, named repertoire/instrument pilot only after identifying source materials and a qualified reviewer.
- Record competing variants rather than forcing a single “correct” pitch mapping where sources document variation.
- Preserve original notation/audio/transcription provenance and reviewer decisions.

## Recommended immediate implementation order

1. Create a pure browser parser module and test harness.
2. Add cross-runtime differential tests against the canonical golden corpus.
3. Fix each confirmed divergence with one regression fixture per behavior.
4. Add 128-note notation parity tests.
5. Only then design a Myanmar-specific notation profile from repertoire-specific evidence.

## Non-claims

- No audio-to-MIDI transcription has been validated.
- No Myanmar traditional notation model has been validated.
- No browser/Python parity pass has been achieved yet.
- This research document does not authorize merge or deployment.
