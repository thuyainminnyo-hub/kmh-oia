import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.android_video_adapter import AndroidMediaCodecVideoAdapter, AndroidVideoConfig
from src.production_execution import ProductionExecutionBridge
from src.production_job import ProductionJob


class AndroidMediaCodecAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"synthetic-source")
        self.output = self.root / "out"
        self.config = AndroidVideoConfig(
            str(self.source), str(self.output), width=640, height=360, fps=24,
        )
        self.job = ProductionJob.create("video", "controlled android render")

    def runner_for(self, encoder="h264_mediacodec"):
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            if command[0] == "getprop":
                return SimpleNamespace(returncode=0, stdout="test-device", stderr="")
            if command[:2] == ["ffmpeg", "-version"]:
                return SimpleNamespace(returncode=0, stdout="ffmpeg version test", stderr="")
            if command[:3] == ["ffmpeg", "-hide_banner", "-encoders"]:
                return SimpleNamespace(returncode=0, stdout=f" V..... {encoder} Android MediaCodec", stderr="")
            if command[0] == "ffmpeg":
                Path(command[-1]).write_bytes(b"synthetic-mp4")
                return SimpleNamespace(returncode=0, stdout="progress=end", stderr="")
            if command[0] == "ffprobe":
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "format": {"duration": "2.5", "format_name": "mov,mp4"},
                    "streams": [{"codec_type": "video", "codec_name": "h264",
                                 "width": 640, "height": 360}],
                }), stderr="")
            raise AssertionError(command)
        return runner, commands

    @patch("src.android_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_hardware_mediacodec_is_selected_and_verified(self, _which):
        runner, commands = self.runner_for()
        adapter = AndroidMediaCodecVideoAdapter(self.config, runner=runner)
        result = adapter.execute(ProductionJob(
            job_id=self.job.job_id, asset_type="video", prompt=self.job.prompt,
            status="running", attempt=1,
        ))
        self.assertTrue(result.success, result.error_message)
        render = next(c for c in commands if c[0] == "ffmpeg" and "-i" in c)
        self.assertIn("h264_mediacodec", render)
        self.assertIn("nv12", render)
        manifest = next(self.output.glob("*.execution.json"))
        data = json.loads(manifest.read_text())
        self.assertEqual(data["compute"]["mode"], "android-hardware-mediacodec")
        self.assertEqual(len(data["source"]["sha256"]), 64)
        self.assertEqual(len(data["output"]["sha256"]), 64)

    @patch("src.android_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_no_implicit_cpu_fallback(self, _which):
        runner, commands = self.runner_for(encoder="libx264")
        adapter = AndroidMediaCodecVideoAdapter(self.config, runner=runner)
        running = ProductionJob(
            job_id=self.job.job_id, asset_type="video", prompt=self.job.prompt,
            status="running", attempt=1,
        )
        result = adapter.execute(running)
        self.assertFalse(result.success)
        self.assertIn("CPU fallback is disabled", result.error_message)
        self.assertFalse(any(c[0] == "ffprobe" for c in commands))

    @patch("src.android_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_explicit_cpu_fallback_is_recorded(self, _which):
        runner, commands = self.runner_for(encoder="libx264")
        config = AndroidVideoConfig(
            str(self.source), str(self.output), width=640, height=360,
            allow_software_fallback=True,
        )
        adapter = AndroidMediaCodecVideoAdapter(config, runner=runner)
        running = ProductionJob(
            job_id=self.job.job_id, asset_type="video", prompt=self.job.prompt,
            status="running", attempt=1,
        )
        result = adapter.execute(running)
        self.assertTrue(result.success, result.error_message)
        render = next(c for c in commands if c[0] == "ffmpeg" and "-i" in c)
        self.assertIn("libx264", render)
        data = json.loads(next(self.output.glob("*.execution.json")).read_text())
        self.assertEqual(data["compute"]["mode"], "android-local-cpu-explicit-fallback")

    @patch("src.android_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_execution_bridge_stops_at_qa_pending(self, _which):
        runner, _ = self.runner_for()
        adapter = AndroidMediaCodecVideoAdapter(self.config, runner=runner)
        bridge = ProductionExecutionBridge(adapter, allowed_output_root=self.output)
        result = bridge.execute(self.job)
        self.assertEqual(result.status, "qa_pending")
        self.assertEqual(result.attempt, 1)

    @patch("src.android_video_adapter.shutil.which", return_value=None)
    def test_missing_ffmpeg_fails_closed(self, _which):
        running = ProductionJob(
            job_id=self.job.job_id, asset_type="video", prompt=self.job.prompt,
            status="running", attempt=1,
        )
        result = AndroidMediaCodecVideoAdapter(self.config).execute(running)
        self.assertFalse(result.success)
        self.assertIn("ffmpeg", result.error_message)

    def test_config_rejects_odd_dimensions(self):
        with self.assertRaisesRegex(ValueError, "even integers"):
            AndroidVideoConfig(str(self.source), str(self.output), width=641)


if __name__ == "__main__":
    unittest.main()
