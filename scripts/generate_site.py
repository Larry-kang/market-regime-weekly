from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAILY_DIR = DOCS / "daily"
MARKET_DIR = DOCS / "market"
WEEKLY_DIR = DOCS / "weekly"
TZ = ZoneInfo("Asia/Taipei")
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")

STAGE_ORDER = ["熊底", "過渡", "復甦", "牛初", "過熱"]

ASSETS = [
    {
        "key": "btc",
        "label": "BTC",
        "symbol": "BTC-USD",
        "kind": "btc",
        "page_title": "BTC 階段分析",
        "summary": "BTC 是高波動成長資產，適合用長期分批處理，而不是一次性重壓。",
        "risk": "長均線確認 / 波動風險",
        "actions": {
            "熊底": "小額試單或等待確認",
            "過渡": "維持 DCA，等待更明確的長均線確認",
            "復甦": "可續投，保留彈性",
            "牛初": "核心可續投",
            "過熱": "放慢節奏，等回檔",
        },
    },
    {
        "key": "taiex",
        "label": "TAIEX",
        "symbol": "^TWII",
        "kind": "equity",
        "page_title": "TAIEX 階段分析",
        "summary": "台股加權常常跑得比想像快，趨勢強時很強，但乖離擴大後也容易變得難追。",
        "risk": "乖離過大 / 追高風險",
        "actions": {
            "熊底": "只觀察，不急著動作",
            "過渡": "等確認，不追價",
            "復甦": "可小量分批",
            "牛初": "可投但不追高",
            "過熱": "先等回檔，不追高",
        },
    },
    {
        "key": "sp500",
        "label": "S&P 500",
        "symbol": "^GSPC",
        "kind": "equity",
        "page_title": "S&P 500 階段分析",
        "summary": "S&P 500 是核心風險資產的代表，適合用規律的資金節奏持續累積。",
        "risk": "估值與風險偏好",
        "actions": {
            "熊底": "先等底部確認",
            "過渡": "核心分批開始",
            "復甦": "核心可續投",
            "牛初": "核心可續投",
            "過熱": "續投但節奏放慢",
        },
    },
    {
        "key": "qqq",
        "label": "QQQ",
        "symbol": "QQQ",
        "kind": "equity",
        "page_title": "QQQ 短線與階段分析",
        "summary": "QQQ 是可交易的高 beta 成長 ETF，短線訊號用來補充中期結構。",
        "risk": "高 beta / 超買與量價背離",
        "actions": {
            "熊底": "只小量觀察",
            "過渡": "等待結構確認",
            "復甦": "回檔後分批",
            "牛初": "只在回檔加",
            "過熱": "避免追價",
        },
    },
    {
        "key": "gold",
        "label": "黃金",
        "symbol": "GC=F",
        "kind": "macro",
        "page_title": "黃金階段分析",
        "summary": "黃金更像對沖與防守資產，適合在宏觀環境轉弱或避險需求升溫時觀察。",
        "risk": "整理區 / 非主攻",
        "actions": {
            "熊底": "等待趨勢翻正",
            "過渡": "暫不主攻",
            "復甦": "可小量布局",
            "牛初": "按節奏分批",
            "過熱": "觀察乖離，不追高",
        },
    },
    {
        "key": "us10y",
        "label": "美國 10Y",
        "symbol": "^TNX",
        "kind": "macro",
        "page_title": "美國 10Y 階段分析",
        "summary": "10 年期殖利率會直接影響估值與資金面，尤其對高 beta 資產最敏感。",
        "risk": "利率壓力 / 估值折現",
        "actions": {
            "熊底": "觀察利率轉折",
            "過渡": "持續觀察",
            "復甦": "利率壓力緩和時可提高風險偏好",
            "牛初": "若趨勢穩定可視為順風",
            "過熱": "留意折現壓力",
        },
    },
    {
        "key": "dxy",
        "label": "DXY",
        "symbol": "DX-Y.NYB",
        "kind": "macro",
        "page_title": "DXY 階段分析",
        "summary": "美元強弱會影響全球流動性與風險資產估值，常是市場情緒的重要背景音。",
        "risk": "美元偏強 / 壓抑風險資產",
        "actions": {
            "熊底": "先觀察美元壓力",
            "過渡": "暫不追",
            "復甦": "若美元回落可提高風險偏好",
            "牛初": "維持觀察",
            "過熱": "美元若太強，要小心風險資產",
        },
    },
    {
        "key": "vix",
        "label": "VIX",
        "symbol": "^VIX",
        "kind": "macro",
        "page_title": "VIX 階段分析",
        "summary": "VIX 反映波動與恐慌溫度，低波動時市場通常較平靜，但不代表可以無腦追高。",
        "risk": "波動是否升溫",
        "actions": {
            "熊底": "防守優先",
            "過渡": "觀察波動變化",
            "復甦": "若回升可提高風控",
            "牛初": "留意波動是否開始放大",
            "過熱": "若波動升溫，降低追價",
        },
    },
]


