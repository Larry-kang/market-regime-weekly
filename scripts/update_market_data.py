from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .generate_site import (
        CACHE_LOOKBACK_DAYS,
        HISTORY_DIR,
        TZ,
        _cache_path,
        _download_market_history,
        _normalize_history,
        load_cached_history,
        save_cached_history,
    )
    from .market_snapshot import write_market_snapshot, write_universe_manifest
    from .market_universe import DATA_ASSETS
except ImportError:  # pragma: no cover - direct script execution
    from generate_site import (
        CACHE_LOOKBACK_DAYS,
        HISTORY_DIR,
        TZ,
        _cache_path,
        _download_market_history,
        _normalize_history,
        load_cached_history,
        save_cached_history,
    )
    from market_snapshot import write_market_snapshot, write_universe_manifest
    from market_universe import DATA_ASSETS


def refresh_market_history(
    symbol: str,
    cache_dir: Path = HISTORY_DIR,
    full_rebuild: bool = False,
    period: str = "10y",
    retries: int = 3,
    cache_lookback_days: int = CACHE_LOOKBACK_DAYS,
):
    """Refresh one daily history cache.

    Any non-empty cache is refreshed incrementally. This is intentional: newer
    products such as IBIT/BITU/Strategy preferred securities cannot satisfy the
    legacy 1,000-row history threshold even when their cache already contains
    their full listed history. Use --full-rebuild when a cache needs repair.
    """
    path = _cache_path(symbol, cache_dir=cache_dir)
    if full_rebuild and path.exists():
        path.unlink()

    cached = load_cached_history(symbol, cache_dir=cache_dir)
    if cached.empty:
        fresh = _download_market_history(symbol, period=period, retries=retries)
    else:
        start = cached.index[-1] - timedelta(days=cache_lookback_days)
        end = datetime.now(TZ).date() + timedelta(days=1)
        fresh = _download_market_history(
            symbol,
            period=period,
            retries=retries,
            start=start.date().isoformat(),
            end=end.isoformat(),
        )

    combined = _normalize_history(
        __import__("pandas").concat([cached, fresh])
    )
    save_cached_history(symbol, combined, cache_dir=cache_dir)
    return combined


def update_market_data(
    cache_dir: Path = HISTORY_DIR,
    full_rebuild: bool = False,
) -> list[tuple[str, int, str]]:
    """Refresh the shared data universe without generating public reports."""
    updated: list[tuple[str, int, str]] = []
    required_failures: list[str] = []
    cache_dir.mkdir(parents=True, exist_ok=True)

    for spec in DATA_ASSETS:
        symbol = spec["symbol"]
        try:
            print(f"[update] {spec['label']} ({symbol})")
            history = refresh_market_history(
                symbol,
                cache_dir=cache_dir,
                full_rebuild=full_rebuild,
            )
            latest = history.index[-1].date().isoformat()
            updated.append((symbol, len(history), latest))
            print(f"[ok] {symbol}: rows={len(history)}, latest={latest}")
        except Exception as exc:
            level = "required" if spec.get("required", False) else "optional"
            print(f"[warning] {symbol} ({level}) update failed: {exc}")
            if spec.get("required", False):
                required_failures.append(f"{symbol}: {exc}")

    if required_failures:
        joined = "; ".join(required_failures)
        raise RuntimeError(f"Required market data update failed: {joined}")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Update shared durable market data")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Discard existing history and download full available history",
    )
    args = parser.parse_args()
    update_market_data(full_rebuild=args.full_rebuild)
    snapshot = write_market_snapshot()
    universe = write_universe_manifest()
    print(f"[publish] snapshot={snapshot}")
    print(f"[publish] universe={universe}")


if __name__ == "__main__":
    main()
