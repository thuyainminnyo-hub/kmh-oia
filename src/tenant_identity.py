"""Pure validation helpers for KMH OIA canonical tenant identifiers.

This module validates identifier syntax only. It does not establish that a tenant
exists, that a caller belongs to it, or that a Registry membership is active.
Those checks must be performed by the authoritative Registry integration.
"""
from __future__ import annotations

import uuid


def is_canonical_tenant_id(value: object) -> bool:
    """Return True only for the tn_ prefix plus lowercase canonical UUIDv4.

    Validation is intentionally strict: uppercase UUIDs, non-canonical spellings,
    non-v4 UUIDs, and non-RFC-4122 UUID variants are rejected.
    """
    if not isinstance(value, str) or not value.startswith("tn_"):
        return False

    raw_uuid = value[3:]
    try:
        parsed = uuid.UUID(raw_uuid)
    except (ValueError, AttributeError, TypeError):
        return False

    return (
        str(parsed) == raw_uuid
        and parsed.version == 4
        and parsed.variant == uuid.RFC_4122
    )