def ensure_dirs() -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_DIR.mkdir(parents=True, exist_ok=True)
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS / "stylesheets").mkdir(parents=True, exist_ok=True)


def is_number(value) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value))


def fmt_num(value, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_pct(value, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"{value:+.{decimals}f}%"


def bucket_rsi(value: float | None) -> str:
    if value is None or math.isnan(value):
        return "N/A"
    if value < 30:
        return "超賣"
    if value < 45:
        return "低檔"
    if value < 55:
        return "中性"
    if value < 70:
        return "中性偏強"
    return "超買"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([head, sep, *body])


def fetch_market_history(symbol: str, period: str = "10y", retries: int = 3) -> pd.DataFrame:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False, actions=False)
            if df.empty:
                raise RuntimeError("empty history")
            if "Close" not in df.columns:
                raise RuntimeError("Close column missing")
            df = df.dropna(subset=["Close"]).copy()
            df.index = pd.to_datetime(df.index)
            df = df[~df.index.duplicated(keep="last")].sort_index()
            return df
        except Exception as exc:  # pragma: no cover - network dependent
            last_exc = exc
            time.sleep(1.2 * attempt)
    raise RuntimeError(f"Failed to fetch {symbol}: {last_exc}")


def fetch_close_series(symbol: str, period: str = "10y", retries: int = 3) -> pd.Series:
    """Backward-compatible close-only accessor used by external callers."""
    return fetch_market_history(symbol, period=period, retries=retries)["Close"].astype(float)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    return out


def macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal
    return line, signal, hist


def trend_text(current: float | None, previous: float | None) -> str:
    if current is None or previous is None or (isinstance(current, float) and math.isnan(current)) or (isinstance(previous, float) and math.isnan(previous)):
        return "N/A"
    return "走升" if current >= previous else "走弱"


def macd_text(line: float | None, signal: float | None, hist: float | None, prev_hist: float | None) -> str:
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in [line, signal, hist]):
        return "N/A"
    relation = "高於" if line >= signal else "低於"
    sign = "正" if hist >= 0 else "負"
    if prev_hist is None or (isinstance(prev_hist, float) and math.isnan(prev_hist)):
        momentum = ""
    else:
        momentum = "，較前值收斂" if abs(hist) < abs(prev_hist) else "，較前值擴大"
    return f"MACD 線{relation}訊號線，柱狀體{sign}{abs(hist):.2f}{momentum}"


def classify_equity_stage(snapshot: dict) -> str:
    price = snapshot["close"]
    w20 = snapshot["weekly_ma20"]
    w50 = snapshot["weekly_ma50"]
    w200 = snapshot["weekly_ma200"]
    wrsi = snapshot["weekly_rsi"]
    whist = snapshot["weekly_hist"]
    dist = snapshot["dist_200w_pct"]

    if any(not is_number(v) for v in [price, w20, w50, w200, wrsi, whist, dist]):
        return "過渡"

    if price < w200 and w20 < w50 < w200 and wrsi < 40 and whist < 0:
        return "熊底"
    if price < w200 * 0.97 or (price < w200 and wrsi < 50):
        return "過渡"
    if price >= w200 and w20 > w50 > w200 and 50 <= wrsi < 70 and dist < 25:
        return "牛初"
    if price >= w200 and (wrsi >= 70 or dist >= 25):
        return "過熱"
    if price >= w200:
        return "復甦"
    return "過渡"


def classify_btc_stage(snapshot: dict) -> str:
    price = snapshot["close"]
    d20 = snapshot["daily_ma20"]
    d50 = snapshot["daily_ma50"]
    d200 = snapshot["daily_ma200"]
    w20 = snapshot["weekly_ma20"]
    w50 = snapshot["weekly_ma50"]
    w200 = snapshot["weekly_ma200"]
    drsi = snapshot["daily_rsi"]
    wrsi = snapshot["weekly_rsi"]
    dhist = snapshot["daily_hist"]
    whist = snapshot["weekly_hist"]
    dist = snapshot["dist_200w_pct"]

    if any(not is_number(v) for v in [price, d20, d50, d200, w20, w50, w200, drsi, wrsi, dhist, whist, dist]):
        return "過渡"

    if price < w200 and w20 < w50 < w200 and wrsi < 35 and whist < 0:
        return "熊底"

    if price < w200 * 0.98 or (price < w200 and wrsi < 45):
        return "過渡"

    if price >= w200 and wrsi < 45 and whist < 0 and abs(dist) < 10:
        return "過渡"

    if price >= w200 and (w20 > w50 > w200 or (drsi >= 50 and wrsi >= 45 and whist >= 0)):
        if wrsi >= 70 or dist >= 25:
            return "過熱"
        if w20 > w50 > w200 and 50 <= wrsi < 65 and dist < 15:
            return "牛初"
        return "復甦"

    if price >= w200:
        return "復甦"

    return "過渡"


