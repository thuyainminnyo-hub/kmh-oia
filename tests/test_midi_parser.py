import unittest

from src.music_intelligence.midi_parser import MIDIFormatError, parse_midi
from src.music_intelligence.number_notes import DualNumberNotesEngine


def vlq(value):
    buffer = value & 0x7F
    value >>= 7
    while value:
        buffer <<= 8
        buffer |= ((value & 0x7F) | 0x80)
        value >>= 7
    out = bytearray()
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(out)


def midi_file(track, ppqn=480, fmt=0, tracks=1):
    header = b"MThd" + (6).to_bytes(4, "big") + fmt.to_bytes(2, "big")
    header += tracks.to_bytes(2, "big") + ppqn.to_bytes(2, "big")
    return header + b"MTrk" + len(track).to_bytes(4, "big") + track


class TestMIDIParser(unittest.TestCase):
    def test_note_events_and_default_tempo(self):
        # C4 on at tick 0, off after one quarter note.
        track = bytes([0, 0x90, 60, 100, 0x83, 0x60, 0x80, 60, 0, 0, 0xFF, 0x2F, 0])
        parsed = parse_midi(midi_file(track))
        self.assertEqual(len(parsed.notes), 1)
        note = parsed.notes[0]
        self.assertEqual((note.midi_pitch, note.velocity), (60, 100))
        self.assertEqual((note.start_tick, note.end_tick), (0, 480))
        self.assertAlmostEqual(note.duration_seconds, 0.5)

    def test_tempo_event_changes_seconds_not_ticks(self):
        # Tempo 1,000,000 us/quarter; note lasts one quarter note.
        track = bytes([0, 0xFF, 0x51, 3, 0x0F, 0x42, 0x40,
                       0, 0x90, 64, 90,
                       0x83, 0x60, 0x80, 64, 0,
                       0, 0xFF, 0x2F, 0])
        note = parse_midi(midi_file(track)).notes[0]
        self.assertAlmostEqual(note.duration_seconds, 1.0)

    def test_running_status_is_supported(self):
        # Second note-on reuses 0x90 status.
        track = bytes([0, 0x90, 60, 80, 0, 62, 90,
                       0x83, 0x60, 0x80, 60, 0,
                       0, 0x80, 62, 0, 0, 0xFF, 0x2F, 0])
        notes = parse_midi(midi_file(track)).notes
        self.assertEqual([n.midi_pitch for n in notes], [60, 62])

    def test_zero_velocity_note_on_is_note_off(self):
        track = bytes([0, 0x90, 67, 70, 0x83, 0x60, 0x90, 67, 0,
                       0, 0xFF, 0x2F, 0])
        self.assertEqual(len(parse_midi(midi_file(track)).notes), 1)

    def test_overlapping_same_pitch_pairs_fifo(self):
        track = bytes([0, 0x90, 60, 80, 10, 60, 90,
                       10, 0x80, 60, 0, 10, 0x80, 60, 0,
                       0, 0xFF, 0x2F, 0])
        notes = parse_midi(midi_file(track)).notes
        self.assertEqual([(n.start_tick, n.end_tick) for n in notes], [(0, 20), (10, 30)])

    def test_unclosed_note_rejected(self):
        track = bytes([0, 0x90, 60, 90, 0, 0xFF, 0x2F, 0])
        with self.assertRaises(MIDIFormatError):
            parse_midi(midi_file(track))

    def test_smpte_division_rejected(self):
        raw = midi_file(bytes([0, 0xFF, 0x2F, 0]), ppqn=480)
        raw = raw[:12] + bytes([0xE7, 0x28]) + raw[14:]
        with self.assertRaises(MIDIFormatError):
            parse_midi(raw)

    def test_malformed_header_rejected(self):
        with self.assertRaises(MIDIFormatError):
            parse_midi(b"not midi")

    def test_parser_to_dual_notes_engine(self):
        track = bytes([0, 0x90, 60, 90, 0x83, 0x60, 0x80, 60, 0,
                       0, 0x90, 67, 90, 0x83, 0x60, 0x80, 67, 0,
                       0, 0xFF, 0x2F, 0])
        events = parse_midi(midi_file(track)).notes
        labels = [DualNumberNotesEngine("C").label(e.midi_pitch) for e in events]
        self.assertEqual([(x.western_number, x.sargam) for x in labels],
                         [("1", "Sa"), ("5", "Pa")])


if __name__ == "__main__":
    unittest.main()
