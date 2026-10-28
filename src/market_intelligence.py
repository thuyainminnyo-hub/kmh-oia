"""Local-only, deterministic market indicator pilot using synthetic OHLCV data.

No network access, live market data, investment advice, or order execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Iterable
from uuid import uuid4


class MarketDataValidationError(ValueError):
    """Raised when OHLCV input violates the pilot data contract."""


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    occurred_at: str
    analysis_id: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class IndicatorResult:
    analysis_id: str
    candle_count: int
    rsi_14: float
    ema_50: float
    bollinger_middle_20: float
    bollinger_upper_20_2: float
    bollinger_lower_20_2: float
    audit_events: tuple[AuditEvent, ...]


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise MarketDataValidationError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError("timestamp must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MarketDataValidationError("timestamp must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def validate_candles(candles: Iterable[Candle]) -> tuple[Candle, ...]:
    """Validate and freeze ordered OHLCV input; fail closed on malformed data."""
    rows = tuple(candles)
    if len(rows) < 50:
        raise MarketDataValidationError("at least 50 candles are required for EMA(50)")

    previous: datetime | None = None
    seen: set[datetime] = set()
    for index, candle in enumerate(rows):
        if not isinstance(candle, Candle):
            raise MarketDataValidationError(f"candle[{index}] must be a Candle")
        timestamp = _parse_timestamp(candle.timestamp)
        if timestamp in seen:
            raise MarketDataValidationError(f"duplicate timestamp at candle[{index}]")
        if previous is not None and timestamp <= previous:
            raise MarketDataValidationError("candles must be strictly increasing by timestamp")
        seen.add(timestamp)
        previous = timestamp

        values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            raise MarketDataValidationError(f"candle[{index}] values must be finite numbers")
        if min(candle.open, candle.high, candle.low, candle.close) <= 0:
            raise MarketDataValidationError(f"candle[{index}] prices must be positive")
        if candle.volume < 0:
            raise MarketDataValidationError(f"candle[{index}] volume must be non-negative")
        if candle.low > candle.high or not (candle.low <= candle.open <= candle.high):
            raise MarketDataValidationError(f"candle[{index}] has invalid OHLC range")
        if not (candle.low <= candle.close <= candle.high):
            raise MarketDataValidationError(f"candle[{index}] close is outside low/high range")
    return rows


def _ema(values: tuple[float, ...], period: int) -> float:
    if len(values) < period:
        raise MarketDataValidationError(f"not enough values for EMA({period})")
    current = sum(values[:period]) / period
    alpha = 2.0 / (period + 1)
    for value in values[period:]:
        current = alpha * value + (1.0 - alpha) * current
    return current


def _rsi_wilder(values: tuple[float, ...], period: int = 14) -> float:
    if len(values) <= period:
        raise MarketDataValidationError(f"not enough values for RSI({period})")
    changes = tuple(values[index] - values[index - 1] for index in range(1, len(values)))
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    for index in range(period, len(gains)):
        average_gain = ((period - 1) * average_gain + gains[index]) / period
        average_loss = ((period - 1) * average_loss + losses[index]) / period
    if average_gain == 0 and average_loss == 0:
        return 50.0
    if average_loss == 0:
        return 100.0
    if average_gain == 0:
        return 0.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def analyze_synthetic_market(candles: Iterable[Candle], *, analysis_id: str | None = None) -> IndicatorResult:
    """Validate synthetic OHLCV and calculate RSI(14), EMA(50), and BB(20, 2)."""
    rows = validate_candles(candles)
    closes = tuple(float(row.close) for row in rows)
    identifier = analysis_id or str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    metadata = {"symbol_scope": "synthetic", "candle_count": str(len(rows))}
    events = (
        AuditEvent("market.analysis.requested", now, identifier, metadata),
        AuditEvent("market.data.quality_passed", now, identifier, metadata),
    )

    period_closes = closes[-20:]
    middle = sum(period_closes) / 20
    variance = sum((value - middle) ** 2 for value in period_closes) / 20
    deviation = math.sqrt(variance)
    result_events = events + (
        AuditEvent(
            "market.indicators.computed",
            now,
            identifier,
            {
                **metadata,
                "indicators": "RSI(14),EMA(50),Bollinger(20,2)",
                "calculation_version": "market-indicators-v1",
            },
        ),
    )
    return IndicatorResult(
        analysis_id=identifier,
        candle_count=len(rows),
        rsi_14=_rsi_wilder(closes),
        ema_50=_ema(closes, 50),
        bollinger_middle_20=middle,
        bollinger_upper_20_2=middle + 2 * deviation,
        bollinger_lower_20_2=middle - 2 * deviation,
        audit_events=result_events,
    )
