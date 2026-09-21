import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.update_market_data import update_market_data


class MarketDataUpdaterTests(unittest.TestCase):
    @patch(
        "scripts.update_market_data.DATA_ASSETS",
        [{"label": "Test", "symbol": "TEST", "required": True}],
    )
    @patch("scripts.update_market_data.refresh_market_history")
    def test_updates_data_only_and_returns_summary(self, refresh_history):
        index = pd.date_range("2025-01-01", periods=3, freq="D")
        refresh_history.return_value = pd.DataFrame(
            {"Close": [1.0, 2.0, 3.0]}, index=index
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            summary = update_market_data(cache_dir=cache_dir)

        self.assertEqual(summary, [("TEST", 3, "2025-01-03")])
        refresh_history.assert_called_once_with(
            "TEST",
            cache_dir=cache_dir,
            full_rebuild=False,
        )

    @patch(
        "scripts.update_market_data.DATA_ASSETS",
        [{"label": "Optional", "symbol": "OPT", "required": False}],
    )
    @patch("scripts.update_market_data.refresh_market_history")
    def test_optional_asset_failure_does_not_block_hub(self, refresh_history):
        refresh_history.side_effect = RuntimeError("not listed yet")
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = update_market_data(cache_dir=Path(temp_dir))
        self.assertEqual(summary, [])

    @patch(
        "scripts.update_market_data.DATA_ASSETS",
        [{"label": "Required", "symbol": "REQ", "required": True}],
    )
    @patch("scripts.update_market_data.refresh_market_history")
    def test_required_asset_failure_blocks_publish(self, refresh_history):
        refresh_history.side_effect = RuntimeError("source unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "REQ"):
                update_market_data(cache_dir=Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
