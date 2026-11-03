import unittest

from src.music_intelligence.number_notes import DualNumberNotesEngine


class TestDualNumberNotesEngineCmajor(unittest.TestCase):
    def setUp(self):
        self.engine = DualNumberNotesEngine(key="C")

    def test_c_major_scale_both_systems(self):
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]
        labels = self.engine.label_many(pitches)
        self.assertEqual(
            [item.western_number for item in labels],
            ["1", "2", "3", "4", "5", "6", "7", "1"],
        )
        self.assertEqual(
            [item.sargam for item in labels],
            ["Sa", "Re", "Ga", "Ma", "Pa", "Dha", "Ni", "Sa"],
        )

    def test_chromatic_notes_are_not_silently_rounded(self):
        label = self.engine.label(61)
        self.assertEqual(label.western_number, "b2")
        self.assertEqual(label.sargam, "komal Re")
        self.assertEqual(label.semitones_from_tonic, 1)

    def test_octave_is_preserved(self):
        self.assertEqual(self.engine.label(60).octave, 4)
        self.assertEqual(self.engine.label(72).octave, 5)

    def test_output_contains_both_systems(self):
        result = self.engine.convert(67)
        self.assertEqual(result["western_number"], "5")
        self.assertEqual(result["sargam"], "Pa")
        self.assertEqual(result["key"], "C Major")

    def test_invalid_midi_pitch_rejected(self):
        for pitch in (-1, 128):
            with self.subTest(pitch=pitch):
                with self.assertRaises(ValueError):
                    self.engine.label(pitch)

    def test_non_integer_pitch_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.label(60.5)

    def test_major_key_transposition(self):
        g_major = DualNumberNotesEngine(key="G")
        self.assertEqual(g_major.label(67).western_number, "1")
        self.assertEqual(g_major.label(69).western_number, "2")
        self.assertEqual(g_major.label(67).sargam, "Sa")

    def test_unsupported_mode_rejected(self):
        with self.assertRaises(ValueError):
            DualNumberNotesEngine(key="C", mode="minor")


if __name__ == "__main__":
    unittest.main()
