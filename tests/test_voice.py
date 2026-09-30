import unittest

from src.voice import AudioFrame, DeterministicSpeechCodec, VoiceRuntime


class VoiceRuntimeTests(unittest.TestCase):
    def test_audio_to_text_core_to_audio_round_trip(self):
        runtime = VoiceRuntime()
        audio, trace = runtime.execute(
            AudioFrame("hello from voice".encode("utf-8")),
            session_id="voice-e2e",
        )

        self.assertEqual(audio.payload, b"hello from voice")
        self.assertIn("input_gateway", trace.stages)
        self.assertIn("oia_core", trace.stages)
        self.assertIn("agent", trace.stages)
        self.assertIn("governed_tool", trace.stages)
        self.assertIn("evaluation", trace.stages)
        self.assertIn("response", trace.stages)
        self.assertIn("trace", trace.stages)

        keys = ("request_id", "session_id", "workflow_id", "task_id", "agent_id", "trace_id")
        first = {key: trace.events[0].metadata[key] for key in keys}
        for event in trace.events:
            self.assertEqual({key: event.metadata[key] for key in keys}, first)
        self.assertEqual(first["session_id"], "voice-e2e")

    def test_codec_is_explicitly_local_and_deterministic(self):
        codec = DeterministicSpeechCodec()
        self.assertEqual(codec.transcribe(codec.synthesize("မြန်မာစာ")), "မြန်မာစာ")


if __name__ == "__main__":
    unittest.main()
