"""Local SQLite library and JSON interchange for extracted music candidates.

Standard-library only. Candidate records remain unverified until an explicit
human-review promotion call is made.
"""
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional


class LibraryValidationError(ValueError):
    pass


class LocalMusicLibrary:
    def __init__(self, database_path=":memory:"):
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        self.connection.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS songs (
                song_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_name TEXT NOT NULL DEFAULT '',
                source_sha256 TEXT NOT NULL DEFAULT '',
                tonic TEXT NOT NULL DEFAULT 'C',
                mode TEXT NOT NULL DEFAULT 'major',
                status TEXT NOT NULL DEFAULT 'candidate'
                    CHECK(status IN ('candidate', 'verified', 'rejected')),
                review_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS note_events (
                song_id TEXT NOT NULL REFERENCES songs(song_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                track INTEGER NOT NULL,
                channel INTEGER NOT NULL,
                midi_pitch INTEGER NOT NULL CHECK(midi_pitch BETWEEN 0 AND 127),
                velocity INTEGER NOT NULL CHECK(velocity BETWEEN 0 AND 127),
                start_tick INTEGER NOT NULL CHECK(start_tick >= 0),
                end_tick INTEGER NOT NULL CHECK(end_tick >= start_tick),
                start_seconds REAL NOT NULL CHECK(start_seconds >= 0),
                end_seconds REAL NOT NULL CHECK(end_seconds >= start_seconds),
                western_number TEXT NOT NULL,
                sargam TEXT NOT NULL,
                pitch_name TEXT NOT NULL,
                octave INTEGER NOT NULL,
                PRIMARY KEY(song_id, ordinal)
            );
            CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
            CREATE INDEX IF NOT EXISTS idx_songs_fingerprint ON songs(source_sha256);
            CREATE INDEX IF NOT EXISTS idx_note_events_pitch ON note_events(midi_pitch);
        """)
        self.connection.commit()

    @staticmethod
    def _required_text(value, field):
        if not isinstance(value, str) or not value.strip():
            raise LibraryValidationError(field + " must be a non-empty string")
        return value.strip()

    def add_candidate(self, song_id, title, note_events, tonic="C",
                      source_name="", source_sha256="", mode="major"):
        song_id = self._required_text(song_id, "song_id")
        title = self._required_text(title, "title")
        if not isinstance(note_events, list) or not note_events:
            raise LibraryValidationError("note_events must be a non-empty list")
        if not isinstance(tonic, str) or len(tonic.strip()) not in (1, 2):
            raise LibraryValidationError("tonic must be a pitch-class name")
        if mode != "major":
            raise LibraryValidationError("only major mode is supported in v1")

        rows = []
        for index, event in enumerate(note_events):
            try:
                pitch = int(event["midi_pitch"])
                start_tick = int(event["start_tick"])
                end_tick = int(event["end_tick"])
                start_seconds = float(event["start_seconds"])
                end_seconds = float(event["end_seconds"])
                velocity = int(event.get("velocity", 0))
                track = int(event.get("track", 0))
                channel = int(event.get("channel", 0))
                label = event["label"]
                if not 0 <= pitch <= 127 or not 0 <= velocity <= 127:
                    raise ValueError("MIDI values outside valid range")
                if start_tick < 0 or end_tick < start_tick:
                    raise ValueError("invalid tick range")
                if start_seconds < 0 or end_seconds < start_seconds:
                    raise ValueError("invalid seconds range")
                rows.append((song_id, index, track, channel, pitch, velocity,
                             start_tick, end_tick, start_seconds, end_seconds,
                             str(label["western_number"]), str(label["sargam"]),
                             str(label["pitch_name"]), int(label["octave"])))
            except (KeyError, TypeError, ValueError) as exc:
                raise LibraryValidationError(
                    "invalid note event at index " + str(index) + ": " + str(exc)
                ) from exc

        with self.connection:
            self.connection.execute(
                """INSERT INTO songs
                (song_id,title,source_name,source_sha256,tonic,mode,status)
                VALUES (?,?,?,?,?,?, 'candidate')""",
                (song_id, title, str(source_name), str(source_sha256),
                 tonic.strip().upper(), mode),
            )
            self.connection.executemany(
                """INSERT INTO note_events
                (song_id,ordinal,track,channel,midi_pitch,velocity,start_tick,
                 end_tick,start_seconds,end_seconds,western_number,sargam,
                 pitch_name,octave)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows
            )
        return self.get_song(song_id)

    def get_song(self, song_id):
        song = self.connection.execute(
            "SELECT * FROM songs WHERE song_id=?", (song_id,)
        ).fetchone()
        if song is None:
            return None
        notes = self.connection.execute(
            "SELECT * FROM note_events WHERE song_id=? ORDER BY ordinal",
            (song_id,),
        ).fetchall()
        result = dict(song)
        result["notes"] = [dict(note) for note in notes]
        return result

    def list_songs(self, status: Optional[str] = None):
        if status is None:
            rows = self.connection.execute(
                "SELECT song_id,title,status,tonic,mode FROM songs ORDER BY title"
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT song_id,title,status,tonic,mode FROM songs WHERE status=? ORDER BY title",
                (status,),
            ).fetchall()
        return [dict(row) for row in rows]

    def find_exact_pitch_sequence(self, pitches):
        """Find candidates with the exact ordered MIDI pitch sequence."""
        requested = [int(pitch) for pitch in pitches]
        if not requested:
            return []
        matches = []
        for item in self.connection.execute("SELECT song_id FROM songs"):
            song = self.get_song(item["song_id"])
            actual = [note["midi_pitch"] for note in song["notes"]]
            if actual == requested:
                matches.append(song["song_id"])
        return matches

    def review(self, song_id, decision, reviewer_note):
        if decision not in ("verified", "rejected"):
            raise LibraryValidationError("decision must be verified or rejected")
        reviewer_note = self._required_text(reviewer_note, "reviewer_note")
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE songs SET status=?, review_note=? WHERE song_id=?",
                (decision, reviewer_note, song_id),
            )
            if cursor.rowcount != 1:
                raise KeyError("unknown song_id: " + str(song_id))
        return self.get_song(song_id)

    def export_json(self, destination=None, include_rejected=True):
        songs = self.connection.execute(
            "SELECT song_id FROM songs ORDER BY song_id"
        ).fetchall()
        records = []
        for row in songs:
            song = self.get_song(row["song_id"])
            if not include_rejected and song["status"] == "rejected":
                continue
            records.append(song)
        payload = {
            "schema_version": 1,
            "library_type": "kmh_music_intelligence_candidate_library",
            "songs": records,
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if destination is not None:
            Path(destination).expanduser().write_text(encoded + "\n", encoding="utf-8")
        return encoded

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