def classify_macro_stage(snapshot: dict) -> str:
    price = snapshot["close"]
    w20 = snapshot["weekly_ma20"]
    w50 = snapshot["weekly_ma50"]
    w200 = snapshot["weekly_ma200"]
    wrsi = snapshot["weekly_rsi"]
    whist = snapshot["weekly_hist"]
    dist = snapshot["dist_200w_pct"]

    if any(not is_number(v) for v in [price, w20, w50, w200, wrsi, whist, dist]):
        return "過渡"

    if price < w200 and wrsi < 50:
        return "過渡"
    if price >= w200 and w20 > w50 > w200 and 50 <= wrsi < 70 and dist < 25:
        return "牛初"
    if price >= w200 and dist >= 35 and wrsi >= 55:
        return "過熱"
    if price >= w200 and price < w50 and wrsi < 50:
        return "復甦"
    if price >= w200:
        return "復甦"
    return "過渡"


def classify_stage(spec: dict, snapshot: dict) -> str:
    kind = spec.get("kind", "equity")
    if kind == "btc":
        return classify_btc_stage(snapshot)
    if kind == "macro":
        return classify_macro_stage(snapshot)
    return classify_equity_stage(snapshot)


def stage_proximity(current: str, row: str) -> str:
    current_idx = STAGE_ORDER.index(current)
    row_idx = STAGE_ORDER.index(row)
    if current_idx == row_idx:
        return "是，最貼近目前狀態"
    if abs(current_idx - row_idx) == 1:
        return "部分符合"
    return "否"


def stage_table(current_stage: str) -> str:
    rows = [
        ["熊底", "跌破 200W、20W/50W/200W 空頭排列、RSI 低檔、MACD 負值擴大", stage_proximity(current_stage, "熊底")],
        ["過渡", "仍未完全站穩 200W，或剛開始靠近，動能改善但還不完整", stage_proximity(current_stage, "過渡")],
        ["復甦", "收復 200W，短中期均線開始翻揚，動能回到正向", stage_proximity(current_stage, "復甦")],
        ["牛初", "20W > 50W > 200W，價格站穩長均線，RSI 多在中性到偏強", stage_proximity(current_stage, "牛初")],
        ["過熱", "漲幅與乖離擴大，週 RSI 進入超買，追價風險高", stage_proximity(current_stage, "過熱")],
    ]
    return table(["階段", "典型訊號特徵", "目前是否接近/位於"], rows)


def daily_zone(value: float | None) -> str:
    return bucket_rsi(value)


def weekly_zone(value: float | None) -> str:
    return bucket_rsi(value)


def classify_daily_state(snapshot: dict) -> str:
    """Classify the short-term public daily overlay without private inputs."""
    required = [
        "close", "daily_ma3", "daily_ma5", "daily_ma7", "daily_rsi6",
        "daily_return_7d_pct", "recent_high", "recent_low",
    ]
    if any(not is_number(snapshot.get(key)) for key in required):
        return "資料不足"

    close = snapshot["close"]
    ma3, ma5, ma7 = snapshot["daily_ma3"], snapshot["daily_ma5"], snapshot["daily_ma7"]
    rsi6 = snapshot["daily_rsi6"]
    high = snapshot["recent_high"]
    distance_to_high = (high - close) / high * 100 if high else None

    if close < ma7:
        return "短線轉弱"
    if rsi6 >= 80 and distance_to_high is not None and distance_to_high <= 2.0:
        return "偏多震盪／接近壓力"
    if close >= ma3 >= ma5 >= ma7 and rsi6 >= 70:
        return "偏多但未確認突破"
    if close >= ma5 and snapshot["daily_return_7d_pct"] > 0:
        return "偏多整理"
    if close < ma5 and snapshot["daily_return_7d_pct"] < 0:
        return "偏空整理"
    return "中性震盪"


def _fmt_zone(low: float | None, high: float | None) -> str:
    if not is_number(low) or not is_number(high):
        return "N/A"
    return f"{low:,.2f}–{high:,.2f}"


