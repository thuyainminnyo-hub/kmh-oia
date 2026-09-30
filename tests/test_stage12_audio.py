import unittest

from src.voice import AudioFrame, DeterministicSpeechCodec, VoiceRuntime


class Stage12AudioValidationTests(unittest.TestCase):
    def test_pv7_voice_path_round_trips_through_shared_text_core(self):
        runtime = VoiceRuntime()
        inputs = [
            "stage12 audio validation",
            "မြန်မာစာ အသံ စမ်းသပ်မှု",
        ]

        for index, text in enumerate(inputs):
            output, trace = runtime.execute(
                AudioFrame(text.encode("utf-8")),
                session_id=f"pv7-{index}",
            )

            self.assertEqual(output.payload, text.encode("utf-8"))
            self.assertEqual(trace.stages[-1], "trace")
            self.assertEqual(trace.events[-1].status, "ok")
            required = {
                "input_gateway",
                "oia_core",
                "context_assembly",
                "workflow",
                "agent",
                "governed_tool",
                "evaluation",
                "response",
                "trace",
            }
            self.assertTrue(required.issubset(set(trace.stages)))

            keys = (
                "request_id", "session_id", "workflow_id",
                "task_id", "agent_id", "trace_id",
            )
            context = {
                key: trace.events[0].metadata[key]
                for key in keys
            }
            for event in trace.events:
                self.assertEqual(
                    {key: event.metadata[key] for key in keys},
                    context,
                )
            self.assertEqual(context["session_id"], f"pv7-{index}")

    def test_pv7_codec_contract_is_deterministic_and_unicode_safe(self):
        codec = DeterministicSpeechCodec()
        for text in ("hello", "မြန်မာစာ", "voice ✓"):
            frame = codec.synthesize(text)
            self.assertEqual(frame.payload, text.encode("utf-8"))
            self.assertEqual(codec.transcribe(frame), text)


if __name__ == "__main__":
    unittest.main()
