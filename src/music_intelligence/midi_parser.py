"""Small Standard MIDI File (SMF) parser using only the Python standard library.

Supports format 0/1, PPQN timing, note-on/off, running status, and tempo
meta-events. It does not infer notes from audio or support SMPTE time division.
"""
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Tuple


class MIDIFormatError(ValueError):
    """Raised when the input is not a supported, structurally valid SMF."""


@dataclass(frozen=True)
class MIDINoteEvent:
    track: int
    channel: int
    midi_pitch: int
    velocity: int
    start_tick: int
    end_tick: int
    start_seconds: float
    end_seconds: float
    duration_seconds: float


@dataclass(frozen=True)
class MIDIFile:
    format_type: int
    ticks_per_quarter: int
    track_count: int
    tempo_events: Tuple[Tuple[int, int], ...]
    notes: Tuple[MIDINoteEvent, ...]


def _read_vlq(data: bytes, offset: int, end: int) -> Tuple[int, int]:
    value = 0
    for _ in range(4):
        if offset >= end:
            raise MIDIFormatError("truncated variable-length quantity")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset
    raise MIDIFormatError("variable-length quantity exceeds four bytes")


def _parse_track(data: bytes, track_index: int):
    offset = 0
    end = len(data)
    tick = 0
    running_status = None
    active = defaultdict(deque)
    completed = []
    tempos = []
    while offset < end:
        delta, offset = _read_vlq(data, offset, end)
        tick += delta
        if offset >= end:
            raise MIDIFormatError("track ended before event status")
        status = data[offset]
        if status & 0x80:
            offset += 1
            if status < 0xF0:
                running_status = status
        else:
            if running_status is None:
                raise MIDIFormatError("running status used before channel status")
            status = running_status

        if status == 0xFF:
            if offset >= end:
                raise MIDIFormatError("truncated meta event")
            meta_type = data[offset]
            offset += 1
            length, offset = _read_vlq(data, offset, end)
            payload_end = offset + length
            if payload_end > end:
                raise MIDIFormatError("meta event exceeds track boundary")
            payload = data[offset:payload_end]
            offset = payload_end
            if meta_type == 0x51:
                if length != 3:
                    raise MIDIFormatError("tempo meta-event must contain 3 bytes")
                tempo = int.from_bytes(payload, "big")
                if tempo <= 0:
                    raise MIDIFormatError("tempo must be greater than zero")
                tempos.append((tick, tempo))
            if meta_type == 0x2F:
                break
            continue

        if status in (0xF0, 0xF7):
            length, offset = _read_vlq(data, offset, end)
            offset += length
            if offset > end:
                raise MIDIFormatError("system-exclusive event exceeds track boundary")
            running_status = None
            continue

        if status >= 0xF0:
            raise MIDIFormatError("unsupported system MIDI event")
        command = status & 0xF0
        channel = status & 0x0F
        size = 1 if command in (0xC0, 0xD0) else 2
        if offset + size > end:
            raise MIDIFormatError("truncated channel event")
        first = data[offset]
        second = data[offset + 1] if size == 2 else 0
        offset += size
        if first > 127 or second > 127:
            raise MIDIFormatError("channel data bytes must be 7-bit values")

        if command == 0x90 and second > 0:
            active[(channel, first)].append((tick, second))
        elif command == 0x80 or (command == 0x90 and second == 0):
            queue = active[(channel, first)]
            if queue:
                start_tick, velocity = queue.popleft()
                completed.append((track_index, channel, first, velocity,
                                  start_tick, tick))
    dangling = sum(len(queue) for queue in active.values())
    if dangling:
        raise MIDIFormatError("one or more note-on events have no matching note-off")
    return completed, tempos


def _tick_to_seconds(tick: int, tempo_map, ppqn: int) -> float:
    elapsed = 0.0
    previous_tick = 0
    current_tempo = 500000  # SMF default: 120 quarter-note beats/minute.
    for event_tick, tempo in tempo_map:
        if event_tick > tick:
            break
        if event_tick > previous_tick:
            elapsed += ((event_tick - previous_tick) * current_tempo) / (ppqn * 1_000_000)
            previous_tick = event_tick
        current_tempo = tempo
    elapsed += ((tick - previous_tick) * current_tempo) / (ppqn * 1_000_000)
    return elapsed


def parse_midi(data: bytes) -> MIDIFile:
    """Parse MIDI bytes into note events with absolute ticks and seconds."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes")
    data = bytes(data)
    if len(data) < 14 or data[:4] != b"MThd":
        raise MIDIFormatError("missing or truncated MThd header")
    header_length = int.from_bytes(data[4:8], "big")
    if header_length < 6 or 8 + header_length > len(data):
        raise MIDIFormatError("invalid MIDI header length")
    format_type = int.from_bytes(data[8:10], "big")
    track_count = int.from_bytes(data[10:12], "big")
    division = int.from_bytes(data[12:14], "big")
    if format_type not in (0, 1):
        raise MIDIFormatError("only MIDI formats 0 and 1 are supported")
    if track_count < 1 or (format_type == 0 and track_count != 1):
        raise MIDIFormatError("invalid track count for MIDI format")
    if division & 0x8000 or division == 0:
        raise MIDIFormatError("SMPTE or zero time division is not supported")
    ppqn = division

    offset = 8 + header_length
    raw_notes = []
    tempo_events = []
    parsed_tracks = 0
    while offset < len(data):
        if offset + 8 > len(data) or data[offset:offset + 4] != b"MTrk":
            raise MIDIFormatError("missing or truncated MTrk chunk")
        length = int.from_bytes(data[offset + 4:offset + 8], "big")
        start = offset + 8
        stop = start + length
        if stop > len(data):
            raise MIDIFormatError("track chunk exceeds file boundary")
        notes, tempos = _parse_track(data[start:stop], parsed_tracks)
        raw_notes.extend(notes)
        tempo_events.extend(tempos)
        parsed_tracks += 1
        offset = stop
    if parsed_tracks != track_count:
        raise MIDIFormatError("header track count does not match track chunks")

    # At the same tick, later-listed tempo events take precedence deterministically.
    tempo_events.sort(key=lambda item: item[0])
    tempo_map = []
    for event in tempo_events:
        if tempo_map and tempo_map[-1][0] == event[0]:
            tempo_map[-1] = event
        else:
            tempo_map.append(event)

    notes = []
    for track, channel, pitch, velocity, start_tick, end_tick in raw_notes:
        if end_tick < start_tick:
            raise MIDIFormatError("note-off precedes note-on")
        start_seconds = _tick_to_seconds(start_tick, tempo_map, ppqn)
        end_seconds = _tick_to_seconds(end_tick, tempo_map, ppqn)
        notes.append(MIDINoteEvent(
            track, channel, pitch, velocity, start_tick, end_tick,
            start_seconds, end_seconds, end_seconds - start_seconds,
        ))
    notes.sort(key=lambda note: (note.start_tick, note.track, note.channel, note.midi_pitch))
    return MIDIFile(format_type, ppqn, parsed_tracks, tuple(tempo_map), tuple(notes))