def daily_overlay_from_snapshot(snapshot: dict) -> dict:
    state = classify_daily_state(snapshot)
    complete = state != "資料不足"
    ma5 = snapshot.get("daily_ma5")
    ma7 = snapshot.get("daily_ma7")
    recent_low = snapshot.get("recent_low")
    recent_high = snapshot.get("recent_high")
    support_values = [v for v in [recent_low, ma7] if is_number(v)]
    support_low = min(support_values) if support_values else None
    support_high = max([v for v in [recent_low, ma5] if is_number(v)], default=None)
    resistance_values = [v for v in [snapshot.get("close"), recent_high] if is_number(v)]
    resistance_low = min(resistance_values) if resistance_values else None
    resistance_high = max(resistance_values) if resistance_values else None
    limitations = ["RSI(6) 僅作短線提示，不等同標準 RSI(14)"]
    if not is_number(snapshot.get("daily_volume_ratio")):
        limitations.append("成交量資料不可用")
    return {
        "state": state,
        "support": _fmt_zone(support_low, support_high),
        "resistance": _fmt_zone(resistance_low, resistance_high),
        "confidence": "中" if complete else "低",
        "limitations": "；".join(limitations),
    }


def build_snapshot(spec: dict) -> dict:
    history = fetch_market_history(spec["symbol"])
    close = history["Close"].astype(float)
    weekly = close.resample("W-FRI").last().dropna()

    d_rsi = rsi(close)
    w_rsi = rsi(weekly)
    d_macd, d_signal, d_hist = macd(close)
    w_macd, w_signal, w_hist = macd(weekly)

    snapshot = {
        "close": float(close.iloc[-1]),
        "close_date": close.index[-1].date().isoformat(),
        "daily_ma20": float(close.rolling(20).mean().iloc[-1]),
        "daily_ma50": float(close.rolling(50).mean().iloc[-1]),
        "daily_ma200": float(close.rolling(200).mean().iloc[-1]),
        "weekly_ma20": float(weekly.rolling(20).mean().iloc[-1]),
        "weekly_ma50": float(weekly.rolling(50).mean().iloc[-1]),
        "weekly_ma200": float(weekly.rolling(200).mean().iloc[-1]),
        "daily_rsi": float(d_rsi.iloc[-1]),
        "daily_rsi_prev": float(d_rsi.iloc[-2]) if len(d_rsi.dropna()) > 1 else None,
        "weekly_rsi": float(w_rsi.iloc[-1]),
        "weekly_rsi_prev": float(w_rsi.iloc[-2]) if len(w_rsi.dropna()) > 1 else None,
        "daily_macd": float(d_macd.iloc[-1]),
        "daily_signal": float(d_signal.iloc[-1]),
        "daily_hist": float(d_hist.iloc[-1]),
        "daily_hist_prev": float(d_hist.iloc[-2]) if len(d_hist.dropna()) > 1 else None,
        "weekly_macd": float(w_macd.iloc[-1]),
        "weekly_signal": float(w_signal.iloc[-1]),
        "weekly_hist": float(w_hist.iloc[-1]),
        "weekly_hist_prev": float(w_hist.iloc[-2]) if len(w_hist.dropna()) > 1 else None,
    }
    recent = close.tail(7)
    daily_delta = recent.diff().dropna()
    gains = daily_delta.clip(lower=0).sum()
    losses = -daily_delta.clip(upper=0).sum()
    snapshot["daily_ma3"] = float(close.rolling(3).mean().iloc[-1])
    snapshot["daily_ma5"] = float(close.rolling(5).mean().iloc[-1])
    snapshot["daily_ma7"] = float(close.rolling(7).mean().iloc[-1])
    snapshot["daily_rsi6"] = float(100 - 100 / (1 + gains / losses)) if losses > 0 else 100.0
    snapshot["daily_return_7d_pct"] = float((recent.iloc[-1] / recent.iloc[0] - 1) * 100) if len(recent) >= 2 else None
    snapshot["recent_high"] = float(history["High"].tail(7).max()) if "High" in history.columns else None
    snapshot["recent_low"] = float(history["Low"].tail(7).min()) if "Low" in history.columns else None
    if "Volume" in history.columns and history["Volume"].tail(7).notna().sum() >= 3:
        volumes = history["Volume"].tail(7).astype(float)
        snapshot["daily_volume_ratio"] = float(volumes.iloc[-1] / volumes.mean()) if volumes.mean() else None
    else:
        snapshot["daily_volume_ratio"] = None
    snapshot["daily_overlay"] = daily_overlay_from_snapshot(snapshot)
    snapshot["dist_200w"] = snapshot["close"] - snapshot["weekly_ma200"]
    snapshot["dist_200w_pct"] = ((snapshot["close"] / snapshot["weekly_ma200"]) - 1) * 100 if is_number(snapshot["weekly_ma200"]) else None
    snapshot["stage"] = classify_stage(spec, snapshot)
    return snapshot


