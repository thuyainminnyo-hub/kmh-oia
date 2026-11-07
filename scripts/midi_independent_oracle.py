"""Cross-check supported golden MIDI fixtures with the independent Mido parser."""
from collections import defaultdict, deque
from io import BytesIO
import importlib.util
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

import mido

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_PATH = ROOT / "tests" / "test_midi_parser_golden.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "midi_golden_manifest.json"
# Mido's reader requires MThd to be followed immediately by MTrk and therefore
# cannot serve as an oracle for the explicit unknown-chunk skip fixture G012.
MIDO_UNSUPPORTED_CASES = {"G012_unknown_chunk"}


def load_test_module():
    spec = importlib.util.spec_from_file_location(
        "kmh_midi_golden_tests_for_mido_oracle", TEST_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_bytes_for_test(module, method_name):
    from src.music_intelligence import ingest

    test_class = module.TestMIDIGoldenValidFixtures
    captured = []
    parser = module.parse_midi
    ingest_parser = ingest.parse_midi

    def capture(original):
        def wrapped(data, *args, **kwargs):
            if isinstance(data, (bytes, bytearray)):
                captured.append(bytes(data))
            return original(data, *args, **kwargs)
        return wrapped

    result = unittest.TestResult()
    case = test_class(method_name)
    with patch.object(module, "parse_midi", capture(parser)), patch.object(
        ingest, "parse_midi", capture(ingest_parser)
    ):
        unittest.TestSuite([case]).run(result)
    if not result.wasSuccessful():
        details = "\\n".join(item[1] for item in result.errors + result.failures)
        raise RuntimeError(f"{method_name} failed while collecting fixture bytes:\\n{details}")
    if not captured:
        raise RuntimeError(f"{method_name} yielded no fixture bytes")
    return captured


def mido_notes(raw):
    midi = mido.MidiFile(file=BytesIO(raw), clip=False)
    active = defaultdict(deque)
    notes = []
    for track_index, track in enumerate(midi.tracks):
        tick = 0
        for message in track:
            tick += message.time
            if message.is_meta or not message.type in ("note_on", "note_off"):
                continue
            key = (track_index, message.channel, message.note)
            if message.type == "note_on" and message.velocity > 0:
                active[key].append((tick, message.velocity))
            else:
                if not active[key]:
                    raise AssertionError(f"Mido found orphan note-off: {key} at {tick}")
                start_tick, velocity = active[key].popleft()
                notes.append((track_index, message.channel, message.note,
                              velocity, start_tick, tick))
    dangling = [key for key, queue in active.items() if queue]
    if dangling:
        raise AssertionError(f"Mido found unclosed notes: {dangling}")
    return midi, sorted(notes)


def tick_seconds(tick, midi):
    tempo_events = []
    for message in midi.tracks[0]:
        if message.type == "set_tempo":
            tempo_events.append((sum_time_before(midi.tracks[0], message), message.tempo))
    tempo_events.sort(key=lambda item: item[0])
    elapsed = 0.0
    previous_tick = 0
    tempo = 500000
    for event_tick, event_tempo in tempo_events:
        if event_tick > tick:
            break
        elapsed += mido.tick2second(event_tick - previous_tick,
                                    midi.ticks_per_beat, tempo)
        previous_tick = event_tick
        tempo = event_tempo
    elapsed += mido.tick2second(tick - previous_tick, midi.ticks_per_beat, tempo)
    return elapsed


def sum_time_before(track, target):
    tick = 0
    for message in track:
        tick += message.time
        if message is target:
            return tick
    raise AssertionError("tempo message was not found in its source track")


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    module = load_test_module()
    results = []
    checked = 0
    skipped = []
    for case_id in manifest["valid_cases"]:
        if case_id in MIDO_UNSUPPORTED_CASES:
            skipped.append({"case_id": case_id, "reason": "Mido reader does not support unknown chunks before MTrk"})
            continue
        prefix = "test_" + case_id.split("_", 1)[0].lower() + "_"
        method_name = next(
            (name for name in dir(module.TestMIDIGoldenValidFixtures)
             if name.startswith(prefix)), None
        )
        if method_name is None:
            raise RuntimeError(f"No golden test method found for {case_id}")
        raw_fixtures = fixture_bytes_for_test(module, method_name)
        for fixture_index, raw in enumerate(raw_fixtures):
            independent_midi, oracle = mido_notes(raw)
            parsed = module.parse_midi(raw)
            actual = sorted(
                (n.track, n.channel, n.midi_pitch, n.velocity,
                 n.start_tick, n.end_tick)
                for n in parsed.notes
            )
            if actual != oracle:
                raise AssertionError(
                    f"{case_id}[{fixture_index}] note mismatch: KMH={actual}, Mido={oracle}"
                )
            for note in parsed.notes:
                for tick, seconds in (
                    (note.start_tick, note.start_seconds),
                    (note.end_tick, note.end_seconds),
                ):
                    reference = tick_seconds(tick, independent_midi)
                    if abs(seconds - reference) > 1e-9:
                        raise AssertionError(
                            f"{case_id}[{fixture_index}] time mismatch at tick {tick}: "
                            f"KMH={seconds}, Mido={reference}"
                        )
            checked += 1
            results.append({"case_id": case_id, "fixture_index": fixture_index,
                            "note_count": len(actual), "result": "PASS"})
    evidence = {
        "schema": "kmh.midi-independent-parser-evidence.v1",
        "oracle": "Mido",
        "oracle_version": mido.version_info,
        "fixture_cases_checked": checked,
        "fixture_cases_skipped": skipped,
        "results": results,
        "status": "PASS",
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))
    print(f"MIDI INDEPENDENT PARSER CROSS-CHECK: PASS ({checked} fixtures; {len(skipped)} documented skip)")


if __name__ == "__main__":
    main()
