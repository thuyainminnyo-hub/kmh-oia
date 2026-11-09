# Phase 02.73 — Expressive Pitch, Tuning Metadata & Myanmar Repertoire Profile Research

**Status:** Research and implementation proposal only. No parser or product code changed.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.72 browser/Python parser conformance research.

## Executive finding

The current Python and browser ingestion paths preserve note-on/note-off-derived note events, but they do not preserve the full performance expression needed to reason about pitch between equal-tempered note numbers. In the Python parser, non-note channel messages are read for byte structure and then discarded. The browser parser similarly only creates note events from commands 0x80 and 0x90. Consequently, pitch bend and tuning-related controller data are not available to downstream notation or analysis.

This is not a parser bug if the declared product scope is note-event extraction only. It is a capability boundary that must be explicit before claiming microtonal or expressive-pitch analysis.

## Evidence from external sources

1. **MIDI Association — MIDI 1.0 Detailed Specification.** The official MIDI 1.0 core specification covers channel voice messages and expression control. Use this as the normative reference for interpreting MIDI 1.0 messages.
   - https://midi.org/midi-1-0-detailed-specification
2. **MIDI Association — MIDI 1.0 Control Change Messages.** RPN 0,0 is Pitch Bend Sensitivity; RPN 0,1 is Channel Fine Tuning; RPN 0,2 is Channel Coarse Tuning. Data Entry MSB/LSB carry the configured parameter value.
   - https://midi.org/midi-1-0-control-change-messages
3. **MIDI Association — MIDI Polyphonic Expression (MPE).** MPE assigns notes to member channels so pitch bend and other expressive messages can be applied to individual notes rather than only to a shared channel.
   - https://midi.org/midi-polyphonic-expression-mpe
4. **W3C — Web MIDI API.** Web MIDI is for live MIDI device access, not direct Standard MIDI File parsing. It exposes low-level messages and does not interpret their musical meaning. It requires a secure context and permission; SysEx is a stronger permission and should not be requested unless needed.
   - https://www.w3.org/TR/webmidi/
5. **MDN — Web MIDI API.** Browser support is limited; Web MIDI requires a secure context and explicit user permission.
   - https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API
6. **Aung & Campbell (2023), “Learning Burmese (Saung Gauk) Music”.** The article describes Saung Gauk practice as using five primary pitches with two ornamental extras. This is specific to the repertoire/instrument discussed, not a universal rule for every Myanmar tradition.
   - https://journals.sagepub.com/doi/10.1177/27527646231185567
7. **Chiarofonte (2020), SOAS PhD thesis, “Powerful Sounds”.** The study describes Burmese nat hsaing modal categories as pentatonic selections from a heptatonic framework, with some tones falling between Western natural and flatted notes. It also discusses multiple possible renderings in Mahagita practice. These are repertoire- and context-specific ethnographic findings, not a single national tuning standard.
   - https://eprints.soas.ac.uk/37915/1/Chiarofonte_2020.pdf

## Technical implications

### 1. Pitch bend is not self-describing in cents

A MIDI 1.0 Pitch Bend message carries a 14-bit value (0–16383), with centre 8192. The pitch displacement in semitones/cents depends on the active Pitch Bend Sensitivity, configured through RPN 0,0 (CC 101/100 to select; CC 6/38 for Data Entry). Do not convert raw bend values to cents unless the applicable range is known and the event ordering/state has been reconstructed.

### 2. Channel scope matters

In ordinary MIDI 1.0, pitch bend is channel-scoped. If multiple notes sound on one channel, a bend may affect all of them. MPE uses member channels to support per-note expression. A data model that attaches every bend to one individual note without channel and time context would invent precision that the source does not contain.

### 3. Preserve facts before interpretation

Proposed raw event record fields:
- source file SHA-256 and parser version
- track index, MIDI channel, absolute tick, derived seconds
- event kind and original status/data bytes
- raw 14-bit pitch-bend value, where applicable
- controller number/value for relevant CC events
- current RPN selection and Data Entry state, where reconstructable
- explicit unknown, not-present, or not-reconstructable state rather than guessed values

Keep the note-event view as a derived projection. Do not overwrite the original raw event stream.

### 4. Separate the notation and tuning layers

Keep these distinct:
- MIDI note number (source fact)
- equal-tempered display spelling and octave convention
- Western key-relative degree analysis
- Sargam labels
- measured performance pitch and expressive bend
- named Myanmar repertoire/instrument tuning profile
- human-reviewed notation/transcription

A Myanmar profile should be versioned and scoped by named repertoire, instrument/ensemble, source recording or score, tuning reference, and reviewer. Competing versions must be retained where the evidence documents variation.

## Proposed implementation gates

### Gate A — Event preservation
- Extend both parsers to preserve pitch bend and relevant controller events without changing the existing note-event API.
- Keep absolute tick ordering, track/channel context, and original raw bytes.
- Test pitch-bend centre, minimum, maximum, and intermediate values.
- Test RPN 0,0 selection and Data Entry updates, including partial or missing configuration.
- Test channel isolation and simultaneous notes on one channel.
- Preserve unsupported messages as opaque events or explicitly document why they are omitted.

### Gate B — Time and state reconstruction
- Reconstruct per-channel controller/RPN state in event order.
- Do not assume a default pitch-bend range when the source does not establish it; mark the range as assumed only if a documented compatibility profile explicitly says so.
- Compare browser and Python event streams against the same fixture corpus.
- Keep raw events immutable; store derived pitch curves separately with algorithm/version metadata.

### Gate C — MPE and live input
- Treat MPE as a later optional capability, not a prerequisite for file-import parity.
- Treat Web MIDI live-device input as a separate adapter from SMF file parsing.
- Request ordinary MIDI access only after explicit user action; do not request SysEx permission for note/pitch analysis unless a reviewed requirement needs it.

### Gate D — Myanmar repertoire pilot
- Choose one named repertoire and instrument/ensemble with source materials and a qualified practitioner/researcher reviewer.
- Capture reference recordings, instrument/tuning context, transcription provenance, and reviewer decisions.
- Compare actual measured pitch distributions against equal-tempered MIDI note labels; do not force a twelve-tone mapping.
- Do not generalize findings from Saung Gauk to nat hsaing, Mahagita, zat pwe, or all Myanmar music.

## Acceptance criteria

- Existing note-event ingestion remains backward-compatible.
- Raw pitch-bend/controller events are preserved with source timing and channel context.
- No cents/semitone interpretation is emitted without known bend/tuning state.
- Browser/Python event-level parity passes on shared fixtures.
- Myanmar-specific output is marked experimental until reviewed against a named repertoire and evidence set.

## Non-claims

- No audio-to-MIDI transcription has been validated.
- No universal Myanmar tuning standard has been established by this research.
- No microtonal accuracy has been demonstrated by the current parser.
- No MPE or live Web MIDI implementation is complete.
- This document does not authorize merge or deployment.
