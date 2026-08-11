import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.generate_site import (
    cache_has_sufficient_history,
    fetch_market_history,
    load_cached_history,
    save_cached_history,
)


class HistoryCacheTests(unittest.TestCase):
    def make_history(self, periods=2000):
        index = pd.date_range("2018-01-01", periods=periods, freq="D")
        return pd.DataFrame(
            {
                "Open": range(periods),
                "High": range(periods),
                "Low": range(periods),
                "Close": [float(value) + 1 for value in range(periods)],
                "Volume": [100] * periods,
            },
            index=index,
        )

    def test_cache_round_trip_preserves_market_history(self):
        history = self.make_history()
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            save_cached_history("TEST", history, cache_dir=cache_dir)
            loaded = load_cached_history("TEST", cache_dir=cache_dir)

        pd.testing.assert_frame_equal(loaded, history, check_freq=False)

    def test_short_cache_is_not_considered_sufficient(self):
        short_history = self.make_history(periods=100)
        self.assertFalse(cache_has_sufficient_history(short_history))
        self.assertTrue(cache_has_sufficient_history(self.make_history()))

    @patch("scripts.generate_site.yf.Ticker")
    def test_existing_cache_fetches_recent_overlap_and_merges(self, ticker_factory):
        cached = self.make_history()
        fresh_index = pd.date_range(cached.index[-1] - pd.Timedelta(days=45), periods=50, freq="D")
        fresh = pd.DataFrame(
            {
                "Open": [10] * len(fresh_index),
                "High": [11] * len(fresh_index),
                "Low": [9] * len(fresh_index),
                "Close": [12.0] * len(fresh_index),
                "Volume": [200] * len(fresh_index),
            },
            index=fresh_index,
        )
        ticker_factory.return_value.history.return_value = fresh

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            save_cached_history("TEST", cached, cache_dir=cache_dir)
            result = fetch_market_history("TEST", cache_dir=cache_dir)

        call_kwargs = ticker_factory.return_value.history.call_args.kwargs
        self.assertIn("start", call_kwargs)
        self.assertNotIn("period", call_kwargs)
        self.assertEqual(result.loc[fresh_index[-1], "Close"], 12.0)
        self.assertGreater(len(result), len(cached))


if __name__ == "__main__":
    unittest.main()
