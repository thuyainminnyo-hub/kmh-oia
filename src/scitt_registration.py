"""Minimal SCRAPI registration/receipt-resolution adapter.

The caller supplies already-encoded COSE Signed Statements and an HTTP transport.
This module does not create COSE signatures, verify receipts, or contact a service
unless an application supplies a real transport.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


class HttpTransport(Protocol):
    def request(
        self, method: str, url: str, *,
        headers: Mapping[str, str], body: bytes = b"",
    ) -> HttpResponse: ...


@dataclass(frozen=True)
class RegistrationResult:
    state: str  # "registered" or "pending"
    receipt: bytes | None
    receipt_url: str
    retry_after: str | None = None


class ScittProtocolError(ValueError):
    pass


def _header(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return None


class ScittRegistrationClient:
    """SCRAPI /entries and /.well-known/scitt-keys protocol adapter."""

    def __init__(self, *, base_url: str, transport: HttpTransport) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("SCITT base_url must be an absolute HTTPS URL")
        self.base_url = base_url.rstrip("/") + "/"
        self._origin = (parsed.scheme, parsed.netloc.lower())
        self.transport = transport

    def _same_origin_location(self, location: str | None) -> str:
        if not location:
            raise ScittProtocolError("SCRAPI response is missing Location")
        resolved = urljoin(self.base_url, location)
        parsed = urlparse(resolved)
        if (parsed.scheme, parsed.netloc.lower()) != self._origin:
            raise ScittProtocolError("cross-origin receipt Location is not permitted")
        if parsed.username or parsed.password or parsed.fragment:
            raise ScittProtocolError("invalid receipt Location")
        return resolved

    def register(self, signed_statement: bytes) -> RegistrationResult:
        if not isinstance(signed_statement, bytes) or not signed_statement:
            raise ValueError("signed_statement must be non-empty COSE bytes")
        response = self.transport.request(
            "POST", urljoin(self.base_url, "entries"),
            headers={
                "Accept": "application/cose, application/cbor",
                "Content-Type": "application/cose",
            },
            body=signed_statement,
        )
        location = self._same_origin_location(_header(response.headers, "Location"))
        if response.status == 201:
            if not response.body:
                raise ScittProtocolError("201 registration response has no COSE receipt")
            return RegistrationResult(
                state="registered", receipt=response.body, receipt_url=location,
            )
        if response.status == 202:
            return RegistrationResult(
                state="pending", receipt=None, receipt_url=location,
                retry_after=_header(response.headers, "Retry-After"),
            )
        raise ScittProtocolError(f"unexpected SCRAPI registration status: {response.status}")

    def resolve_receipt(self, receipt_url: str) -> RegistrationResult:
        safe_url = self._same_origin_location(receipt_url)
        response = self.transport.request(
            "GET", safe_url,
            headers={"Accept": "application/cose"},
        )
        if response.status == 200:
            if not response.body:
                raise ScittProtocolError("200 receipt response has an empty body")
            return RegistrationResult(
                state="registered", receipt=response.body, receipt_url=safe_url,
            )
        if response.status == 204:
            return RegistrationResult(
                state="pending", receipt=None, receipt_url=safe_url,
                retry_after=_header(response.headers, "Retry-After"),
            )
        if response.status == 404:
            raise ScittProtocolError("SCITT receipt not found or registration failed")
        raise ScittProtocolError(f"unexpected SCRAPI receipt status: {response.status}")

    def discover_keys(self) -> bytes:
        response = self.transport.request(
            "GET", urljoin(self.base_url, ".well-known/scitt-keys"),
            headers={"Accept": "application/cbor"},
        )
        if response.status != 200 or not response.body:
            raise ScittProtocolError("SCITT Transparency Service key discovery failed")
        return response.body
