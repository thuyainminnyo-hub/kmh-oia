"""Azure Speech REST adapter for KMH's provider-neutral audio contracts.

Uses the standard library so the core contract tests do not require a vendor SDK.
Credentials are read from environment variables and are never logged.
"""
from __future__ import annotations

import json
import os
from time import perf_counter
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

from src.audio_contracts import (
    AudioContractError,
    AudioInput,
    AudioProviderError,
    SynthesisResult,
    TranscriptionResult,
    validate_wav_input,
)

PostFunction = Callable[[str, dict[str, str], bytes, float], tuple[int, bytes]]


def _stdlib_post(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, bytes]:
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as exc:
        # Do not propagate provider response bodies: they may contain sensitive details.
        raise AudioProviderError(f"Azure Speech request failed with HTTP {exc.code}.") from None
    except (URLError, TimeoutError, OSError):
        raise AudioProviderError("Azure Speech request failed due to a network or timeout error.") from None


class AzureSpeechAdapter:
    """Short-audio Burmese STT and neural TTS using Azure Speech REST endpoints.

    Configure SPEECH_KEY and SPEECH_REGION in the server environment.
    The injected post function is intended for deterministic tests, not production.
    """

    provider = "azure-speech"

    def __init__(
        self,
        *,
        speech_key: str | None = None,
        region: str | None = None,
        stt_locale: str = "my-MM",
        tts_locale: str = "my-MM",
        tts_voice: str = "my-MM-NilarNeural",
        timeout_seconds: float = 20.0,
        post: PostFunction = _stdlib_post,
    ) -> None:
        self._speech_key = speech_key or os.getenv("SPEECH_KEY")
        self._region = region or os.getenv("SPEECH_REGION")
        if not self._speech_key or not self._region:
            raise AudioProviderError(
                "Azure Speech is not configured; set SPEECH_KEY and SPEECH_REGION."
            )
        if not self._region.replace("-", "").isalnum():
            raise AudioProviderError("SPEECH_REGION is invalid.")
        if timeout_seconds <= 0:
            raise AudioProviderError("timeout_seconds must be positive.")
        self._stt_locale = stt_locale
        self._tts_locale = tts_locale
        self._tts_voice = tts_voice
        self._timeout = timeout_seconds
        self._post = post

    def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        validate_wav_input(audio)
        locale = audio.language_hint or self._stt_locale
        if locale == "my":
            locale = "my-MM"
        query = urlencode({"language": locale, "format": "simple"})
        url = (
            f"https://{self._region}.stt.speech.microsoft.com/"
            f"speech/recognition/conversation/cognitiveservices/v1?{query}"
        )
        started = perf_counter()
        try:
            status, body = self._post(
                url,
                {
                    "Ocp-Apim-Subscription-Key": self._speech_key,
                    "Content-Type": audio.mime_type,
                    "Accept": "application/json",
                },
                audio.payload,
                self._timeout,
            )
        except AudioProviderError:
            raise
        except Exception:
            raise AudioProviderError("Azure Speech transcription request failed.") from None
        if status < 200 or status >= 300:
            raise AudioProviderError(f"Azure Speech transcription failed with HTTP {status}.")
        try:
            result = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AudioProviderError("Azure Speech returned an invalid transcription response.") from None
        if result.get("RecognitionStatus") != "Success":
            raise AudioProviderError("Azure Speech could not recognize speech in this audio.")
        text = result.get("DisplayText")
        if not isinstance(text, str) or not text.strip():
            raise AudioProviderError("Azure Speech returned an empty transcript.")
        return TranscriptionResult(
            text=text,
            provider=self.provider,
            model="speech-to-text-rest",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )

    def synthesize(self, text: str, language: str = "my") -> SynthesisResult:
        if not isinstance(text, str) or not text.strip():
            raise AudioContractError("Text to synthesize must be a non-empty string.")
        locale = self._tts_locale if language == "my" else language
        # SSML attributes are controlled configuration; user text is XML-escaped.
        ssml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<speak version="1.0" xml:lang="{escape(locale, {chr(34): "&quot;", chr(39): "&apos;"})}" '
            'xmlns="http://www.w3.org/2001/10/synthesis">'
            f'<voice name="{escape(self._tts_voice, {chr(34): "&quot;", chr(39): "&apos;"})}">'
            f'{escape(text)}</voice></speak>'
        ).encode("utf-8")
        url = f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1"
        started = perf_counter()
        try:
            status, payload = self._post(
                url,
                {
                    "Ocp-Apim-Subscription-Key": self._speech_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                    "User-Agent": "KMH-OIA-AudioAdapter",
                },
                ssml,
                self._timeout,
            )
        except AudioProviderError:
            raise
        except Exception:
            raise AudioProviderError("Azure Speech synthesis request failed.") from None
        if status < 200 or status >= 300:
            raise AudioProviderError(f"Azure Speech synthesis failed with HTTP {status}.")
        if not payload:
            raise AudioProviderError("Azure Speech returned an empty audio payload.")
        return SynthesisResult(
            payload=payload,
            mime_type="audio/mpeg",
            provider=self.provider,
            model=self._tts_voice,
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )
