"""Deterministic synthetic SMF fixtures for Phase 02.71 parser validation.

Fixtures are generated from byte-level helpers so no copyrighted music or
third-party MIDI downloads are required. Each test asserts complete event data
or a strict parser rejection.
"""
import unittest

from src.music_intelligence.ingest import import_midi_bytes
from src.music_intelligence.library import LocalMusicLibrary
from src.music_intelligence.midi_parser import MIDIFormatError, parse_midi


def vlq(value):
    if not 0 <= value <= 0x0FFFFFFF:
        raise ValueError("VLQ outside SMF 4-byte range")
    encoded = [value & 0x7F]
    value >>= 7
    while value:
        encoded.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(encoded)


def chunk(kind, payload):
    if len(kind) != 4:
        raise ValueError("chunk type must be four bytes")
    return kind + len(payload).to_bytes(4, "big") + payload


def eot(delta=0):
    return vlq(delta) + b"\xFF\x2F\x00"


def make_track(events=b"", include_eot=True):
    return events + (eot() if include_eot else b"")


def make_smf(tracks, fmt=0, ppqn=480, header_extra=b"", prefix_chunks=b"",
             declared_tracks=None, suffix=b""):
    count = len(tracks) if declared_tracks is None else declared_tracks
    header = (fmt.to_bytes(2, "big") + count.to_bytes(2, "big")
              + ppqn.to_bytes(2, "big") + header_extra)
    result = chunk(b"MThd", header) + prefix_chunks
    result += b"".join(chunk(b"MTrk", track) for track in tracks)
    return result + suffix


def note_on(pitch, velocity=90, delta=0, channel=0):
    return vlq(delta) + bytes([0x90 | channel, pitch, velocity])


def note_off(pitch, delta=0, channel=0):
    return vlq(delta) + bytes([0x80 | channel, pitch, 0])


