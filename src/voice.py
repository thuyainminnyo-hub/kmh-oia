"""Deterministic voice adapters that reuse the KMH OIA text core."""

from dataclasses import dataclass
from typing import Protocol

from src.main import Trace, run


@dataclass(frozen=True)
class AudioFrame:
    """Transport-neutral audio payload used by the local voice contract."""

    payload: bytes


class SpeechToText(Protocol):
    def transcribe(self, audio: AudioFrame) -> str: ...


class TextToSpeech(Protocol):
    def synthesize(self, text: str) -> AudioFrame: ...


class DeterministicSpeechCodec:
    """Test codec: UTF-8 bytes represent the spoken text exactly."""

    def transcribe(self, audio: AudioFrame) -> str:
        return audio.payload.decode("utf-8")

    def synthesize(self, text: str) -> AudioFrame:
        return AudioFrame(text.encode("utf-8"))


class VoiceRuntime:
    """Voice boundary that delegates reasoning to the existing text runtime."""

    def __init__(
        self,
        speech_to_text: SpeechToText | None = None,
        text_to_speech: TextToSpeech | None = None,
    ) -> None:
        codec = DeterministicSpeechCodec()
        self.speech_to_text = speech_to_text or codec
        self.text_to_speech = text_to_speech or codec

    def execute(
        self,
        audio: AudioFrame,
        session_id: str = "default",
    ) -> tuple[AudioFrame, Trace]:
        goal = self.speech_to_text.transcribe(audio)
        response, trace = run(goal, session_id=session_id)
        return self.text_to_speech.synthesize(response), trace
