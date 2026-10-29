import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.comfyui_adapter import ComfyUIImageAdapter
from src.production_execution import AdapterResult
from src.production_job import ProductionJob


class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit=-1):
        return self.body[:limit]


class ComfyUIImageAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workflow = self.root / "workflow.json"
        self.workflow.write_text(json.dumps({
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "old prompt"}}
        }), encoding="utf-8")
        self.job = ProductionJob.create("image", "a test image")
        self.running_job = ProductionJob(
            job_id=self.job.job_id, asset_type="image", prompt=self.job.prompt,
            status="running", attempt=1,
        )
        self.adapter = ComfyUIImageAdapter(
            base_url="http://127.0.0.1:8188",
            workflow_path=self.workflow,
            output_root=self.root / "out",
            prompt_node_id="6",
            request_timeout_seconds=1,
            job_timeout_seconds=1,
            poll_interval_seconds=0.001,
        )

    def test_requires_local_http_base_url(self):
        with self.assertRaisesRegex(ValueError, "local HTTP"):
            ComfyUIImageAdapter(
                base_url="https://example.com", workflow_path=self.workflow,
                output_root=self.root / "out", prompt_node_id="6",
            )

    def test_missing_prompt_node_fails_closed(self):
        adapter = ComfyUIImageAdapter(
            base_url="http://localhost:8188", workflow_path=self.workflow,
            output_root=self.root / "out", prompt_node_id="missing",
        )
        result = adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("prompt node", result.error_message)

    @patch("src.comfyui_adapter.urlopen")
    def test_submits_polls_downloads_and_saves_output(self, mock_urlopen):
        image_bytes = b"\x89PNG\r\n\x1a\nsynthetic payload"
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_urlopen.side_effect = [
            FakeResponse(json.dumps({"prompt_id": "prompt-1"}).encode()),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(image_bytes),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertIsInstance(result, AdapterResult)
        self.assertTrue(result.success, result.error_message)
        path = Path(result.output_path)
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), image_bytes)
        submitted = json.loads(mock_urlopen.call_args_list[0].args[0].data.decode())
        self.assertEqual(submitted["prompt"]["6"]["inputs"]["text"], self.job.prompt)

    @patch("src.comfyui_adapter.time.sleep")
    @patch("src.comfyui_adapter.urlopen")
    def test_waits_for_success_status_before_downloading(self, mock_urlopen, _mock_sleep):
        running = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "running"}}}
        success = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(running).encode()),
            FakeResponse(json.dumps(success).encode()),
            FakeResponse(b"\\x89PNG\\r\\n\\x1a\\nsynthetic payload"),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertTrue(result.success, result.error_message)
        self.assertEqual(Path(result.output_path).read_bytes(), b"\\x89PNG\\r\\n\\x1a\\nsynthetic payload")

    @patch("src.comfyui_adapter.urlopen")
    def test_queue_response_without_prompt_id_fails(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b"{}")
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("prompt_id", result.error_message)

    @patch("src.comfyui_adapter.time.monotonic", side_effect=[0.0, 0.0, 0.0, 2.0])
    @patch("src.comfyui_adapter.time.sleep")
    @patch("src.comfyui_adapter.urlopen")
    def test_missing_history_output_fails(self, mock_urlopen, _mock_sleep, _mock_monotonic):
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(b'{"prompt-1":{"outputs":{},"status":{"status_str":"success"}}}'),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("no output image metadata", result.error_message)

    @patch("src.comfyui_adapter.urlopen")
    def test_history_without_image_metadata_fails(self, mock_urlopen):
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(b'{"prompt-1":{"outputs":{"9":{"images":[]}},"status":{"status_str":"success"}}}'),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("no output image metadata", result.error_message)

    @patch("src.comfyui_adapter.urlopen")
    def test_empty_image_fails(self, mock_urlopen):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(b""),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("empty image", result.error_message)

    @patch("src.comfyui_adapter.urlopen")
    def test_rejects_bytes_that_do_not_match_image_extension(self, mock_urlopen):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(b"not a png file"),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("do not match", result.error_message)

    @patch("src.comfyui_adapter.urlopen")
    def test_rejects_unsupported_extension(self, mock_urlopen):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.exe", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_urlopen.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("extension", result.error_message)

    def test_rejects_video_jobs(self):
        video_job = ProductionJob.create("video", "test")
        running = ProductionJob(
            job_id=video_job.job_id, asset_type="video", prompt="test", status="running", attempt=1,
        )
        result = self.adapter.execute(running)
        self.assertFalse(result.success)
        self.assertIn("only supports image", result.error_message)


if __name__ == "__main__":
    unittest.main()
