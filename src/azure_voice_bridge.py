"""Bridge Azure's typed audio contracts to the existing VoiceRuntime protocols."""
from __future__ import annotations

from src.audio_contracts import AudioInput
from src.azure_speech_adapter import AzureSpeechAdapter
from src.voice import AudioFrame


class AzureSpeechToTextBridge:
    """Adapt WAV AudioFrame input to the provider-neutral Azure STT contract."""

    def __init__(self, adapter: AzureSpeechAdapter) -> None:
        self._adapter = adapter

    def transcribe(self, audio: AudioFrame) -> str:
        mime_type = audio.mime_type or "audio/wav"
        result = self._adapter.transcribe(
            AudioInput(payload=audio.payload, mime_type=mime_type, language_hint="my")
        )
        return result.text


class AzureTextToSpeechBridge:
    """Adapt Azure TTS output to the AudioFrame expected by VoiceRuntime."""

    def __init__(self, adapter: AzureSpeechAdapter) -> None:
        self._adapter = adapter

    def synthesize(self, text: str) -> AudioFrame:
        result = self._adapter.synthesize(text, language="my")
        return AudioFrame(payload=result.payload, mime_type=result.mime_type)
