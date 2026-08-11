import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.update_market_data import update_market_data


class MarketDataUpdaterTests(unittest.TestCase):
    @patch("scripts.update_market_data.ASSETS", [{"label": "Test", "symbol": "TEST"}])
    @patch("scripts.update_market_data.fetch_market_history")
    def test_updates_data_only_and_returns_summary(self, fetch_history):
        index = pd.date_range("2025-01-01", periods=3, freq="D")
        fetch_history.return_value = pd.DataFrame(
            {"Close": [1.0, 2.0, 3.0]}, index=index
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            summary = update_market_data(cache_dir=Path(temp_dir))

        self.assertEqual(summary, [("TEST", 3, "2025-01-03")])
        fetch_history.assert_called_once_with("TEST", cache_dir=Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
