# KMH OIA Market Intelligence Module v1 — P0/P1 Specification

**Status:** implementation proposal on an isolated pilot branch; verification pending  
**Reference:** StockLyzer user-provided screenshot (UI observed; provider internals and prediction accuracy unverified)  
**Boundary:** local-only, deterministic calculations, synthetic fixtures only. No live provider, network ingestion, cloud deployment, brokerage connection, or order execution.

## Goal
Create a reproducible market-data analysis primitive that validates synthetic OHLCV input, calculates technical indicators deterministically, and emits structured audit events. This is not an investment-advice engine and does not make a buy/sell recommendation.

## P0 — Data contract
Each candle contains:
- `timestamp`: ISO-8601 timestamp with explicit timezone.
- `open`, `high`, `low`, `close`: finite positive numeric values.
- `volume`: finite non-negative numeric value.
- Candles must be unique and strictly increasing by timestamp.
- OHLC relationships must be valid: low <= open/close <= high and low <= high.
- At least 50 candles are required for the initial EMA(50) output.
- Stale-data policy, market calendar, corporate-action adjustment, and provider provenance are intentionally out of scope until a real source is explicitly approved.

## P1 — Deterministic indicators
- RSI(14): Wilder smoothing, seeded from the first 14 close-to-close changes.
- EMA(50): SMA seed over the first 50 closes, then standard EMA recurrence with alpha = 2/(period+1).
- Bollinger Bands(20, 2): last-20 close SMA +/- 2 population standard deviations.
- Calculations use unrounded float values internally; presentation rounding belongs to a future renderer.
- Flat RSI series returns 50. A no-loss series returns 100; a no-gain series returns 0.

## Data flow
Synthetic fixture -> schema/chronology validation -> frozen tuple of candles -> indicators -> structured result + audit events.
Invalid input raises `MarketDataValidationError`; it must not produce a normal analysis result.

## Audit events
Every successful analysis emits ordered events:
1. `market.analysis.requested`
2. `market.data.quality_passed`
3. `market.indicators.computed`

Each event has an event type, UTC timestamp, analysis ID, and small metadata map. Audit events must not contain secrets. Failed validation is represented by the exception at this initial stage; durable append-only audit storage and explicit failure-event persistence are follow-up work.

## Verification gates
- G1: malformed, non-finite, non-positive, duplicate, unordered, timezone-naive, and inconsistent OHLCV fixtures are rejected.
- G2: RSI/EMA/Bollinger calculations match independently hand-computed fixtures within defined tolerance.
- G3: identical inputs produce identical indicator values; generated IDs/timestamps are excluded from that determinism assertion.
- G4: successful outputs contain the expected ordered audit event names and share one analysis ID.
- G5: no live network, external market feed, account, or order-execution code is added.
- G6: run the repository's full suite and CI before treating any gate as passed.

## Explicit limitations
This module does not calculate forecast confidence, targets, stop-loss levels, fair value, or trading decisions. A future scenario layer must cite its inputs and have separately validated risk rules. A percentage called “confidence” must not be represented as a calibrated probability without out-of-sample evidence.
