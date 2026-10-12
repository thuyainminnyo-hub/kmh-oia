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


def validate_audio_input(audio: AudioInput, *, max_bytes: int = 20_000_000) -> None:
    """Validate safe, basic transport metadata before passing bytes to a provider.

    This function validates the envelope only. Use validate_wav_input for WAV
    structural validation; do not infer a codec from the filename.
    """
    if not isinstance(audio.payload, bytes) or not audio.payload:
        raise AudioContractError("Audio payload is empty; provide a non-empty audio file.")
    if len(audio.payload) > max_bytes:
        raise AudioContractError(f"Audio payload exceeds the {max_bytes}-byte limit.")
    if not audio.mime_type or "/" not in audio.mime_type:
        raise AudioContractError("A valid audio MIME type is required.")
    if not audio.mime_type.lower().startswith("audio/"):
        raise AudioContractError("Unsupported MIME type: expected an audio/* type.")
    if audio.sample_rate_hz is not None and audio.sample_rate_hz <= 0:
        raise AudioContractError("sample_rate_hz must be a positive integer.")
    if audio.channels is not None and audio.channels <= 0:
        raise AudioContractError("channels must be a positive integer.")
    if audio.duration_ms is not None and audio.duration_ms <= 0:
        raise AudioContractError("duration_ms must be a positive integer.")


def validate_wav_input(audio: AudioInput, *, max_bytes: int = 20_000_000) -> None:
    """Validate a WAV/PCM payload using the Python standard library."""
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
    except (wave.Error, EOFError) as exc:
        raise AudioContractError("Invalid or unsupported WAV file; provide a valid PCM WAV recording.") from exc