def advice_for(spec: dict, stage: str) -> str:
    return spec["actions"].get(stage, spec["actions"].get("過渡", "觀察"))


def render_asset_page(spec: dict, snap: dict, report_date: str) -> str:
    daily_state = f"RSI {fmt_num(snap['daily_rsi'], 1)}，{daily_zone(snap['daily_rsi'])}；{macd_text(snap['daily_macd'], snap['daily_signal'], snap['daily_hist'], snap['daily_hist_prev'])}"
    weekly_state = f"RSI {fmt_num(snap['weekly_rsi'], 1)}，{weekly_zone(snap['weekly_rsi'])}；{macd_text(snap['weekly_macd'], snap['weekly_signal'], snap['weekly_hist'], snap['weekly_hist_prev'])}"
    overlay = snap["daily_overlay"]
    advice = advice_for(spec, snap["stage"])
    current_tag = f"**階段：{snap['stage']}**"

    summary_rows = [
        ["最新收盤", f"{fmt_num(snap['close'])}（{snap['close_date']}）", "最新可用收盤價"],
        ["20D / 50D / 200D MA", f"{fmt_num(snap['daily_ma20'])} / {fmt_num(snap['daily_ma50'])} / {fmt_num(snap['daily_ma200'])}", "日線均線位置"],
        ["20W / 50W / 200W MA", f"{fmt_num(snap['weekly_ma20'])} / {fmt_num(snap['weekly_ma50'])} / {fmt_num(snap['weekly_ma200'])}", "週線均線位置"],
        ["距 200W MA", f"{fmt_num(snap['dist_200w'])} 點（{fmt_pct(snap['dist_200w_pct'])}）", "距離長週線的乖離"],
        ["日線 RSI(14)", f"{fmt_num(snap['daily_rsi'], 1)}，{daily_zone(snap['daily_rsi'])}", "短線動能"],
        ["日報短線 overlay", overlay["state"], f"信心：{overlay['confidence']}"],
        ["7 日報酬 / 成交量比", f"{fmt_pct(snap['daily_return_7d_pct'])} / {fmt_num(snap['daily_volume_ratio'], 2)}x", "短線動能與量能；量比為最近 7 日均值比例"],
        ["短線支撐 / 壓力", f"{overlay['support']} / {overlay['resistance']}", "最近 7 日價格區間與均線"],
        ["日線 MACD(12,26,9)", macd_text(snap['daily_macd'], snap['daily_signal'], snap['daily_hist'], snap['daily_hist_prev']), "日線趨勢"],
        ["週線 RSI(14)", f"{fmt_num(snap['weekly_rsi'], 1)}，{weekly_zone(snap['weekly_rsi'])}", "中週期動能"],
        ["週線 MACD(12,26,9)", macd_text(snap['weekly_macd'], snap['weekly_signal'], snap['weekly_hist'], snap['weekly_hist_prev']), "週線趨勢"],
    ]

    stage_md = stage_table(snap["stage"])

    body = f"""---
title: {spec['page_title']}
date: {report_date}
---

# {spec['label']}

<div class="thread-feed">
  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">目前結論</span><span>{spec['label']} / {snap['stage']}</span></div>
    <p>{current_tag}。{advice}。</p>
  </div>

  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">一句話</span><span>{spec['summary']}</span></div>
    <p>{spec['risk']} 是現在最需要看的重點。</p>
  </div>
</div>

## 現況摘要
{table(['項目', '數值', '解讀'], summary_rows)}

## 日線觀察
- {daily_state}
- **日報式短線判斷**：{overlay['state']}；支撐約 {overlay['support']}，壓力約 {overlay['resistance']}。
- 日線目前偏向 {daily_zone(snap['daily_rsi'])} 區，代表短線動能已經有方向，但未必足以單獨當作進場依據。
- 若日線 MACD 柱狀體持續收斂，通常表示短線壓力正在減輕；若擴大，代表還要再等。

## 週線觀察
- {weekly_state}
- 週線更能反映中期趨勢，因此這一段通常比日線更值得當成主要判斷。
- 若週線 RSI 已在超買，或價格遠離 200W MA，代表趨勢雖強，但追價容錯率會明顯下降。

## 階段判讀
{stage_md}

## 實務意思
- **目前階段**：{snap['stage']}
- **對應動作**：{advice}
- **風險重點**：{spec['risk']}
- **我的解讀**：{spec['summary']}
"""
    return body


