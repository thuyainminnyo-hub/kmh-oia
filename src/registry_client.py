"""Fail-closed adapter for the authoritative Master System tenant membership API.

This module is not wired into payment reads/writes yet. Integration remains
blocked until tenant persistence, tenant-scoped idempotency, and route-level
cross-tenant regression tests are reviewed.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

REGISTRY_VERIFY_PATH = "/api/v1/registry/tenants/verify"
_TENANT_ID = re.compile(r"^tn_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_USER_ID = re.compile(r"^usr_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class TenantContext(BaseModel):
    """Untrusted caller context; syntactic validation is not authorization."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    tenant_id: str = Field(min_length=1, max_length=39)
    user_id: str = Field(min_length=1, max_length=40)

    @field_validator("tenant_id")
    @classmethod
    def canonical_tenant_uuid4(cls, value: str) -> str:
        if not _TENANT_ID.fullmatch(value):
            raise ValueError("INVALID_TENANT_ID_FORMAT")
        return value

    @field_validator("user_id")
    @classmethod
    def canonical_user_uuid_shape(cls, value: str) -> str:
        if not _USER_ID.fullmatch(value):
            raise ValueError("INVALID_USER_ID_FORMAT")
        return value


class RegistryMembership(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    role: str = Field(min_length=1, max_length=64)
    status: str
    verified_at: datetime

    @field_validator("verified_at")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("verified_at must include a timezone")
        return value


class RegistryVerifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str
    status: str
    membership: RegistryMembership


@dataclass(frozen=True)
class VerifiedTenantAuthority:
    tenant_id: str
    user_id: str
    role: str
    verified_at: datetime


class RegistryDenied(Exception):
    """Registry explicitly denied the tenant/member request."""


class RegistryUnavailable(Exception):
    """Registry could not safely establish authority; callers must fail closed."""


class RegistryClient:
    def __init__(self, *, base_url: str | None = None, service_token: str | None = None,
                 timeout_seconds: float = 2.0, transport: httpx.BaseTransport | None = None) -> None:
        self.base_url = (base_url if base_url is not None else os.getenv("MASTER_REGISTRY_BASE_URL", "")).strip().rstrip("/")
        self.service_token = (service_token if service_token is not None else os.getenv("MASTER_REGISTRY_SERVICE_TOKEN", "")).strip()
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def verify_membership(self, context: TenantContext) -> VerifiedTenantAuthority:
        # Validate configuration before making any request; never fall back to allow.
        if not self.base_url or not self.service_token or self.timeout_seconds <= 0:
            raise RegistryUnavailable("Registry client configuration is missing or invalid")
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(
                    self.base_url + REGISTRY_VERIFY_PATH,
                    headers={"Authorization": "Bearer " + self.service_token, "Content-Type": "application/json"},
                    json={"tenant_id": context.tenant_id, "user_id": context.user_id},
                )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise RegistryUnavailable("Registry request failed; access denied") from exc

        if response.status_code in (403, 404):
            raise RegistryDenied(f"Registry explicitly denied authority (HTTP {response.status_code})")
        if response.status_code != 200:
            raise RegistryUnavailable(f"Registry did not verify authority (HTTP {response.status_code})")
        try:
            body: Any = response.json()
            verified = RegistryVerifyResponse.model_validate(body)
        except (ValueError, ValidationError) as exc:
            raise RegistryUnavailable("Registry response was invalid; access denied") from exc
        if (verified.tenant_id != context.tenant_id or verified.status != "ACTIVE"
                or verified.membership.user_id != context.user_id or verified.membership.status != "ACTIVE"):
            raise RegistryDenied("Registry response does not establish active matching membership")
        return VerifiedTenantAuthority(tenant_id=verified.tenant_id, user_id=verified.membership.user_id,
                                       role=verified.membership.role, verified_at=verified.membership.verified_at)
