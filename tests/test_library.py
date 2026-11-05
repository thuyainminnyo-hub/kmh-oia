import json
import tempfile
import unittest
from pathlib import Path

from src.music_intelligence.library import (
    LibraryValidationError, LocalMusicLibrary,
)


def event(pitch, ordinal):
    return {
        "track": 0, "channel": 0, "midi_pitch": pitch, "velocity": 90,
        "start_tick": ordinal * 480, "end_tick": (ordinal + 1) * 480,
        "start_seconds": ordinal * 0.5, "end_seconds": (ordinal + 1) * 0.5,
        "label": {
            "western_number": str(ordinal + 1), "sargam": "Sa",
            "pitch_name": "C4", "octave": 4,
        },
    }


class TestLocalMusicLibrary(unittest.TestCase):
    def setUp(self):
        self.library = LocalMusicLibrary()
        self.library.add_candidate(
            "demo-001", "Test melody", [event(60, 0), event(64, 1), event(67, 2)],
            tonic="C", source_name="demo.mid", source_sha256="abc123",
        )

    def tearDown(self):
        self.library.close()

    def test_new_records_are_candidates(self):
        self.assertEqual(self.library.get_song("demo-001")["status"], "candidate")

    def test_note_order_and_dual_labels_preserved(self):
        song = self.library.get_song("demo-001")
        self.assertEqual([n["midi_pitch"] for n in song["notes"]], [60, 64, 67])
        self.assertEqual(song["notes"][2]["western_number"], "3")
        self.assertEqual(song["notes"][2]["sargam"], "Sa")

    def test_exact_sequence_search(self):
        self.assertEqual(self.library.find_exact_pitch_sequence([60, 64, 67]), ["demo-001"])
        self.assertEqual(self.library.find_exact_pitch_sequence([60, 67]), [])

    def test_json_export_round_trip_shape(self):
        payload = json.loads(self.library.export_json())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["songs"][0]["song_id"], "demo-001")
        self.assertEqual(len(payload["songs"][0]["notes"]), 3)

    def test_json_export_to_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backup.json"
            self.library.export_json(path)
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text())["songs"][0]["title"], "Test melody")

    def test_review_is_explicit(self):
        reviewed = self.library.review("demo-001", "verified", "Checked against authorized score")
        self.assertEqual(reviewed["status"], "verified")
        self.assertEqual(reviewed["review_note"], "Checked against authorized score")

    def test_invalid_review_rejected(self):
        with self.assertRaises(LibraryValidationError):
            self.library.review("demo-001", "approved", "ok")

    def test_invalid_pitch_rejected(self):
        bad = event(200, 0)
        with self.assertRaises(LibraryValidationError):
            self.library.add_candidate("bad", "Bad", [bad])

    def test_duplicate_song_id_rejected(self):
        with self.assertRaises(Exception):
            self.library.add_candidate("demo-001", "Duplicate", [event(60, 0)])

    def test_unknown_review_target_rejected(self):
        with self.assertRaises(KeyError):
            self.library.review("missing", "verified", "reviewed")


if __name__ == "__main__":
    unittest.main()