def render_weekly_index(report_files: list[Path], latest_report: str, latest_stage_rows: list[list[str]]) -> str:
    archives = []
    for path in report_files:
        date = path.stem
        archives.append(f"- [{date} 台灣市場週報]({date}/)")
    archive_text = "\n".join(archives) if archives else "- 尚無報告"

    rows = latest_stage_rows
    summary_table = table(["標的", "階段", "判斷結果"], rows)

    return f"""# 最新週報

<div class="thread-feed">
  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">最新報告</span><span>{latest_report}</span></div>
    <p>這一頁放最近一週的完整內容，並保留歷史歸檔連結。內容採 Threads 風格，先給結論，再往下展開細節。</p>
  </div>
</div>

## 最新一則
- [{latest_report} 台灣市場週報]({latest_report}/)

## 階段摘要
{summary_table}

## 歷史歸檔
{archive_text}

> 未來每週產出的報告都會放在這個資料夾，並以日期命名。
"""


def overall_summary(snaps: dict[str, dict]) -> str:
    stages = [snaps[spec["key"]]["stage"] for spec in ASSETS]
    heat = sum(stage == "過熱" for stage in stages)
    bulls = sum(stage in {"復甦", "牛初"} for stage in stages)
    transitions = sum(stage == "過渡" for stage in stages)

    if heat >= 5:
        return "風險資產整體偏熱，台股與美股核心都已進入高檔區，現階段重點是控節奏而不是追價。"
    if heat >= 3:
        return "市場仍偏多，但多數資產已進入過熱或接近過熱，回檔後再布局會比追高舒服。"
    if bulls >= 3:
        return "風險資產仍有多頭延續力，核心資產可以續投，但仍要留意利率與美元背景。"
    if transitions >= 5:
        return "市場多數資產仍在轉折與整理區，先保留彈性比積極加碼更重要。"
    return "市場結構正在分化，核心資產可續投，但單筆追價的容錯率已經下降。"


def render_homepage(latest_date: str, latest_report: str, snaps: dict[str, dict], latest_daily: str | None = None) -> str:
    top_line = overall_summary(snaps)
    daily_link = f'<p><a href="daily/{latest_daily}/">{latest_daily} 台灣市場日報</a></p>' if latest_daily else "<p>尚無日報</p>"
    latest_cards = f"""<div class=\"card-grid\">
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
    for key in ["btc", "taiex", "sp500", "qqq", "gold", "us10y", "dxy", "vix"]:
        snap = snaps[key]
        asset_cards.append(
            f"""  <div class=\"thread-card thread-connector\">\n    <div class=\"thread-meta\"><span class=\"thread-avatar\"></span><span class=\"thread-badge\">{key.upper() if key != 'us10y' else 'US10Y'}</span><span>{snap['stage']}</span></div>\n    <p>{key.upper() if key != 'us10y' else '美國 10Y'}：{advice_for(next(a for a in ASSETS if a['key']==key), snap['stage'])}</p>\n  </div>"""
        )
    asset_cards_text = "\n".join(asset_cards)

    return f"""# 台灣市場週報

{latest_cards}

## 這裡會看到什麼
<div class="thread-feed">
  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">最新週報</span><span>每週一次的市場階段總結</span></div>
    <p>每週整理市場總結、標的階段、宏觀判讀與行動摘要。</p>
  </div>

  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">標的頁</span><span>BTC / TAIEX / 美股 / 黃金 / 美債 / 美元指數 / VIX</span></div>
    <p>每個標的都有獨立頁面，現在會提供更完整的網頁閱讀版分析。</p>
  </div>

  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">閱讀方式</span><span>先看結論，再看細節</span></div>
    <p>本站優先顯示判斷結果，讓你能快速掃完；完整內容則收在週報頁與個別標的頁。</p>
  </div>
</div>

## 快速入口
- <a href="weekly/{latest_report}/">最新週報：{latest_report} 台灣市場週報</a>
- <a href="weekly/index.md">週報歷史索引</a>

## 最新標的狀態
<div class="thread-feed">
{asset_cards_text}
</div>
"""


