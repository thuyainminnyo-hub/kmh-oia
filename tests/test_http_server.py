"""HTTP adapter contract tests using only local synthetic inputs."""
import json
import socket
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.http_server import MAX_BODY_BYTES, MAX_GOAL_CHARS, MAX_SESSION_ID_CHARS, OIARequestHandler


class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), OIARequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.server_address = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, method="GET", payload=None, content_type="application/json"):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", content_type)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            return error.code, json.loads(error.read())
        return response.status, json.loads(response.read())

    def request_raw(self, path, data, content_type="application/json"):
        request = Request(self.base_url + path, data=data, method="POST")
        request.add_header("Content-Type", content_type)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            return error.code, json.loads(error.read())
        return response.status, json.loads(response.read())

    def test_healthz_is_liveness(self):
        status, body = self.request("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok", "check": "liveness"})

    def test_run_executes_and_returns_trace(self):
        status, body = self.request("/run", "POST", {"goal": "hello HTTP", "session_id": "test-session"})
        self.assertEqual(status, 200)
        self.assertEqual(body["response"], "hello HTTP")
        self.assertEqual(body["stages"][0], "input_gateway")
        self.assertEqual(body["stages"][-1], "trace")
        self.assertEqual(body["events"][0]["metadata"]["session_id"], "test-session")

    def test_empty_goal_fails_closed(self):
        status, body = self.request("/run", "POST", {"goal": "  "})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "goal_must_be_non_empty_string")

    def test_invalid_json_fails_closed(self):
        status, body = self.request_raw("/run", b"{not-json")
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_json")

    def test_wrong_content_type_is_rejected(self):
        status, body = self.request("/run", "POST", {"goal": "hello"}, content_type="text/plain")
        self.assertEqual(status, 415)
        self.assertEqual(body["error"], "application_json_required")

    def test_oversized_body_is_rejected_before_reading_body(self):
        oversized = b"x" * (MAX_BODY_BYTES + 1)
        status, body = self.request_raw("/run", oversized)
        self.assertEqual(status, 413)
        self.assertEqual(body["error"], "request_too_large")

    def test_missing_content_length_is_rejected(self):
        with socket.create_connection(self.server_address, timeout=3) as connection:
            connection.sendall(
                b"POST /run HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Content-Type: application/json\r\n"
                b"Connection: close\r\n\r\n"
            )
            response = b""
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                response += chunk
        self.assertIn(b" 411 ", response.split(b"\r\n", 1)[0])
        self.assertIn(b'"content_length_required"', response)

    def test_transfer_encoding_is_rejected(self):
        with socket.create_connection(self.server_address, timeout=3) as connection:
            connection.sendall(
                b"POST /run HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 18\r\n"
                b"Transfer-Encoding: chunked\r\n"
                b"Connection: close\r\n\r\n"
            )
            response = b""
            while True:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                response += chunk
        self.assertIn(b" 400 ", response.split(b"\r\n", 1)[0])
        self.assertIn(b'"transfer_encoding_not_supported"', response)

    def test_non_object_json_is_rejected(self):
        status, body = self.request_raw("/run", b'["not", "an", "object"]')
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "json_object_required")

    def test_goal_length_is_bounded(self):
        status, body = self.request("/run", "POST", {"goal": "x" * (MAX_GOAL_CHARS + 1)})
        self.assertEqual(status, 413)
        self.assertEqual(body["error"], "goal_too_long")

    def test_session_id_length_is_bounded(self):
        status, body = self.request(
            "/run", "POST", {"goal": "hello", "session_id": "s" * (MAX_SESSION_ID_CHARS + 1)}
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "session_id_too_long")

    def test_unknown_path_is_not_found(self):
        status, body = self.request("/unknown")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
