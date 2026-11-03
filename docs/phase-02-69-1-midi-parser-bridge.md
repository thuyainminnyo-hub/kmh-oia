# Phase 02.69.1 — MIDI Parser Bridge

## Purpose
Parse an existing Standard MIDI File (SMF) without third-party dependencies,
then pass its MIDI pitches to the dual Western-degree/Sargam engine.

## Supported in v1
- SMF format 0 and 1; PPQN time division.
- Track chunks, channel note-on/note-off, running status.
- Note-on velocity zero treated as note-off.
- Tempo meta-event (0x51); default 500,000 microseconds per quarter note
  when no tempo event is present.
- Absolute tick positions, velocity, track, channel, and seconds are retained.
- Repeated overlapping same-pitch notes are paired FIFO within a track/channel.

## Explicit limits
- Does not decode WAV/MP3 or infer notes from audio.
- Does not support SMPTE timing, format 2, pitch bend, sustain pedal semantics,
  lyrics, or instrument-specific interpretation.
- An unmatched note-on is rejected instead of guessing its duration.
- Seconds are derived from MIDI tempo metadata and PPQN, not estimated from audio.
- Parser output is an extracted candidate, not a verified song transcription.

## Local phone-first test
From repository root:
```bash
python -m unittest discover -s tests -p 'test_midi_parser.py' -v
```
Only Python standard library is required.
