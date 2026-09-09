from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.generate_site as gs


def fmt_volume_ratio(value) -> str:
    if not gs.is_number(value) or value <= 0:
        return "N/A"
    text = f"{value:,.2f}x"
    if value > 3:
        return f"{text}（可能受期貨／代理商品影響）"
    return text


def data_as_of_note(close_date: str | None, report_date: str) -> str:
    if not close_date or close_date == report_date:
        return ""
    return f"資料截至 {close_date}（市場休市或尚未更新）"


def stale_assets(snaps: dict[str, dict], report_date: str) -> list[str]:
    labels = []
    for spec in gs.ASSETS:
        snap = snaps.get(spec["key"], {})
        close_date = snap.get("close_date")
        if close_date and close_date != report_date:
            labels.append(f"{spec['label']}（{close_date}）")
    return labels


def stage_change_text(snaps: dict[str, dict], previous_stages: dict[str, str] | None) -> str:
    if not previous_stages:
        return ""
    changes = []
    for spec in gs.ASSETS:
        current = snaps[spec["key"]]["stage"]
        previous = previous_stages.get(spec["key"])
        if previous and previous != current:
            changes.append(f"{spec['label']}由{previous}改為{current}")
    if not changes:
        return "相對上週，各標的階段沒有改變。"
    return "相對上週，" + "、".join(changes) + "。"


def overall_summary(
    snaps: dict[str, dict],
    previous_stages: dict[str, str] | None = None,
    report_date: str | None = None,
) -> str:
    stages = [snaps[spec["key"]]["stage"] for spec in gs.ASSETS]
    heat = sum(stage == "過熱" for stage in stages)
    bulls = sum(stage in {"復蘇", "牛初"} for stage in stages)
    transitions = sum(stage == "過渡" for stage in stages)
    hot_labels = [spec["label"] for spec in gs.ASSETS if snaps[spec["key"]]["stage"] == "過熱"]
    if heat >= 5:
        base = "風險資產整體偏熱，台股與美股核心都已進入高檔區，現階段重點是控節奏而不是追價。"
    elif heat >= 3:
        names = "、".join(hot_labels) if hot_labels else "多數資產"
        base = f"市場仍偏多，但{names}已進入過熱或接近過熱，回檔後再布局會比追高舒服。"
    elif bulls >= 3:
        base = "風險資產仍有多頭延續力，核心資產可以續投，但仍要留意利率與美元背景。"
    elif transitions >= 5:
        base = "市場多數資產仍在轉折與整理區，先保留彈性比積極加碼更重要。"
    else:
        base = "市場結構正在分化，核心資產可續投，但單筆追價的容錯率已經下降。"
    change = stage_change_text(snaps, previous_stages)
    stale = stale_assets(snaps, report_date) if report_date else []
    stale_text = f"部分標的資料落後：{'、'.join(stale)}。" if stale else ""
    return " ".join(part for part in [base, change, stale_text] if part)


def liquidity_text(us10y_stage: str, dxy_stage: str) -> str:
    if us10y_stage in {"復蘇", "牛初"} and dxy_stage in {"熊底", "過渡"}:
        return f"10Y 目前為 {us10y_stage}、DXY 為 {dxy_stage}，利率壓力仍在，但美元尚未形成全面緊縮。"
    if us10y_stage == "過熱" or dxy_stage == "過熱":
        return f"10Y 目前為 {us10y_stage}、DXY 為 {dxy_stage}，資金面偏緊，風險資產估值容易受壓。"
    if us10y_stage in {"熊底", "過渡"} and dxy_stage in {"熊底", "過渡"}:
        return f"10Y 目前為 {us10y_stage}、DXY 為 {dxy_stage}，緊縮訊號減弱，但仍不是全面寬鬆。"
    return f"10Y 目前為 {us10y_stage}、DXY 為 {dxy_stage}，資金面仍要個案觀察。"


def discount_text(us10y_stage: str) -> str:
    if us10y_stage in {"過熱", "牛初"}:
        return "利率仍偏高或正在走升，對高 beta 與高估值資產的折現壓力還在。"
    if us10y_stage == "復蘇":
        return "利率壓力開始緩和，但還不足以當成全面放寬估值的理由。"
    return "利率並未明顯走升，折現壓力相對可控，但仍要看後續資料。"


