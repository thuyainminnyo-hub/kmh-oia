"""Vercel-hosted HTTP boundary for the deterministic KMH OIA runtime.

This surface is intentionally conservative:
- health/readiness reveal configuration state, never secret values;
- runtime execution requires an API key and an explicit feature flag;
- only the deterministic, side-effect-free echo tool is exposed;
- each request uses isolated in-memory state (no durability is implied).
"""

from __future__ import annotations

import hmac
import os
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.main import run


SERVICE_VERSION = "0.1.0"
API_KEY_ENV = "KMH_OIA_API_KEY"
EXECUTION_FLAG_ENV = "KMH_OIA_EXECUTION_ENABLED"

app = FastAPI(
    title="KMH OIA Runtime API",
    version=SERVICE_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def _flag_enabled(name: str) -> bool:
    """Read a strict, explicit feature flag; unset and unknown values are false."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _api_key_configured() -> bool:
    return bool(os.getenv(API_KEY_ENV, "").strip())


def _authorize(api_key: str | None) -> None:
    expected = os.getenv(API_KEY_ENV, "")
    if not expected.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="api_auth_not_configured",
        )
    if not isinstance(api_key, str) or not hmac.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_api_key",
        )


class ExecutionRequest(BaseModel):
    """Strict request model for the first, deterministic execution slice."""

    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="vercel-preview", min_length=1, max_length=128)
    tool_name: Literal["echo"] = "echo"

    @field_validator("goal", "session_id")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Liveness probe; intentionally does not disclose deployment secrets."""
    return {"status": "ok", "service": "kmh-oia-runtime-api", "version": SERVICE_VERSION}


@app.get("/ready", tags=["operations"])
def readiness() -> dict[str, object]:
    """Report safe configuration facts, not a claim of production readiness."""
    enabled = _flag_enabled(EXECUTION_FLAG_ENV)
    configured = _api_key_configured()
    return {
        "status": "ready",
        "service": "kmh-oia-runtime-api",
        "version": SERVICE_VERSION,
        "execution_gate": "open" if enabled and configured else "closed",
        "execution_enabled": enabled,
        "api_key_configured": configured,
        "state_backend": "ephemeral-per-request",
        "external_providers_enabled": False,
        "production_release_authorized": False,
    }


@app.post("/v1/executions", status_code=status.HTTP_200_OK, tags=["execution"])
def create_execution(
    payload: ExecutionRequest,
    x_kmh_oia_api_key: str | None = Header(default=None, alias="X-KMH-OIA-API-Key"),
) -> dict[str, object]:
    """Run the restricted deterministic slice; no external tools or durable writes."""
    _authorize(x_kmh_oia_api_key)
    if not _flag_enabled(EXECUTION_FLAG_ENV):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="execution_disabled",
        )

    # The request schema permits only "echo". No shell, network, provider, or
    # production adapter is reachable through this endpoint.
    response, trace = run(
        payload.goal,
        session_id=payload.session_id,
        tool_name=payload.tool_name,
    )
    execution_id = str(uuid4())
    trace_events = [
        {
            "stage": event.stage,
            "status": event.status,
            "metadata": dict(event.metadata),
        }
        for event in trace.events
    ]
    trace_id = trace.events[0].metadata.get("trace_id", "") if trace.events else ""

    return {
        "execution_id": execution_id,
        "status": "completed",
        "mode": "deterministic_local_only",
        "response": response,
        "stages": list(trace.stages),
        "trace_id": trace_id,
        "events": trace_events,
        "durability": "not_persisted",
        "external_side_effects": False,
    }
