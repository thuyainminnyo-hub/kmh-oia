"""Dual Western-degree and Sargam labels for equal-tempered MIDI pitches.

The engine labels pitch classes relative to a major-key tonic. It does not
transcribe audio, infer a tonic, or claim to encode Myanmar traditional notation.
Octave numbers follow the MIDI convention where note 60 is C4.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class NumberNotation(str, Enum):
    WESTERN = "western"
    SARGAM = "sargam"


# Semitone distance from the tonic in a major scale, including chromatic tones.
# The accidental spelling is intentionally key-neutral for this first version.
_WESTERN: Dict[int, Tuple[str, str]] = {
    0: ("1", "tonic"),
    1: ("b2", "chromatic"),
    2: ("2", "major_second"),
    3: ("b3", "chromatic"),
    4: ("3", "major_third"),
    5: ("4", "perfect_fourth"),
    6: ("#4", "chromatic"),
    7: ("5", "perfect_fifth"),
    8: ("b6", "chromatic"),
    9: ("6", "major_sixth"),
    10: ("b7", "chromatic"),
    11: ("7", "major_seventh"),
}

_SARGAM: Dict[int, str] = {
    0: "Sa",
    1: "komal Re",
    2: "Re",
    3: "komal Ga",
    4: "Ga",
    5: "Ma",
    6: "tivra Ma",
    7: "Pa",
    8: "komal Dha",
    9: "Dha",
    10: "komal Ni",
    11: "Ni",
}

_PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F",
                  "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True)
class NoteLabel:
    midi_pitch: int
    pitch_name: str
    key: str
    semitones_from_tonic: int
    western_number: str
    sargam: str
    octave: int

    def as_dict(self) -> dict:
        return {
            "midi_pitch": self.midi_pitch,
            "pitch_name": self.pitch_name,
            "key": self.key,
            "semitones_from_tonic": self.semitones_from_tonic,
            "western_number": self.western_number,
            "sargam": self.sargam,
            "octave": self.octave,
        }


class DualNumberNotesEngine:
    """Map MIDI pitches into Western scale degrees and Sargam simultaneously."""

    def __init__(self, key: str = "C", mode: str = "major") -> None:
        normalized = key.strip().upper()
        if normalized not in _PITCH_CLASSES:
            raise ValueError("key must be one of: " + ", ".join(_PITCH_CLASSES))
        if mode.strip().lower() != "major":
            raise ValueError("Phase 02.69 currently supports major keys only")
        self.key = normalized
        self.mode = "major"
        self._tonic_pc = _PITCH_CLASSES.index(normalized)

    def label(self, midi_pitch: int) -> NoteLabel:
        if isinstance(midi_pitch, bool) or not isinstance(midi_pitch, int):
            raise TypeError("midi_pitch must be an integer")
        if not 0 <= midi_pitch <= 127:
            raise ValueError("midi_pitch must be in the MIDI range 0..127")

        pitch_class = midi_pitch % 12
        relative = (pitch_class - self._tonic_pc) % 12
        octave = (midi_pitch // 12) - 1
        return NoteLabel(
            midi_pitch=midi_pitch,
            pitch_name=f"{_PITCH_CLASSES[pitch_class]}{octave}",
            key=f"{self.key} {self.mode.title()}",
            semitones_from_tonic=relative,
            western_number=_WESTERN[relative][0],
            sargam=_SARGAM[relative],
            octave=octave,
        )

    def label_many(self, midi_pitches):
        """Return labels in input order; repeated pitches remain repeated."""
        return [self.label(pitch) for pitch in midi_pitches]

    def convert(self, midi_pitch: int) -> dict:
        """Convenience output containing both notation systems."""
        return self.label(midi_pitch).as_dict()