class TestMIDIGoldenValidFixtures(unittest.TestCase):
    def test_g001_format0_default_tempo_exact_event(self):
        raw = make_smf([make_track(note_on(60) + note_off(60, 480))])
        parsed = parse_midi(raw)
        self.assertEqual((parsed.format_type, parsed.ticks_per_quarter), (0, 480))
        self.assertEqual(parsed.tempo_events, ())
        self.assertEqual(len(parsed.notes), 1)
        note = parsed.notes[0]
        self.assertEqual(
            (note.track, note.channel, note.midi_pitch, note.velocity,
             note.start_tick, note.end_tick),
            (0, 0, 60, 90, 0, 480),
        )
        self.assertAlmostEqual(note.start_seconds, 0.0)
        self.assertAlmostEqual(note.end_seconds, 0.5)
        self.assertAlmostEqual(note.duration_seconds, 0.5)

    def test_g002_known_scale_sequence_event_order(self):
        events = b"".join(
            note_on(pitch) + note_off(pitch, 120)
            for pitch in (60, 62, 64)
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual(
            [(n.midi_pitch, n.start_tick, n.end_tick) for n in parsed.notes],
            [(60, 0, 120), (62, 120, 240), (64, 240, 360)],
        )

    def test_g003_format1_two_note_tracks(self):
        conductor = make_track(b"\x00\xFF\x51\x03\x07\xA1\x20")
        track_a = make_track(note_on(60) + note_off(60, 480))
        track_b = make_track(note_on(67) + note_off(67, 240))
        parsed = parse_midi(make_smf([conductor, track_a, track_b], fmt=1))
        self.assertEqual(parsed.track_count, 3)
        self.assertEqual(
            [(n.track, n.midi_pitch, n.start_tick, n.end_tick)
             for n in parsed.notes],
            [(1, 60, 0, 480), (2, 67, 0, 240)],
        )

    def test_g004_tempo_change_preserves_ticks_and_changes_seconds(self):
        events = (
            b"\x00\xFF\x51\x03\x07\xA1\x20"
            + note_on(60)
            + note_off(60, 480)
            + b"\x00\xFF\x51\x03\x0F\x42\x40"
            + note_on(62)
            + note_off(62, 480)
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual(parsed.tempo_events, ((0, 500000), (480, 1000000)))
        self.assertEqual([(n.start_tick, n.end_tick) for n in parsed.notes],
                         [(0, 480), (480, 960)])
        self.assertAlmostEqual(parsed.notes[0].end_seconds, 0.5)
        self.assertAlmostEqual(parsed.notes[1].start_seconds, 0.5)
        self.assertAlmostEqual(parsed.notes[1].end_seconds, 1.5)

    def test_g005_running_status_across_delta_times(self):
        events = (
            b"\x00\x90\x3C\x50"
            + b"\x00\x3E\x5A"
            + b"\x83\x60\x80\x3C\x00"
            + b"\x00\x3E\x00"
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual([n.midi_pitch for n in parsed.notes], [60, 62])

    def test_g006_zero_velocity_note_on_is_note_off(self):
        events = b"\x00\x90\x43\x46" + b"\x83\x60\x90\x43\x00"
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual(len(parsed.notes), 1)
        self.assertEqual((parsed.notes[0].midi_pitch,
                          parsed.notes[0].start_tick,
                          parsed.notes[0].end_tick), (67, 0, 480))

    def test_g007_overlapping_same_pitch_fifo_pairing(self):
        events = (
            b"\x00\x90\x3C\x50"
            + b"\x0A\x3C\x5A"
            + b"\x0A\x80\x3C\x00"
            + b"\x0A\x80\x3C\x00"
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual([(n.start_tick, n.end_tick) for n in parsed.notes],
                         [(0, 20), (10, 30)])
        self.assertEqual([n.velocity for n in parsed.notes], [80, 90])

    def test_g008_same_pitch_is_paired_per_channel(self):
        events = (
            note_on(60, 80, channel=0)
            + note_on(60, 90, channel=1)
            + note_off(60, 240, channel=0)
            + note_off(60, 240, channel=1)
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual(
            [(n.channel, n.start_tick, n.end_tick) for n in parsed.notes],
            [(0, 0, 240), (1, 0, 480)],
        )

    def test_g009_vlq_boundary_values(self):
        for delta in (0, 127, 128, 16383, 16384, 0x0FFFFFFF):
            with self.subTest(delta=delta):
                events = note_on(60) + note_off(60, delta)
                parsed = parse_midi(make_smf([make_track(events)]))
                self.assertEqual(parsed.notes[0].end_tick, delta)

    def test_g010_extended_header_length_is_honored(self):
        raw = make_smf(
            [make_track(note_on(60) + note_off(60, 480))],
            header_extra=b"\xAA\x55",
        )
        parsed = parse_midi(raw)
        self.assertEqual(len(parsed.notes), 1)
        self.assertEqual(parsed.notes[0].end_tick, 480)

    def test_g011_unknown_meta_event_payload_is_skipped(self):
        events = (
            b"\x00\xFF\x7F\x03abc"
            + note_on(64)
            + note_off(64, 120)
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual([(n.midi_pitch, n.end_tick) for n in parsed.notes],
                         [(64, 120)])

    def test_g012_unknown_chunk_is_skipped_by_declared_length(self):
        unknown = chunk(b"XTRA", b"\x01\x02\x03")
        raw = make_smf(
            [make_track(note_on(65) + note_off(65, 240))],
            prefix_chunks=unknown,
        )
        parsed = parse_midi(raw)
        self.assertEqual([(n.midi_pitch, n.end_tick) for n in parsed.notes],
                         [(65, 240)])

    def test_g013_sysex_resets_running_status_when_status_is_reintroduced(self):
        events = (
            b"\x00\x90\x3C\x5A"
            + b"\x00\xF0\x03\x01\x02\xF7"
            + b"\x00\x80\x3C\x00"
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual(len(parsed.notes), 1)
        self.assertEqual(parsed.notes[0].end_tick, 0)

    def test_g014_simultaneous_notes_have_stable_canonical_order(self):
        events = (
            note_on(67, delta=0)
            + note_on(60, delta=0)
            + note_off(67, delta=120)
            + note_off(60, delta=0)
        )
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual([n.midi_pitch for n in parsed.notes], [60, 67])

    def test_g015_format1_conductor_tempo_applies_to_all_tracks(self):
        conductor = make_track(b"\x00\xFF\x51\x03\x0F\x42\x40")
        notes = make_track(note_on(60) + note_off(60, 480))
        parsed = parse_midi(make_smf([conductor, notes], fmt=1))
        self.assertAlmostEqual(parsed.notes[0].duration_seconds, 1.0)
        self.assertEqual(parsed.tempo_events, ((0, 1000000),))

    def test_g016_explicit_note_off_after_sysex_works(self):
        events = note_on(72) + b"\x00\xF0\x01\xF7" + note_off(72, 480)
        parsed = parse_midi(make_smf([make_track(events)]))
        self.assertEqual([(n.midi_pitch, n.end_tick) for n in parsed.notes],
                         [(72, 480)])


class TestMIDIGoldenInvalidFixtures(unittest.TestCase):
    def assert_invalid(self, raw):
        with self.assertRaises(MIDIFormatError):
            parse_midi(raw)

    def test_n001_truncated_header(self):
        self.assert_invalid(b"MThd\x00")

    def test_n002_unsupported_format2(self):
        self.assert_invalid(make_smf([make_track()], fmt=2))

    def test_n003_zero_time_division(self):
        self.assert_invalid(make_smf([make_track()], ppqn=0))

    def test_n004_smpte_division(self):
        self.assert_invalid(make_smf([make_track()], ppqn=0xE728))

    def test_n005_truncated_chunk_header(self):
        self.assert_invalid(make_smf([make_track()]) + b"X")

    def test_n006_chunk_length_exceeds_file(self):
        header = chunk(b"MThd", b"\x00\x00\x00\x01\xE0\x00")
        self.assert_invalid(header + b"MTrk\x00\x00\x00\x64\x00")

    def test_n007_truncated_vlq(self):
        raw = make_smf([b"\x81"])
        self.assert_invalid(raw)

    def test_n008_vlq_exceeds_four_bytes(self):
        raw = make_smf([b"\x81\x80\x80\x80\x00"])
        self.assert_invalid(raw)

    def test_n009_unclosed_note_on(self):
        raw = make_smf([make_track(note_on(60), include_eot=True)])
        self.assert_invalid(raw)

    def test_n010_meta_event_cancels_running_status(self):
        events = (
            b"\x00\x90\x3C\x5A"
            + b"\x00\xFF\x01\x01x"
            + b"\x00\x3E\x5A"
        )
        self.assert_invalid(make_smf([make_track(events)]))

    def test_n011_sysex_cancels_running_status(self):
        events = (
            b"\x00\x90\x3C\x5A"
            + b"\x00\xF0\x01\xF7"
            + b"\x00\x3E\x5A"
        )
        self.assert_invalid(make_smf([make_track(events)]))

    def test_n012_missing_end_of_track(self):
        self.assert_invalid(make_smf([make_track(note_on(60) + note_off(60, 120),
                                                 include_eot=False)]))

    def test_n013_event_after_end_of_track(self):
        track = eot() + note_on(60) + note_off(60, 120)
        self.assert_invalid(make_smf([track]))

    def test_n014_malformed_end_of_track_payload(self):
        track = b"\x00\xFF\x2F\x01x"
        self.assert_invalid(make_smf([track]))

    def test_n015_malformed_tempo_event(self):
        for payload in (b"\x01\x02", b"\x00\x00\x00"):
            with self.subTest(payload=payload):
                track = b"\x00\xFF\x51" + vlq(len(payload)) + payload + eot()
                self.assert_invalid(make_smf([track]))

    def test_n016_truncated_meta_or_sysex_payload(self):
        meta = b"\x00\xFF\x01\x03ab"
        sysex = b"\x00\xF0\x05\x01\x02"
        self.assert_invalid(make_smf([meta]))
        self.assert_invalid(make_smf([sysex]))

    def test_n017_track_count_mismatch(self):
        first = make_track(note_on(60) + note_off(60, 120))
        second = make_track(note_on(64) + note_off(64, 120))
        self.assert_invalid(make_smf([first, second], fmt=1, declared_tracks=1))

    def test_n018_orphan_note_off_is_rejected(self):
        self.assert_invalid(make_smf([make_track(note_off(60))]))

    def test_n019_format1_tempo_outside_first_track_is_rejected(self):
        conductor = make_track()
        second = make_track(b"\x00\xFF\x51\x03\x07\xA1\x20")
        self.assert_invalid(make_smf([conductor, second], fmt=1))

    def test_n020_invalid_record_is_not_partially_ingested(self):
        valid_track = make_track(note_on(60) + note_off(60, 120))
        invalid_track = make_track(note_on(64), include_eot=False)
        raw = make_smf([valid_track, invalid_track], fmt=1)
        library = LocalMusicLibrary()
        try:
            with self.assertRaises(MIDIFormatError):
                import_midi_bytes(
                    raw, library, song_id="partial-001",
                    title="Must not be saved",
                )
            self.assertEqual(library.list_songs(), [])
        finally:
            library.close()




class TestGoldenFixtureCatalog(unittest.TestCase):
    def test_catalog_valid_fixtures_are_accepted(self):
        from midi_fixture_catalog import build_catalog

        catalog = build_catalog()
        for fixture_id, raw in catalog["valid"].items():
            with self.subTest(fixture=fixture_id):
                parse_midi(raw)

    def test_catalog_invalid_fixtures_are_rejected(self):
        from midi_fixture_catalog import build_catalog

        catalog = build_catalog()
        for fixture_id, raw in catalog["invalid"].items():
            with self.subTest(fixture=fixture_id):
                with self.assertRaises(MIDIFormatError):
                    parse_midi(raw)


if __name__ == "__main__":
    unittest.main()
