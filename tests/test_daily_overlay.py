from __future__ import annotations

import unittest

from scripts.generate_site import classify_daily_state, daily_overlay_from_snapshot


class DailyOverlayTests(unittest.TestCase):
    def test_overbought_rally_is_not_reported_as_unconditional_breakout(self) -> None:
        snapshot = {
            "close": 65000.0,
            "daily_close_prev": 64000.0,
            "daily_ma3": 64200.0,
            "daily_ma5": 63800.0,
            "daily_ma7": 63000.0,
            "daily_rsi6": 82.0,
            "daily_return_7d_pct": 6.5,
            "daily_volume_ratio": 0.72,
            "recent_high": 65400.0,
            "recent_low": 62000.0,
        }

        self.assertEqual(classify_daily_state(snapshot), "偏多震盪／接近壓力")

    def test_overlay_exposes_support_resistance_and_short_sample_limit(self) -> None:
        snapshot = {
            "close": 100.0,
            "daily_close_prev": 98.0,
            "daily_ma3": 99.0,
            "daily_ma5": 97.0,
            "daily_ma7": 95.0,
            "daily_rsi6": 72.0,
            "daily_return_7d_pct": 3.0,
            "daily_volume_ratio": 1.1,
            "recent_high": 102.0,
            "recent_low": 92.0,
        }

        overlay = daily_overlay_from_snapshot(snapshot)

        self.assertEqual(overlay["state"], "偏多但未確認突破")
        self.assertEqual(overlay["support"], "92.00–97.00")
        self.assertEqual(overlay["resistance"], "100.00–102.00")
        self.assertIn("RSI(6)", overlay["limitations"])

    def test_insufficient_daily_data_is_explicit(self) -> None:
        snapshot = {"close": 100.0}

        self.assertEqual(classify_daily_state(snapshot), "資料不足")
        self.assertEqual(daily_overlay_from_snapshot(snapshot)["confidence"], "低")


if __name__ == "__main__":
    unittest.main()