def render_daily_report(snaps: dict[str, dict], report_date: str) -> str:
    rows = []
    cards = []
    for spec in ASSETS:
        snap = snaps[spec["key"]]
        overlay = snap["daily_overlay"]
        rows.append([
            spec["label"],
            f"{fmt_num(snap['close'])}（{snap['close_date']}）",
            overlay["state"],
            f"{fmt_pct(snap['daily_return_7d_pct'])}",
            f"{overlay['support']} / {overlay['resistance']}",
            overlay["confidence"],
        ])
        cards.append(
            f"""  <div class=\"thread-card thread-connector\">\n    <div class=\"thread-meta\"><span class=\"thread-avatar\"></span><span class=\"thread-badge\">{spec['label']}</span><span>{overlay['state']}</span></div>\n    <p>收盤 {fmt_num(snap['close'])}；7 日報酬 {fmt_pct(snap['daily_return_7d_pct'])}；支撐 {overlay['support']}，壓力 {overlay['resistance']}。</p>\n  </div>"""
        )
    card_text = "\n".join(cards)
    return f"""---
title: {report_date} 台灣市場日報
date: {report_date}
---

# {report_date} 台灣市場日報

<div class=\"thread-feed\">
  <div class=\"thread-card thread-connector\">
    <div class=\"thread-meta\"><span class=\"thread-avatar\"></span><span class=\"thread-badge\">每日短線總結</span><span>短線市場觀察</span></div>
    <p>先看短線狀態，再回到週期階段。</p>
  </div>
</div>

## 市場短線比較
{table(["標的", "最新收盤", "日報狀態", "7 日報酬", "支撐 / 壓力", "信心"], rows)}

## 個別市場觀察
<div class=\"thread-feed\">
{card_text}
</div>
"""


def render_daily_index_page(report_files: list[Path], latest_report: str) -> str:
    archives = "\n".join([f'<a href="{p.stem}/">{p.stem} 台灣市場日報</a><br>' for p in report_files]) if report_files else "- 尚無報告"
    return f"""# 最新日報

## 最新一則

<a href=\"{latest_report}/\">{latest_report} 台灣市場日報</a>

## 歷史歸檔

{archives}
"""


def render_weekly_report(snaps: dict[str, dict], report_date: str) -> str:
    stage_rows = []
    for spec in ASSETS:
        snap = snaps[spec["key"]]
        daily_state = f"RSI {fmt_num(snap['daily_rsi'], 1)}，{daily_zone(snap['daily_rsi'])}"
        weekly_state = f"RSI {fmt_num(snap['weekly_rsi'], 1)}，{weekly_zone(snap['weekly_rsi'])}"
        stage_rows.append([
            spec["label"],
            snap["stage"],
            f"{fmt_pct(snap['dist_200w_pct'])} / {advice_for(spec, snap['stage'])}",
            f"{snap['daily_overlay']['state']}（信心{snap['daily_overlay']['confidence']}）",
            weekly_state,
            f"{snap['daily_overlay']['support']} / {snap['daily_overlay']['resistance']}",
            spec["risk"],
        ])

    comparison = table(["標的", "週期階段", "與200W MA距離", "日報短線狀態", "週線狀態", "短線支撐 / 壓力", "風險重點"], stage_rows)
    stage_map_rows = [[spec["label"], snaps[spec["key"]]["stage"]] for spec in ASSETS]
    stage_map = table(["標的", "階段"], stage_map_rows)
    summary = overall_summary(snaps)
    flow_assets = ["btc", "sp500", "qqq", "taiex"]
    flow = " → ".join([
        f"{next(spec['label'] for spec in ASSETS if spec['key'] == key)}：{advice_for(next(spec for spec in ASSETS if spec['key'] == key), snaps[key]['stage'])}"
        for key in flow_assets
    ])
    us10y_stage = snaps["us10y"]["stage"]
    dxy_stage = snaps["dxy"]["stage"]
    vix_stage = snaps["vix"]["stage"]
    gold_stage = snaps["gold"]["stage"]
    investable_keys = {"btc", "taiex", "sp500", "qqq", "gold"}
    asset_action_lines = "\n".join(
        [f"- **{spec['label']}**：{snaps[spec['key']]['stage']}，{advice_for(spec, snaps[spec['key']]['stage'])}。" for spec in ASSETS if spec["key"] in investable_keys]
    )
    macro_action_lines = "\n".join(
        [f"- **{spec['label']}**：{snaps[spec['key']]['stage']}，{advice_for(spec, snaps[spec['key']]['stage'])}。" for spec in ASSETS if spec["key"] not in investable_keys]
    )

    asset_cards = []
    for spec in ASSETS:
        snap = snaps[spec["key"]]
        asset_cards.append(
            f"""  <div class=\"thread-card thread-connector\">\n    <div class=\"thread-meta\"><span class=\"thread-avatar\"></span><span class=\"thread-badge\">{spec['label']}</span><span>{snap['stage']}</span></div>\n    <p>{spec['summary']} 目前的判斷是：<strong>{snap['stage']}</strong>，建議動作：<strong>{advice_for(spec, snap['stage'])}</strong>。</p>\n  </div>"""
        )
    asset_cards_text = "\n".join(asset_cards)

    return f"""---
title: {report_date} 台灣市場週報
date: {report_date}
---

# {report_date} 台灣市場週報

<div class="thread-feed">
  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">一句話結論</span><span>先看結論，再看細節</span></div>
    <p>{summary}</p>
  </div>

  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">操作摘要</span><span>新資金怎麼放</span></div>
    <p>{flow}</p>
  </div>
</div>

## 比較表
{comparison}

## 階段映射
{stage_map}

## 宏觀解讀
- **風險資產**：{summary}
- **流動性**：10Y 目前為 {us10y_stage}、DXY 為 {dxy_stage}，資金面仍不是全面寬鬆。
- **通膨 / 折現**：高利率尚未完全退場，對高 beta 與高估值資產仍有壓力。
- **避險需求**：VIX 為 {vix_stage}、黃金為 {gold_stage}，市場還沒進入明顯恐慌，但也沒有特別便宜的避險。

## 個別分析
<div class="thread-feed">
{asset_cards_text}
</div>

## 資產行動摘要
{asset_action_lines}

## 宏觀訊號
{macro_action_lines}
"""


