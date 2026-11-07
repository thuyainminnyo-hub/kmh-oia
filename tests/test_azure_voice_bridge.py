import io
import unittest
import wave

from src.audio_contracts import AudioProviderError, SynthesisResult, TranscriptionResult
from src.azure_voice_bridge import AzureSpeechToTextBridge, AzureTextToSpeechBridge
from src.voice import AudioFrame, VoiceRuntime


def make_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


class FakeAzureAdapter:
    def transcribe(self, audio):
        self.audio = audio
        return TranscriptionResult("hello from Azure", "fake", "fake-stt", 1)

    def synthesize(self, text, language="my"):
        self.text = text
        return SynthesisResult(b"mp3-data", "audio/mpeg", "fake", "fake-tts", 1)


class FailingTts:
    def transcribe(self, audio):
        return "hello"

    def synthesize(self, text):
        raise AudioProviderError("provider unavailable")


class AzureVoiceBridgeTests(unittest.TestCase):
    def test_stt_bridge_converts_audio_frame_to_audio_input(self):
        adapter = FakeAzureAdapter()
        bridge = AzureSpeechToTextBridge(adapter)
        self.assertEqual(bridge.transcribe(AudioFrame(make_wav(), "audio/wav")), "hello from Azure")
        self.assertEqual(adapter.audio.mime_type, "audio/wav")
        self.assertEqual(adapter.audio.language_hint, "my")

    def test_tts_bridge_preserves_output_mime_type(self):
        adapter = FakeAzureAdapter()
        frame = AzureTextToSpeechBridge(adapter).synthesize("မြန်မာစာ")
        self.assertEqual(frame.payload, b"mp3-data")
        self.assertEqual(frame.mime_type, "audio/mpeg")

    def test_voice_runtime_returns_text_fallback_if_tts_provider_fails(self):
        runtime = VoiceRuntime(speech_to_text=FailingTts(), text_to_speech=FailingTts())
        frame, trace = runtime.execute(AudioFrame(b"input"), session_id="azure-fallback")
        self.assertTrue(frame.mime_type.startswith("text/plain"))
        self.assertTrue(frame.payload)
        self.assertEqual(trace.events[0].metadata["session_id"], "azure-fallback")


if __name__ == "__main__":
    unittest.main()
