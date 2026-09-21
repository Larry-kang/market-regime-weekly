import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.generate_site import save_cached_history
from scripts.market_snapshot import build_market_snapshot, write_market_snapshot


class MarketSnapshotTests(unittest.TestCase):
    def _history(self, start: float, periods: int = 120) -> pd.DataFrame:
        index = pd.date_range("2026-01-01", periods=periods, freq="D")
        close = pd.Series([start + i * 0.5 for i in range(periods)], index=index)
        return pd.DataFrame(
            {
                "Open": close - 0.2,
                "High": close + 1.0,
                "Low": close - 1.0,
                "Close": close,
                "Volume": [1000] * periods,
            },
            index=index,
        )

    def test_snapshot_contains_assets_and_relationships_without_nan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            save_cached_history("BTC-USD", self._history(80000), cache_dir=cache_dir)
            save_cached_history("IBIT", self._history(45), cache_dir=cache_dir)
            save_cached_history("MSTR", self._history(130), cache_dir=cache_dir)

            payload = build_market_snapshot(
                cache_dir=cache_dir,
                generated_at="2026-09-21T10:00:00+08:00",
            )

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["assets"]["mstr"]["status"], "ok")
        self.assertEqual(payload["assets"]["bitu"]["status"], "missing")
        self.assertEqual(payload["relationships"]["mstr_vs_ibit"]["status"], "ok")
        json.dumps(payload, allow_nan=False)

    def test_snapshot_can_be_written_to_custom_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "cache"
            cache_dir.mkdir()
            save_cached_history("BTC-USD", self._history(80000), cache_dir=cache_dir)
            output = root / "latest.json"
            write_market_snapshot(output_path=output, cache_dir=cache_dir)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("btc", payload["assets"])


if __name__ == "__main__":
    unittest.main()
