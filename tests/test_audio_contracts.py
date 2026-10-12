import io
import unittest
import wave

from src.audio_contracts import (
    AudioContractError,
    AudioInput,
    TranscriptionResult,
    SynthesisResult,
    validate_audio_input,
    validate_wav_input,
)


def make_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


class AudioContractTests(unittest.TestCase):
    def test_accepts_well_formed_wav_and_burmese_language_hint(self):
        audio = AudioInput(
            payload=make_wav(),
            mime_type="audio/wav",
            language_hint="my",
            sample_rate_hz=16000,
            channels=1,
        )
        validate_wav_input(audio)

    def test_rejects_empty_audio(self):
        with self.assertRaisesRegex(AudioContractError, "empty"):
            validate_audio_input(AudioInput(b"", "audio/wav"))

    def test_rejects_non_audio_mime_type(self):
        with self.assertRaisesRegex(AudioContractError, "audio"):
            validate_audio_input(AudioInput(b"payload", "text/plain"))

    def test_rejects_payload_over_limit(self):
        with self.assertRaisesRegex(AudioContractError, "exceeds"):
            validate_audio_input(AudioInput(b"12345", "audio/wav"), max_bytes=4)

    def test_rejects_malformed_wav(self):
        with self.assertRaisesRegex(AudioContractError, "Invalid or unsupported WAV"):
            validate_wav_input(AudioInput(b"not a wav file", "audio/wav"))

    def test_rejects_metadata_mismatch(self):
        audio = AudioInput(make_wav(), "audio/wav", sample_rate_hz=8000)
        with self.assertRaisesRegex(AudioContractError, "sample rate"):
            validate_wav_input(audio)

    def test_result_contracts_are_provider_neutral(self):
        stt = TranscriptionResult("မင်္ဂလာပါ", "mock", "mock-stt", 12, 0.99)
        tts = SynthesisResult(b"audio", "audio/wav", "mock", "mock-tts", 18, 16000)
        self.assertEqual(stt.text, "မင်္ဂလာပါ")
        self.assertEqual(tts.mime_type, "audio/wav")


if __name__ == "__main__":
    unittest.main()
