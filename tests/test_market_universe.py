import unittest

from scripts.generate_site import ASSETS
from scripts.market_universe import DATA_ASSETS, RELATIONSHIPS


class MarketUniverseTests(unittest.TestCase):
    def test_keys_and_symbols_are_unique(self):
        keys = [asset["key"] for asset in DATA_ASSETS]
        symbols = [asset["symbol"] for asset in DATA_ASSETS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(symbols), len(set(symbols)))
        self.assertGreaterEqual(len(DATA_ASSETS), 30)

    def test_public_report_universe_is_subset_of_data_hub(self):
        hub_symbols = {asset["symbol"] for asset in DATA_ASSETS}
        for asset in ASSETS:
            self.assertIn(asset["symbol"], hub_symbols)

    def test_relationship_keys_reference_known_assets(self):
        keys = {asset["key"] for asset in DATA_ASSETS}
        for relationship in RELATIONSHIPS:
            self.assertIn(relationship["left"], keys)
            self.assertIn(relationship["right"], keys)


if __name__ == "__main__":
    unittest.main()