def render_weekly_index_page(report_files: list[Path], latest_report: str, snaps: dict[str, dict]) -> str:
    rows = [[spec["label"], snaps[spec["key"]]["stage"], advice_for(spec, snaps[spec["key"]]["stage"])] for spec in ASSETS]
    stage_summary = table(["標的", "階段", "判斷結果"], rows)
    archives = "\n".join([f'<a href="{p.stem}/">{p.stem} 台灣市場週報</a><br>' for p in report_files]) if report_files else "- 尚無報告"
    return f"""# 最新週報

<div class="thread-feed">
  <div class="thread-card thread-connector">
    <div class="thread-meta"><span class="thread-avatar"></span><span class="thread-badge">最新報告</span><span>{latest_report}</span></div>
    <p>這一頁放最近一週的完整內容，並保留歷史歸檔連結。內容採 Threads 風格，先給結論，再往下展開細節。</p>
  </div>
</div>

## 最新一則
<a href="{latest_report}/">{latest_report} 台灣市場週報</a>

## 階段摘要
{stage_summary}

## 歷史歸檔
{archives}
"""


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public market reports")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="weekly")
    args = parser.parse_args()
    ensure_dirs()

    snapshots: dict[str, dict] = {}
    for spec in ASSETS:
        print(f"[fetch] {spec['label']} ({spec['symbol']})")
        snapshots[spec["key"]] = build_snapshot(spec)
        snapshots[spec["key"]]["report_label"] = spec["label"]

    report_date = TODAY

    for spec in ASSETS:
        snap = snapshots[spec["key"]]
        write(MARKET_DIR / f"{spec['key']}.md", render_asset_page(spec, snap, report_date))

    daily_files = sorted([p for p in DAILY_DIR.glob("*.md") if p.name != "index.md"], reverse=True)
    if args.mode == "daily":
        daily_report_path = DAILY_DIR / f"{report_date}.md"
        write(daily_report_path, render_daily_report(snapshots, report_date))
        daily_files = sorted([p for p in DAILY_DIR.glob("*.md") if p.name != "index.md"], reverse=True)
        write(DAILY_DIR / "index.md", render_daily_index_page(daily_files, report_date))
        weekly_files = sorted([p for p in WEEKLY_DIR.glob("*.md") if p.name != "index.md"], reverse=True)
        latest_weekly = weekly_files[0].stem if weekly_files else report_date
        write(DOCS / "index.md", render_homepage(report_date, latest_weekly, snapshots, report_date))
        print(f"[done] generated {daily_report_path}")
        return

    weekly_report_path = WEEKLY_DIR / f"{report_date}.md"
    write(weekly_report_path, render_weekly_report(snapshots, report_date))
    weekly_files = sorted([p for p in WEEKLY_DIR.glob("*.md") if p.name != "index.md"], reverse=True)
    write(WEEKLY_DIR / "index.md", render_weekly_index_page(weekly_files, report_date, snapshots))
    latest_daily = daily_files[0].stem if daily_files else None
    write(DOCS / "index.md", render_homepage(report_date, report_date, snapshots, latest_daily))
    print(f"[done] generated {weekly_report_path}")


if __name__ == "__main__":
    main()
