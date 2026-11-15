"""Minimal SCRAPI v11 client boundary for KMH OIA.

Transport and COSE/CBOR codecs are injected. This module does not perform
network I/O itself, sign statements, decode CBOR, or verify COSE receipts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol
from urllib.parse import urljoin, urlsplit


class HttpTransport(Protocol):
    def request(
        self, method: str, url: str, *,
        headers: Mapping[str, str], body: bytes | None = None,
    ) -> "HttpResponse": ...


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


@dataclass(frozen=True)
class RegistrationResult:
    status: str  # "registered" or "pending"
    receipt: bytes | None
    receipt_url: str


@dataclass(frozen=True)
class ReceiptResolution:
    status: str  # "ready", "pending", or "not_found"
    receipt: bytes | None
    receipt_url: str


class ScrapiError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.lower()
    return next((v for k, v in headers.items() if k.lower() == wanted), None)


def _media_type(headers: Mapping[str, str]) -> str:
    value = _header(headers, "Content-Type") or ""
    return value.split(";", 1)[0].strip().lower()


class ScrapiClient:
    """Small explicit SCRAPI client; no implicit retries or polling."""

    def __init__(self, service_origin: str, transport: HttpTransport):
        parsed = urlsplit(service_origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("service_origin must be an https origin without credentials")
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("service_origin must not contain path, query, or fragment")
        self.origin = f"https://{parsed.netloc}"
        self.transport = transport

    def _same_origin_location(self, location: str | None) -> str:
        if not location:
            raise ScrapiError(502, "SCRAPI response omitted required Location header")
        resolved = urljoin(self.origin + "/", location)
        parsed = urlsplit(resolved)
        if parsed.scheme != "https" or parsed.netloc.lower() != urlsplit(self.origin).netloc.lower():
            raise ScrapiError(502, "SCRAPI Location must remain on the configured HTTPS origin")
        if parsed.username or parsed.password or parsed.fragment:
            raise ScrapiError(502, "SCRAPI Location contains disallowed URL components")
        return resolved

    def discover_keys(self) -> bytes:
        response = self.transport.request(
            "GET", self.origin + "/.well-known/scitt-keys",
            headers={"Accept": "application/cbor"},
        )
        if response.status != 200:
            raise ScrapiError(response.status, "Transparency Service key discovery failed")
        if _media_type(response.headers) != "application/cbor":
            raise ScrapiError(response.status, "key discovery response must be application/cbor")
        return response.body

    def register_signed_statement(self, signed_statement: bytes) -> RegistrationResult:
        if not isinstance(signed_statement, bytes) or not signed_statement:
            raise ValueError("signed_statement must be non-empty COSE bytes")
        response = self.transport.request(
            "POST", self.origin + "/entries",
            headers={
                "Accept": "application/cbor, application/cose",
                "Content-Type": "application/cose",
            },
            body=signed_statement,
        )
        if response.status not in (201, 202):
            raise ScrapiError(response.status, "Signed Statement registration failed")
        receipt_url = self._same_origin_location(_header(response.headers, "Location"))
        if response.status == 201:
            if _media_type(response.headers) != "application/cose":
                raise ScrapiError(response.status, "immediate receipt must be application/cose")
            if not response.body:
                raise ScrapiError(response.status, "registration returned an empty receipt")
            return RegistrationResult("registered", response.body, receipt_url)
        if response.body:
            raise ScrapiError(response.status, "202 registration response must not carry a receipt")
        return RegistrationResult("pending", None, receipt_url)

    def resolve_receipt(self, receipt_url: str) -> ReceiptResolution:
        safe_url = self._same_origin_location(receipt_url)
        response = self.transport.request(
            "GET", safe_url,
            headers={"Accept": "application/cose"},
        )
        if response.status == 200:
            if _media_type(response.headers) != "application/cose" or not response.body:
                raise ScrapiError(502, "receipt resolution returned invalid COSE content")
            return ReceiptResolution("ready", response.body, safe_url)
        if response.status == 204:
            if response.body:
                raise ScrapiError(502, "204 pending response must not contain a body")
            return ReceiptResolution("pending", None, safe_url)
        if response.status == 404:
            return ReceiptResolution("not_found", None, safe_url)
        raise ScrapiError(response.status, "Receipt resolution failed")
