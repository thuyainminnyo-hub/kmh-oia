import tempfile
import unittest
from pathlib import Path

from src.music_intelligence.ingest import import_midi_bytes, import_midi_file
from src.music_intelligence.library import LocalMusicLibrary


def midi_with_two_notes():
    # C4 and G4, each one quarter note at the SMF default tempo.
    track = bytes([
        0, 0x90, 60, 100, 0x83, 0x60, 0x80, 60, 0,
        0, 0x90, 67, 90, 0x83, 0x60, 0x80, 67, 0,
        0, 0xFF, 0x2F, 0,
    ])
    header = (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big")
              + (1).to_bytes(2, "big") + (480).to_bytes(2, "big"))
    return header + b"MTrk" + len(track).to_bytes(4, "big") + track


class TestMIDIIngestion(unittest.TestCase):
    def setUp(self):
        self.library = LocalMusicLibrary()

    def tearDown(self):
        self.library.close()

    def test_bytes_import_to_candidate_with_both_labels(self):
        song = import_midi_bytes(
            midi_with_two_notes(), self.library,
            song_id="import-001", title="Two notes", tonic="C",
            source_name="two_notes.mid",
        )
        self.assertEqual(song["status"], "candidate")
        self.assertEqual([n["midi_pitch"] for n in song["notes"]], [60, 67])
        self.assertEqual(
            [(n["western_number"], n["sargam"]) for n in song["notes"]],
            [("1", "Sa"), ("5", "Pa")],
        )
        self.assertEqual(len(song["source_sha256"]), 64)

    def test_g_major_tonic_is_applied(self):
        song = import_midi_bytes(
            midi_with_two_notes(), self.library,
            song_id="import-g", title="G key", tonic="G",
        )
        self.assertEqual(song["notes"][0]["western_number"], "2")
        self.assertEqual(song["notes"][1]["western_number"], "1")

    def test_empty_midi_bytes_rejected(self):
        with self.assertRaises(ValueError):
            import_midi_bytes(b"", self.library, song_id="empty", title="Empty")

    def test_midi_without_complete_notes_rejected(self):
        track = bytes([0, 0xFF, 0x2F, 0])
        header = (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big")
                  + (1).to_bytes(2, "big") + (480).to_bytes(2, "big"))
        raw = header + b"MTrk" + len(track).to_bytes(4, "big") + track
        with self.assertRaises(ValueError):
            import_midi_bytes(raw, self.library, song_id="no-notes", title="No notes")

    def test_file_import(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.mid"
            path.write_bytes(midi_with_two_notes())
            song = import_midi_file(path, self.library, song_id="file-001")
            self.assertEqual(song["title"], "sample")
            self.assertEqual(song["source_name"], "sample.mid")

    def test_wrong_extension_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.wav"
            path.write_bytes(midi_with_two_notes())
            with self.assertRaises(ValueError):
                import_midi_file(path, self.library, song_id="wrong-ext")

    def test_candidate_not_auto_promoted(self):
        song = import_midi_bytes(
            midi_with_two_notes(), self.library,
            song_id="candidate-only", title="Candidate",
        )
        self.assertEqual(song["status"], "candidate")
        self.assertEqual(song["review_note"], "")


if __name__ == "__main__":
    unittest.main()
