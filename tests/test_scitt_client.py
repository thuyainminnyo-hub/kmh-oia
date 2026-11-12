import unittest

from src.scitt_client import (
    HttpResponse,
    ScrapiClient,
    ScrapiError,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, headers, body=None):
        self.calls.append((method, url, dict(headers), body))
        return self.responses.pop(0)


class ScrapiClientTests(unittest.TestCase):
    def test_discover_keys_uses_well_known_endpoint_and_cbor(self):
        transport = FakeTransport([
            HttpResponse(200, {"Content-Type": "application/cbor"}, b"keys")
        ])
        client = ScrapiClient("https://ts.example", transport)
        self.assertEqual(client.discover_keys(), b"keys")
        self.assertEqual(transport.calls[0][1], "https://ts.example/.well-known/scitt-keys")
        self.assertEqual(transport.calls[0][2]["Accept"], "application/cbor")

    def test_register_immediate_receipt(self):
        transport = FakeTransport([
            HttpResponse(
                201,
                {"Content-Type": "application/cose", "Location": "/entries/abc"},
                b"receipt",
            )
        ])
        result = ScrapiClient("https://ts.example", transport).register_signed_statement(b"signed")
        self.assertEqual(result.status, "registered")
        self.assertEqual(result.receipt, b"receipt")
        self.assertEqual(result.receipt_url, "https://ts.example/entries/abc")

    def test_register_async_then_resolve_pending_and_ready(self):
        transport = FakeTransport([
            HttpResponse(202, {"Location": "/entries/abc", "Retry-After": "3"}, b""),
            HttpResponse(204, {}, b""),
            HttpResponse(200, {"Content-Type": "application/cose"}, b"receipt"),
        ])
        client = ScrapiClient("https://ts.example", transport)
        pending = client.register_signed_statement(b"signed")
        self.assertEqual(pending.status, "pending")
        self.assertEqual(client.resolve_receipt(pending.receipt_url).status, "pending")
        ready = client.resolve_receipt(pending.receipt_url)
        self.assertEqual(ready.status, "ready")
        self.assertEqual(ready.receipt, b"receipt")

    def test_receipt_not_found_is_explicit(self):
        transport = FakeTransport([HttpResponse(404, {}, b"")])
        result = ScrapiClient("https://ts.example", transport).resolve_receipt(
            "https://ts.example/entries/missing"
        )
        self.assertEqual(result.status, "not_found")

    def test_rejects_cross_origin_location_and_downgrade(self):
        transport = FakeTransport([
            HttpResponse(202, {"Location": "https://attacker.example/steal"}, b"")
        ])
        with self.assertRaises(ScrapiError):
            ScrapiClient("https://ts.example", transport).register_signed_statement(b"signed")
        with self.assertRaises(ScrapiError):
            ScrapiClient("https://ts.example", FakeTransport([])).resolve_receipt(
                "http://ts.example/entries/abc"
            )

    def test_rejects_bad_media_types_and_empty_signed_statement(self):
        client = ScrapiClient(
            "https://ts.example",
            FakeTransport([HttpResponse(200, {"Content-Type": "application/json"}, b"{}")]),
        )
        with self.assertRaises(ScrapiError):
            client.discover_keys()
        with self.assertRaises(ValueError):
            ScrapiClient("https://ts.example", FakeTransport([])).register_signed_statement(b"")

    def test_rejects_202_with_receipt_body(self):
        client = ScrapiClient(
            "https://ts.example",
            FakeTransport([HttpResponse(202, {"Location": "/entries/a"}, b"not-empty")]),
        )
        with self.assertRaises(ScrapiError):
            client.register_signed_statement(b"signed")


if __name__ == "__main__":
    unittest.main()
