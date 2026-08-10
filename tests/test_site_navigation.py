from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.generate_site import ASSETS, render_daily_index_page, render_homepage, render_weekly_index_page


ROOT = Path(__file__).resolve().parents[1]


class SiteNavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report_date = "2026-07-27"
        self.snaps = {spec["key"]: {"stage": "復甦"} for spec in ASSETS}

    def test_homepage_shows_latest_update_and_direct_report_link(self) -> None:
        html = render_homepage(self.report_date, self.report_date, self.snaps, self.report_date)

        self.assertIn(self.report_date, html)
        self.assertIn("2026-07-27 台灣市場週報", html)
        self.assertIn("weekly/2026-07-27/", html)
        self.assertIn("daily/2026-07-27/", html)
        self.assertNotIn("weekly/2026-07-27.md", html)
        self.assertNotIn("weekly/index.md", html)
        self.assertNotIn("[最新週報](weekly/index.md)", html)
        self.assertNotIn("去識別化", html)
        self.assertNotIn("公開版", html)
        self.assertNotIn("自動生成", html)
        self.assertNotIn("Nasdaq 100", html)
        self.assertIn("QQQ", html)

    def test_mkdocs_nav_has_no_hardcoded_weekly_dates(self) -> None:
        mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIsNone(re.search(r"weekly/\d{4}-\d{2}-\d{2}\.md", mkdocs))
        self.assertIn("最新總覽: weekly/index.md", mkdocs)

    def test_weekly_index_puts_latest_report_first(self) -> None:
        report_files = [
            ROOT / "docs/weekly/2026-07-27.md",
            ROOT / "docs/weekly/2026-07-20.md",
            ROOT / "docs/weekly/2026-07-13.md",
        ]
        html = render_weekly_index_page(report_files, self.report_date, self.snaps)

        latest_position = html.index("2026-07-27 台灣市場週報")
        previous_position = html.index("2026-07-20 台灣市場週報")
        oldest_position = html.index("2026-07-13 台灣市場週報")
        self.assertLess(latest_position, previous_position)
        self.assertLess(previous_position, oldest_position)

    def test_latest_report_link_is_not_only_weekly_index(self) -> None:
        html = render_homepage(self.report_date, self.report_date, self.snaps)
        direct_links = re.findall(r'href="(weekly/[^"/]+/)"', html)

        self.assertIn("weekly/2026-07-27/", direct_links)

    def test_daily_index_puts_latest_report_first(self) -> None:
        report_files = [
            ROOT / "docs/daily/2026-07-27.md",
            ROOT / "docs/daily/2026-07-26.md",
        ]
        html = render_daily_index_page(report_files, self.report_date)
        self.assertLess(
            html.index("2026-07-27 台灣市場日報"),
            html.index("2026-07-26 台灣市場日報"),
        )

    def test_checked_in_homepage_exposes_current_report(self) -> None:
        homepage = (ROOT / "docs/index.md").read_text(encoding="utf-8")
        report_dates = sorted(
            report.stem
            for report in (ROOT / "docs/weekly").glob("*.md")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", report.stem)
        )
        latest_report = report_dates[-1]

        self.assertIn(f"{latest_report} 台灣市場週報", homepage)
        self.assertIn(f'href="weekly/{latest_report}/"', homepage)

    def test_checked_in_docs_exclude_internal_disclosures_and_prompts(self) -> None:
        forbidden = (
            "去識別化",
            "公開範圍",
            "公開版",
            "私人資產",
            "槓桿資訊",
            "槓桿資料",
            "資料限制",
            "判讀規則",
            "現金流建議買入區塊",
            "本頁由排程自動生成",
        )
        for path in (ROOT / "docs").rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, content, f"{phrase} remains in {path.relative_to(ROOT)}")

    def test_weekly_report_uses_asset_and_macro_action_sections(self) -> None:
        latest = (ROOT / "docs/weekly/2026-08-10.md").read_text(encoding="utf-8")
        self.assertIn("## 資產行動摘要", latest)
        self.assertIn("## 宏觀訊號", latest)
        self.assertNotIn("## 現金流建議買入區塊", latest)
        self.assertNotIn("| Nasdaq 100 |", latest)
        self.assertIn("| QQQ |", latest)
        self.assertNotIn("先看結論，再看細節", latest)
        self.assertNotIn("這一頁放最近一週", latest)

    def test_uiux_styles_are_loaded_and_mobile_safe(self) -> None:
        css = (ROOT / "docs/stylesheets/extra.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 768px)", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn(".card-grid", css)

    def test_ndx_is_removed_and_qqq_is_retained(self) -> None:
        mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertNotIn("Nasdaq 100", mkdocs)
        self.assertNotIn("market/ndx.md", mkdocs)
        self.assertIn("QQQ: market/qqq.md", mkdocs)
        self.assertNotIn('"key": "ndx"', (ROOT / "scripts/generate_site.py").read_text(encoding="utf-8"))
        self.assertIn('"key": "qqq"', (ROOT / "scripts/generate_site.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
