from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .generate_site import ASSETS, HISTORY_DIR, _cache_path, fetch_market_history
except ImportError:  # pragma: no cover - direct script execution
    from generate_site import ASSETS, HISTORY_DIR, _cache_path, fetch_market_history


def update_market_data(
    cache_dir: Path = HISTORY_DIR,
    full_rebuild: bool = False,
) -> list[tuple[str, int, str]]:
    """Refresh all configured market-history files without generating reports."""
    updated: list[tuple[str, int, str]] = []
    cache_dir.mkdir(parents=True, exist_ok=True)

    for spec in ASSETS:
        symbol = spec["symbol"]
        path = _cache_path(symbol, cache_dir=cache_dir)
        if full_rebuild and path.exists():
            path.unlink()

        print(f"[update] {spec['label']} ({symbol})")
        history = fetch_market_history(symbol, cache_dir=cache_dir)
        latest = history.index[-1].date().isoformat()
        updated.append((symbol, len(history), latest))
        print(f"[ok] {symbol}: rows={len(history)}, latest={latest}")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Update durable market-history data")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Discard existing cached files and download the full configured history",
    )
    args = parser.parse_args()
    update_market_data(full_rebuild=args.full_rebuild)


if __name__ == "__main__":
    main()
