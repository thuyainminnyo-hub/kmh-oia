import io
import json
import os
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request
from unittest.mock import patch

from scripts.comfyui_local_preflight import (
    _RejectRedirectHandler,
    _normalize_local_base_url,
    validate_local_config,
)


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return self.body[:limit]


class ComfyUILocalPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workflow = Path(self.temp.name) / "workflow.json"
        self.workflow.write_text(
            json.dumps(
                {
                    "6": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {"text": "synthetic"},
                    },
                    "9": {
                        "class_type": "SaveImage",
                        "inputs": {"images": ["6", 0]},
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_rejects_nonlocal_urls_without_network(self):
        invalid_urls = (
            "https://example.com",
            "http://example.com:8188",
            "http://localhost:8188",
            "http://192.168.1.10:8188",
            "http://0.0.0.0:8188",
            "http://[::]:8188",
            "http://user:pass@127.0.0.1:8188",
            "http://@127.0.0.1:8188",
            "http://127.0.0.1:8188/?token=x",
            "http://127.0.0.1:8188/#fragment",
            "http://127.0.0.1:8188?",
            "http://127.0.0.1:8188#",
            "http://127.0.0.1:8188/api",
            "http://127.0.0.1:notaport",
            "http://127.0.0.1:70000",
            "http://127.0.0.1:",
            "http://[::1]:",
            "http://[fe80::1%25lo0]:8188",
            "file:///tmp/comfyui",
            "",
        )
        for base_url in invalid_urls:
            with self.subTest(base_url=base_url):
                errors = validate_local_config(base_url, self.workflow, "6")
                self.assertTrue(errors)
                self.assertIn("base_url", errors[0])

    def test_accepts_literal_ipv4_and_ipv6_loopback_urls(self):
        self.assertEqual(
            _normalize_local_base_url("http://127.0.0.1:8188"),
            ("http://127.0.0.1:8188", None),
        )
        self.assertEqual(
            _normalize_local_base_url("http://[::1]:8188/"),
            ("http://[::1]:8188", None),
        )

    def test_rejects_non_string_base_url(self):
        for base_url in (None, 123, object()):
            with self.subTest(base_url=base_url):
                normalized, error = _normalize_local_base_url(base_url)
                self.assertIsNone(normalized)
                self.assertIn("base_url", error)

    def test_rejects_missing_prompt_input_without_network(self):
        errors = validate_local_config(
            "http://127.0.0.1:8188", self.workflow, "6", "missing"
        )
        self.assertTrue(any("prompt input key" in error for error in errors))

    def test_rejects_invalid_timeout_without_network(self):
        for timeout in (0, -1, float("nan"), float("inf"), True, "3"):
            with self.subTest(timeout=timeout):
                errors = validate_local_config(
                    "http://127.0.0.1:8188",
                    self.workflow,
                    "6",
                    timeout_seconds=timeout,
                )
                self.assertIn(
                    "timeout_seconds must be a positive finite number", errors
                )

    @patch("scripts.comfyui_local_preflight.build_opener")
    def test_passes_when_node_classes_are_registered(self, mock_build_opener):
        mock_build_opener.return_value.open.return_value = FakeResponse(
            json.dumps({"CLIPTextEncode": {}, "SaveImage": {}}).encode()
        )

        self.assertEqual(
            validate_local_config(
                "http://127.0.0.1:8188/", self.workflow, "6"
            ),
            [],
        )
        request = mock_build_opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8188/object_info")
        self.assertEqual(request.get_method(), "GET")

    @patch("scripts.comfyui_local_preflight.build_opener")
    def test_fails_for_unregistered_node_class(self, mock_build_opener):
        mock_build_opener.return_value.open.return_value = FakeResponse(
            json.dumps({"CLIPTextEncode": {}}).encode()
        )

        errors = validate_local_config(
            "http://127.0.0.1:8188", self.workflow, "6"
        )
        self.assertTrue(
            any("unregistered class 'SaveImage'" in error for error in errors)
        )

    @patch.dict(
        os.environ,
        {
            "HTTP_PROXY": "http://proxy.invalid:8123",
            "http_proxy": "http://proxy.invalid:8123",
            "HTTPS_PROXY": "http://proxy.invalid:8123",
            "https_proxy": "http://proxy.invalid:8123",
            "ALL_PROXY": "http://proxy.invalid:8123",
            "all_proxy": "http://proxy.invalid:8123",
        },
        clear=False,
    )
    @patch("scripts.comfyui_local_preflight.build_opener")
    def test_disables_environment_proxies(self, mock_build_opener):
        mock_build_opener.return_value.open.return_value = FakeResponse(
            json.dumps({"CLIPTextEncode": {}, "SaveImage": {}}).encode()
        )

        errors = validate_local_config(
            "http://127.0.0.1:8188", self.workflow, "6"
        )

        self.assertEqual(errors, [])
        handlers = mock_build_opener.call_args.args
        self.assertEqual(len(handlers), 2)
        self.assertIsInstance(handlers[0], ProxyHandler)
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsInstance(handlers[1], _RejectRedirectHandler)

    def test_redirect_handler_rejects_redirects(self):
        handler = _RejectRedirectHandler()
        request = Request("http://127.0.0.1:8188/object_info")

        self.assertIsNone(
            handler.redirect_request(
                request,
                io.BytesIO(b""),
                302,
                "Found",
                Message(),
                "http://127.0.0.1:8188/redirected",
            )
        )

    @patch("scripts.comfyui_local_preflight.build_opener")
    def test_http_redirect_is_reported_and_never_followed(self, mock_build_opener):
        response_headers = Message()
        response_headers["Location"] = "http://127.0.0.1:8188/redirected"
        mock_build_opener.return_value.open.side_effect = HTTPError(
            "http://127.0.0.1:8188/object_info",
            302,
            "Found",
            response_headers,
            io.BytesIO(b""),
        )

        errors = validate_local_config(
            "http://127.0.0.1:8188", self.workflow, "6"
        )

        self.assertTrue(any("HTTPError" in error for error in errors))
        self.assertEqual(mock_build_opener.return_value.open.call_count, 1)
        self.assertIsInstance(mock_build_opener.call_args.args[1], _RejectRedirectHandler)


if __name__ == "__main__":
    unittest.main()
