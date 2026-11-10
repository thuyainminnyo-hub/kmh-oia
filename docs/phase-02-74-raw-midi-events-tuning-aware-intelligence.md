# Phase 02.74 — Raw MIDI Event Preservation & Tuning-Aware Intelligence

**Status:** Research-backed implementation specification; implementation not started.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.72 browser/Python conformance research; Phase 02.73 expressive-pitch research.

## Executive decision

Build a lossless raw MIDI event layer before adding expressive-pitch interpretation or Myanmar repertoire notation. Keep the current note-event API as a backward-compatible derived projection.

Do not collapse pitch bend, RPN/NRPN, MIDI Tuning Standard (MTS), MPE, or repertoire-specific tuning into a single cents value. Preserve source facts, event order, channel/track scope, and interpretation provenance.

## Research findings

### MIDI 1.0 Pitch Bend and RPN
- Pitch Bend is a 14-bit value with centre 8192 (0x2000). The receiver's pitch-bend sensitivity determines the musical range; RPN 0,0 configures semitone and cent sensitivity.
- RPN 0,1 is Channel Fine Tuning; RPN 0,2 is Channel Coarse Tuning. Data Entry MSB/LSB are relevant to the selected RPN.
- Therefore, a raw pitch-bend value cannot be converted to cents without reconstructing the applicable channel state and knowing the range.
- Official references:
  - https://midi.org/summary-of-midi-1-0-messages
  - https://midi.org/midi-1-0-control-change-messages

### MIDI Tuning Standard
- MIDI Tuning Standard supports tunings beyond 12-tone equal temperament.
- It includes bulk tuning dumps, single-note tuning changes, and scale/octave tuning messages.
- Treat MTS as a separate tuning source from channel pitch bend and RPN fine/coarse tuning.
- Official references:
  - https://midi.org/midi-tuning-updated-specification
  - https://midi.org/midi-1-0-universal-system-exclusive-messages

### MPE
- MPE uses individual MIDI channels for per-note expression; this differs from ordinary channel-wide pitch bend.
- MPE support is optional and should follow the raw event preservation and channel-state work.
- Official reference: https://midi.org/mpe-midi-polyphonic-expression

### Web MIDI
- Web MIDI is a low-level live device input/output API. It does not directly implement Standard MIDI File parsing.
- It requires a secure context and permission; SysEx access is a stronger permission and should not be requested without a concrete requirement.
- Keep local SMF file parsing and live Web MIDI device input as separate adapters.
- Reference: https://www.w3.org/TR/webmidi/

### Myanmar repertoire evidence
- Smithsonian Folkways' Mahagita material documents Saung Gauk tuning variation between players, pieces, and regions. It gives an example in which E and B are tuned approximately 56 and 62 cents flat in a particular Hnyìnloùn context.
- This is evidence for a specific documented repertoire/instrument context, not a universal Myanmar tuning rule.
- Reference: https://folkways.si.edu/mahagita-harp-vocal-burma/world/music/article/smithsonian
- Aung & Campbell's Saung Gauk pedagogy paper describes five primary pitches and two ornamental extras in the discussed practice; do not generalize this to all Myanmar music.
- Reference: https://journals.sagepub.com/doi/10.1177/27527646231185567

## Proposed data architecture

### Layer 1 — Immutable source
- source file SHA-256
- original file bytes or immutable object reference
- parser name/version
- import timestamp and provenance

### Layer 2 — Raw event stream
- track index
- absolute tick and source delta tick
- event order within track
- raw status and data bytes
- decoded message family
- channel, where applicable
- opaque payload for unsupported/system-exclusive messages
- explicit parse warnings and unsupported-event markers

### Layer 3 — State reconstruction
- per-channel controller state
- RPN/NRPN selector state
- Data Entry MSB/LSB state
- pitch-bend sensitivity state
- channel fine/coarse tuning state
- MTS tuning bank/program and per-note tuning state, when fully decoded
- MPE zone/member-channel configuration, when recognized

State reconstruction must respect event order and scope. Unknown or incomplete configuration must remain unknown, not be filled with assumed defaults.

### Layer 4 — Derived performance pitch
- source MIDI note number
- pitch-bend value and applicable sensitivity
- tuning offset from RPN/MTS, if known
- calculated pitch/cents only when enough source state is present
- calculation algorithm/version and assumptions
- confidence/provenance marker

### Layer 5 — Music interpretation
- equal-tempered note spelling
- Western scale/key analysis
- Sargam labels
- named Myanmar repertoire/instrument tuning profile
- human-reviewed notation/transcription

No interpretation layer may overwrite raw source facts.

## Implementation gates

### Gate A — Raw event preservation
- Extend Python parser to retain supported channel voice events and opaque unsupported events.
- Extract browser parser into a separately testable module.
- Preserve existing note-event API and outputs.
- Ensure deterministic ordering for same-tick events using original event order as a tie-breaker.
- Do not silently discard Pitch Bend, Control Change, Program Change, Channel Pressure, or Polyphonic Key Pressure.

### Gate B — Channel state
- Reconstruct RPN selector (CC 101/100), Data Entry (CC 6/38), and Null RPN behavior.
- Test RPN 0,0; 0,1; 0,2; incomplete Data Entry; selection changes; channel isolation; and reset behavior.
- Never convert bend to cents without known sensitivity. If a compatibility profile assumes a default, expose the assumption and version it.

### Gate C — MTS
- Add MTS decoding as a separate SysEx parser with strict length/checksum/format validation based on the official updated specification.
- Support only message types with test fixtures and verified semantics.
- Preserve unknown SysEx payloads without interpretation.
- Add fixtures for bulk dump, single-note tuning change, scale/octave tuning, and malformed payloads.

### Gate D — Cross-runtime parity
- Use identical raw MIDI fixture bytes in Python and browser tests.
- Compare raw event sequence, event ordering, channel scope, reconstructed state, and derived values.
- Use Mido or another independent parser only for the subset it supports; do not treat its recovery behavior as normative for MTS or unknown SysEx.

### Gate E — Repertoire pilot
- Start with one named Saung Gauk repertoire/profile and source material.
- Record performer/instrument, region/context if documented, piece/version, reference pitch, measurement method, recording/score provenance, and reviewer.
- Retain multiple tunings where evidence documents variation.
- Require practitioner/researcher review before calling the profile verified.
- Do not generalize the profile to Nat Hsaing, Mahagita as a whole, or all Myanmar traditions.

## Acceptance criteria
- Existing note-only clients remain backward-compatible.
- Every supported raw event is preserved with track/channel/tick/order and original bytes.
- Unknown messages are retained or explicitly reported, never silently discarded.
- Bend-to-cents output is suppressed when sensitivity is unknown.
- RPN/MTS tuning interpretations are traceable to source messages and algorithm version.
- Browser/Python raw-event and state-reconstruction parity passes shared fixtures.
- Myanmar tuning profile is marked experimental until named-repertoire evidence and qualified review are complete.

## Out of scope for this phase
- Audio-to-MIDI transcription.
- Automatic inference of Myanmar tuning from arbitrary recordings.
- Universal Myanmar scale or tuning claims.
- Live MIDI device integration as a dependency for file import.
- MPE performance UI.
- Merge, release, or deployment authorization.

## Decision

Phase 02.74 should begin with Gate A (raw event preservation). Do not implement cents conversion, MTS interpretation, or Myanmar notation until the raw event stream and state-reconstruction tests are reliable.
