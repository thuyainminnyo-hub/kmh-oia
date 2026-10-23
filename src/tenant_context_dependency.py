"""Fail-closed FastAPI dependency for verified tenant membership.

Not wired into payment routes until tenant-scoped persistence and migration gates
are reviewed. X-Tenant-ID is only a selector, never proof of authority.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from pydantic import ValidationError

from src.eduautomate_payment_api import require_api_identity
from src.registry_client import (
    RegistryClient, RegistryDenied, RegistryUnavailable, TenantContext,
    VerifiedTenantAuthority,
)


def get_registry_client() -> RegistryClient:
    """Dependency factory; missing configuration fails closed in RegistryClient."""
    return RegistryClient()


def get_verified_tenant(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    claims: dict[str, object] = Depends(require_api_identity),
    registry_client: RegistryClient = Depends(get_registry_client),
) -> VerifiedTenantAuthority:
    """Verify signed identity, match tenant claim, then verify Registry membership.

    The trusted identity assertion must contain a canonical user_id claim. Do not
    infer user_id from sub or accept a caller-supplied user identity.
    """
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TENANT_CONTEXT_MISSING")

    claimed_tenant = claims.get("tenant_id")
    if not isinstance(claimed_tenant, str) or claimed_tenant != x_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TENANT_CONTEXT_MISMATCH")

    user_id = claims.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTHENTICATED_USER_ID_MISSING")

    try:
        context = TenantContext(tenant_id=x_tenant_id, user_id=user_id)
    except ValidationError as exc:
        invalid_fields = {str(item.get("loc", [""])[0]) for item in exc.errors()}
        if "tenant_id" in invalid_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_TENANT_ID_FORMAT") from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_AUTHENTICATED_USER_ID") from exc

    try:
        return registry_client.verify_membership(context)
    except RegistryDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TENANT_MEMBERSHIP_DENIED") from exc
    except RegistryUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="REGISTRY_UNAVAILABLE") from exc
