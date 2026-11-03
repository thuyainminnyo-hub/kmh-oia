# Phase 02.69.3 — MIDI Ingestion to Local Library

## Pipeline
User-selected local .mid/.midi file or supplied MIDI bytes
→ Standard MIDI File parser
→ Dual Western degree + Sargam labels
→ SHA-256 source-file digest
→ SQLite candidate library
→ JSON export (separate library API).

## Safety and governance
- Import does not upload data or call a paid provider.
- The file is read locally by the Python process.
- New records remain `candidate`; no automatic verification/promotion.
- SHA-256 identifies exact byte-for-byte file duplicates only when compared;
  it is not an acoustic fingerprint and does not identify alternate encodings.
- Only C major by default; other major tonic names can be supplied.
- MIDI file tempo metadata is preserved in event timing by the parser.
- Empty or note-free MIDI files are rejected.

## Android implementation note
The Python pipeline is platform-neutral; this commit does not create an Android
UI. For a phone-first UI, use an ordinary HTML file input as the baseline and
feature-detect optional browser file-picker APIs. Do not assume the File System
Access API exists on every Android browser. The browser must receive an explicit
user file selection; it must not scan private storage silently.

## Local test
```bash
python -m unittest discover -s tests -p 'test_ingest.py' -v
```

## Not covered
Audio-to-MIDI transcription, acoustic matching, folder scanning, Android UI,
Myanmar traditional notation, or human verification.
