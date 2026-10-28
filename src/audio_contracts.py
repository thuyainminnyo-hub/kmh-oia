"""Provider-neutral contracts and validation for real KMH audio adapters.

This module intentionally contains no vendor SDK or credentials. Provider-specific
adapters should implement the protocols below and keep raw audio out of logs.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import wave
from typing import Protocol


class AudioContractError(ValueError):
    """Audio input is missing, malformed, or outside the supported contract."""


class AudioProviderError(RuntimeError):
    """A provider call failed; callers should preserve text fallback behavior."""


@dataclass(frozen=True)
class AudioInput:
    payload: bytes
    mime_type: str
    language_hint: str | None = "my"
    sample_rate_hz: int | None = None
    channels: int | None = None
    duration_ms: int | None = None


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    provider: str
    model: str
    latency_ms: int
    confidence: float | None = None


@dataclass(frozen=True)
class SynthesisResult:
    payload: bytes
    mime_type: str
    provider: str
    model: str
    latency_ms: int
    sample_rate_hz: int | None = None


class SpeechToTextAdapter(Protocol):
    def transcribe(self, audio: AudioInput) -> TranscriptionResult: ...


class TextToSpeechAdapter(Protocol):
    def synthesize(self, text: str, language: str = "my") -> SynthesisResult: ...


def _validate_optional_positive_integer(name: str, value: int | None) -> None:
    if value is not None and (type(value) is not int or value <= 0):
        raise AudioContractError(f"{name} must be a positive integer.")


def validate_audio_input(audio: AudioInput, *, max_bytes: int = 20_000_000) -> None:
    """Validate safe, basic transport metadata before passing bytes to a provider.

    This function validates the envelope only. Use validate_wav_input for WAV
    structural validation; do not infer a codec from the filename.
    """
    if not isinstance(audio.payload, bytes) or not audio.payload:
        raise AudioContractError("Audio payload is empty; provide a non-empty audio file.")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise AudioContractError("max_bytes must be a positive integer.")
    if len(audio.payload) > max_bytes:
        raise AudioContractError(f"Audio payload exceeds the {max_bytes}-byte limit.")
    if not isinstance(audio.mime_type, str) or not audio.mime_type or "/" not in audio.mime_type:
        raise AudioContractError("A valid audio MIME type is required.")
    if not audio.mime_type.lower().startswith("audio/"):
        raise AudioContractError("Unsupported MIME type: expected an audio/* type.")
    _validate_optional_positive_integer("sample_rate_hz", audio.sample_rate_hz)
    _validate_optional_positive_integer("channels", audio.channels)
    _validate_optional_positive_integer("duration_ms", audio.duration_ms)


def validate_wav_input(audio: AudioInput, *, max_bytes: int = 20_000_000) -> None:
    """Validate a WAV payload and cross-check declared metadata against its header."""
    validate_audio_input(audio, max_bytes=max_bytes)
    if audio.mime_type.lower() not in {"audio/wav", "audio/x-wav", "audio/wave"}:
        raise AudioContractError("This validator accepts WAV only; convert the file or use a matching adapter.")
    try:
        with wave.open(BytesIO(audio.payload), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frames = wav.getnframes()
            if channels < 1 or sample_rate < 1 or frames < 1:
                raise AudioContractError("WAV must contain audio frames and valid channel/sample-rate metadata.")
            if sample_width not in {1, 2, 3, 4}:
                raise AudioContractError("Unsupported WAV sample width.")
            if audio.channels is not None and audio.channels != channels:
                raise AudioContractError("Declared channels do not match the WAV header.")
            if audio.sample_rate_hz is not None and audio.sample_rate_hz != sample_rate:
                raise AudioContractError("Declared sample rate does not match the WAV header.")
            actual_duration_ms = frames * 1000 / sample_rate
            if audio.duration_ms is not None and abs(audio.duration_ms - actual_duration_ms) > 1:
                raise AudioContractError("Declared duration does not match the WAV frame count.")
    except (wave.Error, EOFError) as exc:
        raise AudioContractError("Invalid or unsupported WAV file; provide a valid PCM WAV recording.") from exc
