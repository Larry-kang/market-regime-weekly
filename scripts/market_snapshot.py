from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from .generate_site import HISTORY_DIR, TZ, load_cached_history, rsi
    from .market_universe import DATA_ASSETS, RELATIONSHIPS, asset_by_key
except ImportError:  # pragma: no cover - direct script execution
    from generate_site import HISTORY_DIR, TZ, load_cached_history, rsi
    from market_universe import DATA_ASSETS, RELATIONSHIPS, asset_by_key

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = ROOT / "docs" / "data"
LATEST_SNAPSHOT_PATH = PUBLIC_DATA_DIR / "latest.json"
UNIVERSE_PATH = PUBLIC_DATA_DIR / "universe.json"
SCHEMA_VERSION = 1


def _finite(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _pct_change(close: pd.Series, observations: int) -> float | None:
    if len(close) <= observations:
        return None
    base = float(close.iloc[-(observations + 1)])
    current = float(close.iloc[-1])
    if base == 0:
        return None
    return (current / base - 1.0) * 100.0


def _asset_snapshot(spec: dict, cache_dir: Path) -> dict:
    history = load_cached_history(spec["symbol"], cache_dir=cache_dir)
    base = {
        "key": spec["key"],
        "label": spec["label"],
        "symbol": spec["symbol"],
        "category": spec["category"],
        "required": bool(spec.get("required", False)),
        "roles": spec.get("roles", []),
    }
    if history.empty:
        return {**base, "status": "missing"}

    close = history["Close"].astype(float)
    latest = float(close.iloc[-1])
    high_source = history["High"].astype(float) if "High" in history.columns else close
    high_20d = float(high_source.tail(20).max()) if len(high_source) else None
    latest_rsi = rsi(close, 14).iloc[-1] if len(close) >= 15 else None

    result = {
        **base,
        "status": "ok",
        "latest_date": history.index[-1].date().isoformat(),
        "rows": int(len(history)),
        "close": latest,
        "previous_close": float(close.iloc[-2]) if len(close) >= 2 else None,
        "return_1d_pct": _pct_change(close, 1),
        "return_7d_pct": _pct_change(close, 7),
        "return_20d_pct": _pct_change(close, 20),
        "sma20": float(close.tail(20).mean()) if len(close) >= 20 else None,
        "sma50": float(close.tail(50).mean()) if len(close) >= 50 else None,
        "sma200": float(close.tail(200).mean()) if len(close) >= 200 else None,
        "rsi14": _finite(latest_rsi),
        "high_20d": high_20d,
        "drawdown_from_20d_high_pct": (
            (latest / high_20d - 1.0) * 100.0 if high_20d and high_20d > 0 else None
        ),
        "volume": (
            _finite(history["Volume"].iloc[-1])
            if "Volume" in history.columns and len(history)
            else None
        ),
    }
    return {key: _finite(value) if isinstance(value, float) else value for key, value in result.items()}


def _relationship_snapshot(spec: dict, cache_dir: Path) -> dict:
    left_spec = asset_by_key(spec["left"])
    right_spec = asset_by_key(spec["right"])
    left = load_cached_history(left_spec["symbol"], cache_dir=cache_dir)
    right = load_cached_history(right_spec["symbol"], cache_dir=cache_dir)

    base = {
        "key": spec["key"],
        "left": spec["left"],
        "right": spec["right"],
        "note": spec.get("note"),
    }
    if left.empty or right.empty:
        return {**base, "status": "missing"}

    aligned = pd.concat(
        [
            left["Close"].astype(float).rename("left"),
            right["Close"].astype(float).rename("right"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    if len(aligned) < 3:
        return {**base, "status": "insufficient_history", "observations": int(len(aligned))}

    returns = aligned.pct_change(fill_method=None).dropna()

    def window_metrics(window: int) -> tuple[float | None, float | None, int]:
        sample = returns.tail(window)
        if len(sample) < 3:
            return None, None, int(len(sample))
        variance = float(sample["right"].var())
        beta = float(sample["left"].cov(sample["right"]) / variance) if variance > 0 else None
        corr = float(sample["left"].corr(sample["right"]))
        return _finite(beta), _finite(corr), int(len(sample))

    beta_30, corr_30, obs_30 = window_metrics(30)
    beta_90, corr_90, obs_90 = window_metrics(90)

    common_20 = aligned.tail(21)
    relative_20 = None
    if len(common_20) >= 2:
        left_return = float(common_20["left"].iloc[-1] / common_20["left"].iloc[0] - 1.0)
        right_return = float(common_20["right"].iloc[-1] / common_20["right"].iloc[0] - 1.0)
        relative_20 = (left_return - right_return) * 100.0

    return {
        **base,
        "status": "ok",
        "latest_common_date": aligned.index[-1].date().isoformat(),
        "beta_30d": beta_30,
        "correlation_30d": corr_30,
        "observations_30d": obs_30,
        "beta_90d": beta_90,
        "correlation_90d": corr_90,
        "observations_90d": obs_90,
        "relative_return_20d_pct": _finite(relative_20),
    }


def build_market_snapshot(
    cache_dir: Path = HISTORY_DIR,
    generated_at: str | None = None,
) -> dict:
    timestamp = generated_at or datetime.now(TZ).isoformat(timespec="seconds")
    assets = {spec["key"]: _asset_snapshot(spec, cache_dir) for spec in DATA_ASSETS}
    relationships = {
        spec["key"]: _relationship_snapshot(spec, cache_dir)
        for spec in RELATIONSHIPS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "source": "Yahoo Finance via yfinance; repository-cached daily bars",
        "assets": assets,
        "relationships": relationships,
    }


def write_market_snapshot(
    output_path: Path = LATEST_SNAPSHOT_PATH,
    cache_dir: Path = HISTORY_DIR,
) -> Path:
    payload = build_market_snapshot(cache_dir=cache_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_universe_manifest(output_path: Path = UNIVERSE_PATH) -> Path:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "assets": DATA_ASSETS,
        "relationships": RELATIONSHIPS,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output_path
