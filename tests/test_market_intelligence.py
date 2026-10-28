import math
import unittest
from datetime import datetime, timedelta, timezone

from src.market_intelligence import (
    Candle,
    MarketDataValidationError,
    analyze_synthetic_market,
    validate_candles,
)


def rising_fixture(count=60):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for index in range(count):
        close = 100.0 + index
        rows.append(Candle(
            timestamp=(start + timedelta(days=index)).isoformat(),
            open=close - 0.25,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=1000.0 + index,
        ))
    return rows


class MarketIntelligenceTests(unittest.TestCase):
    def test_valid_synthetic_input_produces_indicators_and_ordered_audit(self):
        result = analyze_synthetic_market(rising_fixture(), analysis_id="analysis-test-1")
        self.assertEqual(result.candle_count, 60)
        self.assertEqual(result.analysis_id, "analysis-test-1")
        self.assertGreater(result.rsi_14, 99.0)
        self.assertAlmostEqual(result.ema_50, 134.5, places=8)
        self.assertAlmostEqual(result.bollinger_middle_20, 149.5, places=8)
        self.assertGreater(result.bollinger_upper_20_2, result.bollinger_middle_20)
        self.assertLess(result.bollinger_lower_20_2, result.bollinger_middle_20)
        self.assertEqual(
            [event.event_type for event in result.audit_events],
            [
                "market.analysis.requested",
                "market.data.quality_passed",
                "market.indicators.computed",
            ],
        )
        self.assertEqual({event.analysis_id for event in result.audit_events}, {"analysis-test-1"})

    def test_flat_series_has_neutral_rsi(self):
        rows = rising_fixture(60)
        rows = [Candle(r.timestamp, 100, 101, 99, 100, r.volume) for r in rows]
        result = analyze_synthetic_market(rows, analysis_id="flat")
        self.assertEqual(result.rsi_14, 50.0)

    def test_rejects_too_few_candles(self):
        with self.assertRaisesRegex(MarketDataValidationError, "at least 50"):
            validate_candles(rising_fixture(49))

    def test_rejects_timezone_naive_timestamp(self):
        rows = rising_fixture()
        rows[10] = Candle("2026-01-11T00:00:00", rows[10].open, rows[10].high, rows[10].low, rows[10].close, rows[10].volume)
        with self.assertRaisesRegex(MarketDataValidationError, "explicit timezone"):
            validate_candles(rows)

    def test_rejects_duplicate_or_unordered_timestamp(self):
        rows = rising_fixture()
        rows[20] = Candle(rows[19].timestamp, rows[20].open, rows[20].high, rows[20].low, rows[20].close, rows[20].volume)
        with self.assertRaisesRegex(MarketDataValidationError, "duplicate timestamp"):
            validate_candles(rows)
        rows = rising_fixture()
        rows[20], rows[21] = rows[21], rows[20]
        with self.assertRaisesRegex(MarketDataValidationError, "strictly increasing"):
            validate_candles(rows)

    def test_rejects_invalid_ohlc_and_negative_volume(self):
        rows = rising_fixture()
        row = rows[5]
        rows[5] = Candle(row.timestamp, row.open, row.high, row.low, row.high + 1, row.volume)
        with self.assertRaisesRegex(MarketDataValidationError, "close is outside"):
            validate_candles(rows)
        rows = rising_fixture()
        row = rows[5]
        rows[5] = Candle(row.timestamp, row.open, row.high, row.low, row.close, -1)
        with self.assertRaisesRegex(MarketDataValidationError, "volume"):
            validate_candles(rows)

    def test_rejects_non_finite_values(self):
        rows = rising_fixture()
        row = rows[3]
        rows[3] = Candle(row.timestamp, row.open, math.inf, row.low, row.close, row.volume)
        with self.assertRaisesRegex(MarketDataValidationError, "finite"):
            validate_candles(rows)

    def test_same_input_same_indicator_values(self):
        rows = rising_fixture()
        first = analyze_synthetic_market(rows, analysis_id="same-a")
        second = analyze_synthetic_market(rows, analysis_id="same-b")
        self.assertEqual(
            (
                first.rsi_14, first.ema_50, first.bollinger_middle_20,
                first.bollinger_upper_20_2, first.bollinger_lower_20_2,
            ),
            (
                second.rsi_14, second.ema_50, second.bollinger_middle_20,
                second.bollinger_upper_20_2, second.bollinger_lower_20_2,
            ),
        )


if __name__ == "__main__":
    unittest.main()
