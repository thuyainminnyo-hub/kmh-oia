import io
import json
import unittest
import wave
from urllib.parse import urlparse, parse_qs

from src.audio_contracts import AudioContractError, AudioInput, AudioProviderError
from src.azure_speech_adapter import AzureSpeechAdapter


def make_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


class AzureSpeechAdapterTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append((url, headers, body, timeout))
        if ".stt." in url:
            return 200, json.dumps({
                "RecognitionStatus": "Success",
                "DisplayText": "မင်္ဂလာပါ",
            }).encode("utf-8")
        return 200, b"fake-mp3-audio"

    def adapter(self):
        return AzureSpeechAdapter(
            speech_key="test-key",
            region="southeastasia",
            post=self.post,
        )

    def test_transcribes_burmese_wav_with_expected_locale_and_no_key_in_url(self):
        result = self.adapter().transcribe(
            AudioInput(make_wav(), "audio/wav", language_hint="my")
        )
        self.assertEqual(result.text, "မင်္ဂလာပါ")
        self.assertEqual(result.provider, "azure-speech")
        self.assertEqual(parse_qs(urlparse(self.calls[0][0]).query)["language"], ["my-MM"])
        self.assertNotIn("test-key", self.calls[0][0])
        self.assertEqual(self.calls[0][1]["Ocp-Apim-Subscription-Key"], "test-key")

    def test_rejects_invalid_audio_before_network_call(self):
        with self.assertRaises(AudioContractError):
            self.adapter().transcribe(AudioInput(b"not wav", "audio/wav"))
        self.assertEqual(self.calls, [])

    def test_provider_non_success_is_safe_error(self):
        adapter = AzureSpeechAdapter(
            speech_key="test-key",
            region="southeastasia",
            post=lambda *args: (200, b'{"RecognitionStatus":"NoMatch","DisplayText":""}'),
        )
        with self.assertRaisesRegex(AudioProviderError, "could not recognize"):
            adapter.transcribe(AudioInput(make_wav(), "audio/wav"))

    def test_synthesizes_escaped_text_to_mp3(self):
        result = self.adapter().synthesize('မြန်မာ <test> & "text"')
        self.assertEqual(result.payload, b"fake-mp3-audio")
        self.assertEqual(result.mime_type, "audio/mpeg")
        self.assertIn(b"&lt;test&gt; &amp;", self.calls[0][2])
        self.assertEqual(self.calls[0][1]["X-Microsoft-OutputFormat"], "audio-24khz-48kbitrate-mono-mp3")

    def test_synthesis_rejects_empty_text_without_network_call(self):
        with self.assertRaises(AudioContractError):
            self.adapter().synthesize("  ")
        self.assertEqual(self.calls, [])

    def test_requires_credentials_and_region(self):
        with self.assertRaisesRegex(AudioProviderError, "not configured"):
            AzureSpeechAdapter(speech_key="", region="", post=self.post)


if __name__ == "__main__":
    unittest.main()
