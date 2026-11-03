# Phase 02.69 — Dual Number Notes Engine

## Scope
A dependency-free, phone-first Python module maps an existing MIDI pitch number
to both (1) Western major-scale degree notation and (2) Sargam labels. The
initial tonic is C Major. Major-key transposition is configurable.

## Input and output
- Input: integer MIDI pitch 0..127.
- Output: pitch name, key, semitone distance from tonic, Western degree,
  Sargam label, and MIDI octave.
- MIDI octave convention: note 60 is C4.
- Both notation labels are returned together; callers do not choose one.

## Chromatic policy (v1)
Chromatic pitches are preserved and explicitly labeled:
- Western: b2, b3, #4, b6, b7
- Sargam: komal Re, komal Ga, tivra Ma, komal Dha, komal Ni

These are key-neutral degree spellings for the current major-key prototype.
Enharmonic spelling, melodic context, ornamentation, raga-specific rules, and
Myanmar traditional notation are outside this version's verified scope.

## Non-goals
This module does not perform audio transcription, detect a song key, parse MIDI
files, infer tempo, or certify a human-performed note. It labels supplied MIDI
pitch integers only.

## Local test
From the repository root:
```bash
python -m unittest tests.test_number_notes_engine -v
```
No third-party packages, network, cloud compute, or paid API are required.

## Promotion gate
Keep generated labels as extracted candidates. Promote to the verified music
library only after a human reviewer checks the source melody, tonic, octave,
chromatic spelling, and both notation outputs against an authorized reference.
