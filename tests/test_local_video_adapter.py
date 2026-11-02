import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.local_video_adapter import (
    LocalFFmpegVideoAdapter,
    VideoRenderConfig,
)
from src.production_job import ProductionJob


class LocalVideoAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"synthetic-source")
        self.output = self.root / "out"
        self.config = VideoRenderConfig(
            input_path=str(self.source), output_root=str(self.output),
            width=640, height=360, fps=24, timeout_seconds=20,
        )
        self.job = ProductionJob.create("video", "Render approved source video")
        self.running = ProductionJob(
            job_id=self.job.job_id, asset_type="video", prompt=self.job.prompt,
            status="running", attempt=1,
        )

    def test_config_rejects_cpu_fallback_and_odd_dimensions(self):
        with self.assertRaisesRegex(ValueError, "CPU fallback"):
            VideoRenderConfig(str(self.source), str(self.output), video_codec="libx264")
        with self.assertRaisesRegex(ValueError, "even integers"):
            VideoRenderConfig(str(self.source), str(self.output), width=641)

    def test_rejects_non_video_or_non_running_jobs(self):
        adapter = LocalFFmpegVideoAdapter(self.config)
        image_job = ProductionJob.create("image", "image")
        self.assertFalse(adapter.execute(image_job).success)
        queued = ProductionJob.create("video", "queued")
        self.assertFalse(adapter.execute(queued).success)

    @patch("src.local_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_refuses_when_nvenc_is_not_available(self, _which):
        calls = []
        def runner(command, **kwargs):
            calls.append(command)
            if command[0] == "nvidia-smi":
                return SimpleNamespace(returncode=0, stdout="GPU, 1.0", stderr="")
            return SimpleNamespace(returncode=0, stdout=" V..... libx264", stderr="")
        adapter = LocalFFmpegVideoAdapter(self.config, runner=runner)
        result = adapter.execute(self.running)
        self.assertFalse(result.success)
        self.assertIn("h264_nvenc", result.error_message)
        self.assertFalse(any(command[0] == "ffprobe" for command in calls))

    @patch("src.local_video_adapter.shutil.which", return_value="/usr/bin/tool")
    def test_success_writes_manifest_and_returns_output(self, _which):
        def runner(command, **kwargs):
            if command[0] == "nvidia-smi":
                return SimpleNamespace(returncode=0, stdout="NVIDIA Test GPU, 555.1", stderr="")
            if command[:3] == ["ffmpeg", "-hide_banner", "-encoders"]:
                return SimpleNamespace(returncode=0, stdout=" V..... h264_nvenc NVIDIA NVENC", stderr="")
            if command[0] == "ffmpeg":
                Path(command[-1]).write_bytes(b"fake-mp4")
                return SimpleNamespace(returncode=0, stdout="progress=end", stderr="")
            if command[0] == "ffprobe":
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "format": {"duration": "2.5", "format_name": "mov,mp4"},
                    "streams": [{"codec_type": "video", "codec_name": "h264",
                                 "width": 640, "height": 360}],
                }), stderr="")
            raise AssertionError(command)
        adapter = LocalFFmpegVideoAdapter(self.config, runner=runner)
        result = adapter.execute(self.running)
        self.assertTrue(result.success, result.error_message)
        output = Path(result.output_path)
        self.assertTrue(output.is_file())
        manifest = next(self.output.glob("*.execution.json"))
        data = json.loads(manifest.read_text())
        self.assertEqual(data["compute"]["requested"], "nvidia-nvenc")
        self.assertEqual(data["output"]["duration_seconds"], 2.5)
        self.assertIn("h264_nvenc", data["render_config"]["video_codec"])
        self.assertIn("-progress", data["render_config"].get("unused", "") if False else
                      ["-progress", "pipe:1"][-2])

    @patch("src.local_video_adapter.shutil.which", return_value=None)
    def test_missing_ffmpeg_fails_closed(self, _which):
        adapter = LocalFFmpegVideoAdapter(self.config)
        result = adapter.execute(self.running)
        self.assertFalse(result.success)
        self.assertIn("ffmpeg", result.error_message)


if __name__ == "__main__":
    unittest.main()
