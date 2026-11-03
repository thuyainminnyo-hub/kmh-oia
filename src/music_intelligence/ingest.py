"""MIDI-to-candidate-library ingestion pipeline."""
import hashlib
from pathlib import Path
from typing import Optional

from .library import LocalMusicLibrary
from .midi_parser import parse_midi
from .number_notes import DualNumberNotesEngine


def import_midi_bytes(data: bytes, library: LocalMusicLibrary, *,
                      song_id: str, title: str, tonic: str = "C",
                      source_name: str = "uploaded.mid"):
    """Parse MIDI bytes, label notes in both systems, and save as candidate."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("MIDI input must be bytes")
    if not data:
        raise ValueError("MIDI input is empty")
    parsed = parse_midi(bytes(data))
    engine = DualNumberNotesEngine(key=tonic)
    events = []
    for note in parsed.notes:
        label = engine.convert(note.midi_pitch)
        events.append({
            "track": note.track,
            "channel": note.channel,
            "midi_pitch": note.midi_pitch,
            "velocity": note.velocity,
            "start_tick": note.start_tick,
            "end_tick": note.end_tick,
            "start_seconds": note.start_seconds,
            "end_seconds": note.end_seconds,
            "label": label,
        })
    if not events:
        raise ValueError("MIDI file contains no complete note events")
    digest = hashlib.sha256(bytes(data)).hexdigest()
    return library.add_candidate(
        song_id=song_id,
        title=title,
        note_events=events,
        tonic=tonic,
        source_name=source_name,
        source_sha256=digest,
    )


def import_midi_file(path, library: LocalMusicLibrary, *,
                     song_id: str, title: Optional[str] = None,
                     tonic: str = "C"):
    """Read a user-selected local MIDI path and ingest it into the library."""
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(str(source))
    if source.suffix.lower() not in (".mid", ".midi"):
        raise ValueError("only .mid and .midi files are supported")
    data = source.read_bytes()
    return import_midi_bytes(
        data, library,
        song_id=song_id,
        title=title or source.stem,
        tonic=tonic,
        source_name=source.name,
    )
