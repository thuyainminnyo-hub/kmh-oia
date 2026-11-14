"""Synthetic-only GOLDEN PALACE traceability adapter.

This module intentionally emits an EPCIS-shaped local representation, not a
claim of EPCIS 2.0.1 or CBV conformance. Official GS1 artefacts are a separate
pinned validation gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SyntheticReceiving:
    fixture_id: str
    event_id: str
    event_time: str
    timezone_offset: str
    product_lot_id: str
    quantity: float
    uom: str
    location_id: str
    supplier_id: str
    synthetic: bool = True


def parse_receiving_fixture(payload: dict[str, Any]) -> SyntheticReceiving:
    """Validate and parse one OIA-local synthetic receiving envelope."""
    required = (
        "fixture_id", "event_id", "event_time", "timezone_offset",
        "product_lot_id", "quantity", "uom", "location_id", "supplier_id",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError("missing required fixture fields: " + ", ".join(missing))
    if payload.get("synthetic") is not True:
        raise ValueError("only explicitly synthetic fixtures are accepted")
    if payload.get("event_type") != "receiving":
        raise ValueError("fixture event_type must be receiving")
    for key in required:
        value = payload[key]
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{key} must not be empty")
    if isinstance(payload["quantity"], bool) or not isinstance(payload["quantity"], (int, float)):
        raise ValueError("quantity must be numeric")
    if payload["quantity"] <= 0:
        raise ValueError("quantity must be greater than zero")
    try:
        datetime.fromisoformat(payload["event_time"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("event_time must be an ISO-8601 timestamp") from exc
    if not isinstance(payload["timezone_offset"], str) or len(payload["timezone_offset"]) != 6:
        raise ValueError("timezone_offset must use ±HH:MM format")
    return SyntheticReceiving(
        fixture_id=str(payload["fixture_id"]),
        event_id=str(payload["event_id"]),
        event_time=str(payload["event_time"]),
        timezone_offset=str(payload["timezone_offset"]),
        product_lot_id=str(payload["product_lot_id"]),
        quantity=float(payload["quantity"]),
        uom=str(payload["uom"]),
        location_id=str(payload["location_id"]),
        supplier_id=str(payload["supplier_id"]),
    )


def to_epcis_shaped_object_event(event: SyntheticReceiving) -> dict[str, Any]:
    """Map local receiving fixture to a clearly labelled EPCIS-shaped event."""
    if event.synthetic is not True:
        raise ValueError("non-synthetic event rejected")
    return {
        "eventType": "ObjectEvent",
        "eventTime": event.event_time,
        "eventTimeZoneOffset": event.timezone_offset,
        "epcList": [f"urn:kmh:oia:synthetic:lot:{event.product_lot_id}"],
        "action": "OBSERVE",
        "bizStep": "https://ref.gs1.org/cbv/BizStep-receiving",
        "readPoint": {"id": f"urn:kmh:oia:synthetic:location:{event.location_id}"},
        "bizTransactionList": [
            {
                "type": "urn:kmh:oia:synthetic:supplier",
                "bizTransaction": f"urn:kmh:oia:synthetic:party:{event.supplier_id}",
            }
        ],
        "oiaSyntheticMetadata": {
            "fixtureId": event.fixture_id,
            "eventId": event.event_id,
            "quantity": event.quantity,
            "uom": event.uom,
            "conformance": "NOT_CLAIMED",
        },
    }
