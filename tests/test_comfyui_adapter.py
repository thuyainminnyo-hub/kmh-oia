import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

    def test_base_url_trailing_slash_is_normalized_for_api_paths(self):
        adapter = ComfyUIImageAdapter(
            base_url="http://127.0.0.1:8188/",
            workflow_path=self.workflow,
            output_root=self.root / "out",
            prompt_node_id="6",
        )
        self.assertEqual(adapter.base_url, "http://127.0.0.1:8188")
        request = adapter._build_request_for_test if hasattr(adapter, "_build_request_for_test") else None
        # The request helpers append API paths only after base_url normalization.
        self.assertFalse(adapter.base_url.endswith("//"))
        self.assertEqual(adapter.base_url + "/prompt", "http://127.0.0.1:8188/prompt")

    def test_requires_local_http_base_url(self):
        with self.assertRaisesRegex(ValueError, "base_url"):
            ComfyUIImageAdapter(
                base_url="https://example.com", workflow_path=self.workflow,
                output_root=self.root / "out", prompt_node_id="6",
            )

    def test_rejects_non_loopback_and_hostname_targets(self):
        for base_url in (
            "http://example.com:8188",
            "http://localhost:8188",
            "http://192.168.1.10:8188",
            "https://127.0.0.1:8188",
        ):
            with self.subTest(base_url=base_url):
                with self.assertRaises(ValueError):
                    ComfyUIImageAdapter(
                        base_url=base_url, workflow_path=self.workflow,
                        output_root=self.root / "out", prompt_node_id="6",
                    )

    def test_rejects_credentials_query_fragment_path_and_malformed_port(self):
        for base_url in (
            "http://user:pass@127.0.0.1:8188",
            "http://127.0.0.1:8188/?token=x",
            "http://127.0.0.1:8188/#fragment",
            "http://127.0.0.1:8188/api",
            "http://127.0.0.1:notaport",
            "http://127.0.0.1:70000",
        ):
            with self.subTest(base_url=base_url):
                with self.assertRaises(ValueError):
                    ComfyUIImageAdapter(
                        base_url=base_url, workflow_path=self.workflow,
                        output_root=self.root / "out", prompt_node_id="6",
                    )

    def test_missing_prompt_node_fails_closed(self):
        adapter = ComfyUIImageAdapter(
            base_url="http://127.0.0.1:8188", workflow_path=self.workflow,
            output_root=self.root / "out", prompt_node_id="missing",
        )
        result = adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("prompt node", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_submits_polls_downloads_and_saves_output(self, mock_build_opener):
        image_bytes = b"\x89PNG\r\n\x1a\nsynthetic payload"
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
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
        self.assertEqual(result.provider_execution_id, "prompt-1")
        submitted = json.loads(mock_build_opener.return_value.open.call_args_list[0].args[0].data.decode())
        self.assertEqual(submitted["prompt"]["6"]["inputs"]["text"], self.job.prompt)

    @patch("src.comfyui_adapter.time.sleep")
    @patch("src.comfyui_adapter.build_opener")
    def test_waits_for_success_status_before_downloading(self, mock_build_opener, _mock_sleep):
        running = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "running"}}}
        success = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(running).encode()),
            FakeResponse(json.dumps(success).encode()),
            FakeResponse(b"\x89PNG\r\n\x1a\nsynthetic payload"),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertTrue(result.success, result.error_message)
        self.assertEqual(Path(result.output_path).read_bytes(), b"\x89PNG\r\n\x1a\nsynthetic payload")
        self.assertEqual(result.provider_execution_id, "prompt-1")

    @patch("src.comfyui_adapter.build_opener")
    def test_queue_response_without_prompt_id_fails(self, mock_build_opener):
        mock_build_opener.return_value.open.return_value = FakeResponse(b"{}")
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("prompt_id", result.error_message)

    @patch("src.comfyui_adapter.time.monotonic", side_effect=[0.0, 0.0, 0.0, 2.0])
    @patch("src.comfyui_adapter.time.sleep")
    @patch("src.comfyui_adapter.build_opener")
    def test_missing_history_output_fails(self, mock_build_opener, _mock_sleep, _mock_monotonic):
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(b'{"prompt-1":{"outputs":{},"status":{"status_str":"success"}}}'),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("no output image metadata", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_history_without_image_metadata_fails(self, mock_build_opener):
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(b'{"prompt-1":{"outputs":{"9":{"images":[]}},"status":{"status_str":"success"}}}'),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("no output image metadata", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_empty_image_fails(self, mock_build_opener):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(b""),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("empty image", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_rejects_bytes_that_do_not_match_image_extension(self, mock_build_opener):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
            FakeResponse(b"not a png file"),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("do not match", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_rejects_unsupported_extension(self, mock_build_opener):
        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.exe", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertIn("extension", result.error_message)

    def test_output_metadata_accepts_safe_nested_subfolder(self):
        ComfyUIImageAdapter._validate_image_metadata("generated.png", "batch_1/session-2", "output")

    def test_output_metadata_rejects_filename_path_components(self):
        for filename in ("../generated.png", "folder/generated.png", r"..\\generated.png", "bad\x00.png"):
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(RuntimeError, "filename"):
                    ComfyUIImageAdapter._validate_image_metadata(filename, "", "output")

    def test_output_metadata_rejects_unsafe_subfolders(self):
        for subfolder in ("../outside", "/absolute", r"..\\outside", "batch//empty", "C:/outside", "bad\x7fdir"):
            with self.subTest(subfolder=subfolder):
                with self.assertRaisesRegex(RuntimeError, "subfolder"):
                    ComfyUIImageAdapter._validate_image_metadata("generated.png", subfolder, "output")

    def test_output_metadata_rejects_unsupported_type(self):
        with self.assertRaisesRegex(RuntimeError, "image type"):
            ComfyUIImageAdapter._validate_image_metadata("generated.png", "", "remote")

    @patch("src.comfyui_adapter.build_opener")
    def test_json_redirect_is_rejected_without_following_target(self, mock_build_opener):
        from urllib.error import HTTPError

        mock_build_opener.return_value.open.side_effect = HTTPError(
            "http://127.0.0.1:8188/prompt", 302, "Found",
            {"Location": "http://example.invalid/steal"}, None,
        )
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertEqual(mock_build_opener.return_value.open.call_count, 1)
        self.assertIn("302", result.error_message)

    @patch("src.comfyui_adapter.build_opener")
    def test_image_redirect_is_rejected_without_following_target(self, mock_build_opener):
        from urllib.error import HTTPError

        history = {"prompt-1": {"outputs": {"9": {"images": [
            {"filename": "generated.png", "subfolder": "", "type": "output"}
        ]}}, "status": {"status_str": "success"}}}
        mock_build_opener.return_value.open.side_effect = [
            FakeResponse(b'{"prompt_id":"prompt-1"}'),
            FakeResponse(json.dumps(history).encode()),
            HTTPError(
                "http://127.0.0.1:8188/view?filename=generated.png", 302, "Found",
                {"Location": "http://example.invalid/image.png"}, None,
            ),
        ]
        result = self.adapter.execute(self.running_job)
        self.assertFalse(result.success)
        self.assertEqual(mock_build_opener.return_value.open.call_count, 3)
        self.assertIn("302", result.error_message)


    def test_real_local_http_redirects_are_not_followed(self):
        requested_paths = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                requested_paths.append(self.path)
                if self.path in ("/redirect-json", "/redirect-image"):
                    self.send_response(302)
                    self.send_header("Location", "/redirect-target")
                    self.end_headers()
                elif self.path == "/redirect-target":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"unexpected": true}')
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(thread.join, 2)
        self.adapter.base_url = f"http://127.0.0.1:{server.server_port}"

        from urllib.error import HTTPError
        with self.assertRaises(HTTPError) as json_error:
            self.adapter._request_json("GET", "/redirect-json")
        self.assertEqual(json_error.exception.code, 302)
        self.assertEqual(requested_paths, ["/redirect-json"])

        with self.assertRaises(HTTPError) as image_error:
            self.adapter._request_bytes("/redirect-image")
        self.assertEqual(image_error.exception.code, 302)
        self.assertEqual(requested_paths, ["/redirect-json", "/redirect-image"])

    @patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9",
                              "HTTPS_PROXY": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9",
                              "ALL_PROXY": "http://127.0.0.1:9", "all_proxy": "http://127.0.0.1:9"})
    @patch("src.comfyui_adapter.build_opener", wraps=__import__("urllib.request", fromlist=["build_opener"]).build_opener)
    def test_json_and_image_requests_disable_environment_proxy(self, mock_build_opener):
        # Use a reachable local server while proxy environment variables point at a dead endpoint.
        requested_paths = []

        class LocalHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                requested_paths.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(thread.join, 2)
        self.adapter.base_url = f"http://127.0.0.1:{server.server_port}"

        self.assertEqual(self.adapter._request_json("GET", "/json"), {"ok": True})
        self.assertEqual(self.adapter._request_bytes("/image"), b'{"ok": true}')
        self.assertEqual(requested_paths, ["/json", "/image"])

        # Both request paths explicitly supply an empty proxy map to build_opener.
        self.assertEqual(mock_build_opener.call_count, 2)
        for call in mock_build_opener.call_args_list:
            self.assertEqual(type(call.args[0]).__name__, "ProxyHandler")
            self.assertEqual(call.args[0].proxies, {})

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
