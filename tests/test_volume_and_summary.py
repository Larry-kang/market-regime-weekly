from __future__ import annotations

import unittest
from pathlib import Path

from scripts.site_ext import apply, data_as_of_note, fmt_volume_ratio, overall_summary

apply()
from scripts.generate_site import ASSETS, render_homepage, render_weekly_index_page, render_weekly_report


class VolumeAndSummaryTests(unittest.TestCase):
    def test_volume_ratio_hides_missing_and_zero(self) -> None:
        self.assertEqual(fmt_volume_ratio(None), "N/A")
        self.assertEqual(fmt_volume_ratio(0), "N/A")
        self.assertEqual(fmt_volume_ratio(-1), "N/A")
        self.assertEqual(fmt_volume_ratio(1.05), "1.05x")
        self.assertIn("代理商品", fmt_volume_ratio(5.05))

    def test_stale_close_note(self) -> None:
        self.assertEqual(data_as_of_note("2026-09-08", "2026-09-08"), "")
        self.assertIn("資料截至 2026-09-04", data_as_of_note("2026-09-04", "2026-09-08"))

    def test_summary_mentions_week_over_week_change(self) -> None:
        snaps = {spec["key"]: {"stage": "過熱", "close_date": "2026-09-08"} for spec in ASSETS}
        snaps["btc"]["stage"] = "復蘇"
        previous = {spec["key"]: "過熱" for spec in ASSETS}
        text = overall_summary(snaps, previous_stages=previous, report_date="2026-09-08")
        self.assertIn("BTC由過熱改為復蘇", text)

    def test_homepage_links_market_pages(self) -> None:
        snaps = {spec["key"]: {"stage": "復蘇"} for spec in ASSETS}
        html = render_homepage("2026-09-08", "2026-09-07", snaps, "2026-09-08")
        self.assertIn('href="market/btc/"', html)
        self.assertIn("daily/", html)

    def test_weekly_index_is_labeled_snapshot(self) -> None:
        snaps = {spec["key"]: {"stage": "過熱"} for spec in ASSETS}
        html = render_weekly_index_page(
            [Path("docs/weekly/2026-09-07.md")],
            "2026-09-07",
            snaps,
        )
        self.assertIn("本週週報結論", html)
        self.assertIn("即時階段", html)

    def test_weekly_report_does_not_use_fixed_rate_boilerplate(self) -> None:
        snaps = {
            spec["key"]: {
                "stage": "過渡",
                "close": 1,
                "dist_200w_pct": 1,
                "daily_rsi": 50,
                "weekly_rsi": 50,
                "daily_overlay": {"state": "中性震盪", "confidence": "中", "support": "1-2", "resistance": "3-4"},
                "close_date": "2026-09-07",
            }
            for spec in ASSETS
        }
        html = render_weekly_report(snaps, "2026-09-07", previous_stages={"btc": "過熱"})
        self.assertNotIn("高利率尚未完全退場", html)
        self.assertIn("BTC由過熱改為過渡", html)


if __name__ == "__main__":
    unittest.main()