def parse_weekly_stages(path: Path) -> dict[str, str]:
    if not path or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    stages: dict[str, str] = {}
    for spec in gs.ASSETS:
        match = re.search(rf"\| {re.escape(spec['label'])} \| ([^|]+) \|", text)
        if match:
            stages[spec["key"]] = match.group(1).strip()
    return stages


def _patched_build_snapshot(spec: dict, refresh_history: bool = True) -> dict:
    snapshot = _ORIG_BUILD(spec, refresh_history=refresh_history)
    ratio = snapshot.get("daily_volume_ratio")
    if ratio is not None and (not gs.is_number(ratio) or ratio <= 0):
        snapshot["daily_volume_ratio"] = None
        snapshot["daily_overlay"] = gs.daily_overlay_from_snapshot(snapshot)
    return snapshot


def render_homepage(latest_date: str, latest_report: str, snaps: dict[str, dict], latest_daily: str | None = None) -> str:
    top_line = overall_summary(snaps, report_date=latest_date)
    daily_link = (
        f'<p><a href="daily/{latest_daily}/">{latest_daily} 台灣市場日報</a></p>'
        if latest_daily
        else "<p>尚無日報</p>"
    )
    latest_cards = f"""<div class="card-grid">
  <div class="card">
    <h3>最新更新</h3>
    <p>{latest_date}</p>
    <p>{top_line}</p>
  </div>
  <div class="card">
    <h3>最新日報</h3>
    {daily_link}
    <p>每日交易日更新</p>
  </div>
  <div class="card">
    <h3>最新週報</h3>
    <p><a href="weekly/{latest_report}/">{latest_report} 台灣市場週報</a></p>
    <p>更新日期：{latest_date}</p>
  </div>
</div>"""
    asset_cards = []
    for spec in gs.ASSETS:
        snap = snaps[spec["key"]]
        badge = spec["key"].upper() if spec["key"] != "us10y" else "US10Y"
        asset_cards.append(
            "  <div class=\"thread-card thread-connector\">\n"
            f"    <div class=\"thread-meta\"><span class=\"thread-avatar\"></span><span class=\"thread-badge\">{badge}</span><span>{snap['stage']}</span></div>\n"
            f"    <p><a href=\"market/{spec['key']}/\">{spec['label']}</a>：{gs.advice_for(spec, snap['stage'])}</p>\n"
            "  </div>"
        )
    daily_index_link = "- <a href=\"daily/\">日報歷史索引</a>"
    daily_latest_link = (
        f'- <a href="daily/{latest_daily}/">最新日報：{latest_daily} 台灣市場日報</a>'
        if latest_daily
        else "- 尚無日報"
    )
    return f"""# 台灣市場週報

{latest_cards}

## 快速入口
- <a href="weekly/{latest_report}/">最新週報：{latest_report} 台灣市場週報</a>
- <a href="weekly/">週報歷史索引</a>
{daily_latest_link}
{daily_index_link}

## 最新標的狀態
<div class="thread-feed">
{chr(10).join(asset_cards)}
</div>
"""


def render_weekly_index_page(report_files: list[Path], latest_report: str, snaps: dict[str, dict]) -> str:
    rows = [[spec["label"], snaps[spec["key"]]["stage"], gs.advice_for(spec, snaps[spec["key"]]["stage"])] for spec in gs.ASSETS]
    stage_summary = gs.table(["標的", "階段", "判斷結果"], rows)
    archives = "\n".join([f'<a href="{p.stem}/">{p.stem} 台灣市場週報</a><br>' for p in report_files]) if report_files else "- 尚無報告"
    return f"""# 最新週報

## 最新一則
<a href="{latest_report}/">{latest_report} 台灣市場週報</a>

## 本週週報結論（{latest_report} 產出）
{stage_summary}

即時階段以[首頁](../)與各[標的頁](../market/btc/)為準；下表是本週週報產出時的快照，不會隨日報重算。

## 歷史歸檔
{archives}
"""


