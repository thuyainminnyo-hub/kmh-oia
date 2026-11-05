# Phase 02.69.2 — Local Candidate Library

## Storage
- SQLite stores songs and ordered MIDI note events.
- JSON export is the portable backup/interchange representation.
- No network, cloud account, paid API, or third-party Python package is required.
- The default in-memory database is useful for tests; pass a local file path for persistence.

## Governance
- New records are always inserted with status `candidate`.
- Promotion to `verified` or `rejected` requires an explicit review call and non-empty reviewer note.
- Extracted candidate data and human-reviewed data remain distinguishable.
- Exact pitch-sequence search is an ordered MIDI-pitch comparison, not an acoustic fingerprint.
- A source SHA-256 field may be stored when supplied, but this module does not compute or validate it.

## JSON
Export uses schema version 1 and preserves song metadata, note order, timing,
MIDI pitch, dual notation labels, and review state.

## Local tests
```bash
python -m unittest discover -s tests -p 'test_library.py' -v
```

## Limits
This library does not parse audio, perform acoustic similarity search, infer
the key, verify note transcription, or contain copyrighted songbook content.
A human reviewer must check an authorized source before marking a record verified.