def _wrap_asset_page(spec: dict, snap: dict, report_date: str) -> str:
    text = _ORIG_ASSET(spec, snap, report_date)
    text = text.replace(
        f"{gs.fmt_pct(snap['daily_return_7d_pct'])} / {gs.fmt_num(snap['daily_volume_ratio'], 2)}x",
        f"{gs.fmt_pct(snap['daily_return_7d_pct'])} / {fmt_volume_ratio(snap['daily_volume_ratio'])}",
    )
    text = text.replace("N/Ax", "N/A").replace("0.00x", "N/A")
    note = data_as_of_note(snap.get("close_date"), report_date)
    if note:
        text = text.replace("| 最新可用收盤價 |", f"| {note} |", 1)
        text = text.replace("最新可用收盤價", note, 1)
    return text


def _wrap_daily_report(snaps: dict[str, dict], report_date: str) -> str:
    text = _ORIG_DAILY(snaps, report_date)
    if "資料日" not in text:
        text = text.replace(
            "| 標的 | 最新收盤 | 日報狀態 | 7 日報酬 | 支撐 / 壓力 | 信心 |",
            "| 標的 | 最新收盤 | 日報狀態 | 7 日報酬 | 支撐 / 壓力 | 信心 | 資料日 |",
            1,
        )
        text = text.replace("|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|", 1)
        lines = []
        for line in text.splitlines():
            if line.startswith("| ") and "（" in line and line.count("|") == 7:
                spec_label = line.split("|")[1].strip()
                spec = next((s for s in gs.ASSETS if s["label"] == spec_label), None)
                note = "當日"
                if spec:
                    note = data_as_of_note(snaps[spec["key"]].get("close_date"), report_date) or "當日"
                line = line.rstrip() + f" {note} |"
            lines.append(line)
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text.replace("N/Ax", "N/A").replace("0.00x", "N/A")


def render_weekly_report(snaps: dict[str, dict], report_date: str, previous_stages: dict[str, str] | None = None) -> str:
    text = _ORIG_WEEKLY(snaps, report_date)
    new_liq = liquidity_text(snaps["us10y"]["stage"], snaps["dxy"]["stage"])
    text = re.sub(r"- \*\*流動性\*\*：.*", f"- **流動性**：{new_liq}", text)
    text = re.sub(r"- \*\*通膨 / 折現\*\*：.*", f"- **通膨 / 折現**：{discount_text(snaps['us10y']['stage'])}", text)
    extra = overall_summary(snaps, previous_stages=previous_stages, report_date=report_date)
    text = text.replace(_ORIG_SUMMARY(snaps), extra)
    return text


_ORIG_BUILD = gs.build_snapshot
_ORIG_ASSET = gs.render_asset_page
_ORIG_DAILY = gs.render_daily_report
_ORIG_WEEKLY = gs.render_weekly_report
_ORIG_SUMMARY = gs.overall_summary
_ORIG_MAIN = gs.main
_APPLIED = False


def apply() -> None:
    global _APPLIED
    if _APPLIED:
        return
    gs.fmt_volume_ratio = fmt_volume_ratio
    gs.data_as_of_note = data_as_of_note
    gs.stale_assets = stale_assets
    gs.overall_summary = overall_summary
    gs.liquidity_text = liquidity_text
    gs.discount_text = discount_text
    gs.parse_weekly_stages = parse_weekly_stages
    gs.build_snapshot = _patched_build_snapshot
    gs.render_homepage = render_homepage
    gs.render_weekly_index_page = render_weekly_index_page
    gs.render_asset_page = _wrap_asset_page
    gs.render_daily_report = _wrap_daily_report
    gs.render_weekly_report = render_weekly_report
    _APPLIED = True


def main() -> None:
    apply()
    def patched_main() -> None:
        apply()
        if hasattr(gs, "WEEKLY_DIR"):
            weekly_files = sorted(
                [p for p in gs.WEEKLY_DIR.glob("*.md") if p.name != "index.md"],
                reverse=True,
            )
            previous_weekly = weekly_files[0] if weekly_files else None
            previous_stages = parse_weekly_stages(previous_weekly) if previous_weekly else {}

            def weekly_with_prev(snaps, report_date, previous_stages=previous_stages):
                return render_weekly_report(snaps, report_date, previous_stages)

            gs.render_weekly_report = weekly_with_prev
        _ORIG_MAIN()

    patched_main()


if __name__ == "__main__":
    main()
