from __future__ import annotations

# Shared end-of-day market-data universe.
#
# Keep this broader than the public report universe. Consumers should use the
# stable `key` values and never depend on Yahoo Finance symbols directly.
DATA_ASSETS = [
    # Crypto / cross-asset anchors
    {"key": "btc", "label": "BTC", "symbol": "BTC-USD", "category": "crypto", "required": True, "roles": ["core", "finance", "sar"]},
    {"key": "eth", "label": "ETH", "symbol": "ETH-USD", "category": "crypto", "required": True, "roles": ["finance", "sar"]},

    # Benchmarks / macro
    {"key": "taiex", "label": "TAIEX", "symbol": "^TWII", "category": "benchmark", "required": True, "roles": ["public_report", "stock"]},
    {"key": "sp500", "label": "S&P 500", "symbol": "^GSPC", "category": "benchmark", "required": True, "roles": ["public_report", "macro"]},
    {"key": "nasdaq100", "label": "Nasdaq 100", "symbol": "^NDX", "category": "benchmark", "required": False, "roles": ["stock", "sar"]},
    {"key": "qqq", "label": "QQQ", "symbol": "QQQ", "category": "benchmark_etf", "required": True, "roles": ["public_report", "finance", "sar"]},
    {"key": "gold", "label": "Gold", "symbol": "GC=F", "category": "macro", "required": True, "roles": ["public_report", "macro"]},
    {"key": "silver", "label": "Silver", "symbol": "SI=F", "category": "macro", "required": False, "roles": ["macro"]},
    {"key": "us10y", "label": "US 10Y", "symbol": "^TNX", "category": "macro", "required": True, "roles": ["public_report", "macro"]},
    {"key": "dxy", "label": "DXY", "symbol": "DX-Y.NYB", "category": "macro", "required": True, "roles": ["public_report", "macro"]},
    {"key": "vix", "label": "VIX", "symbol": "^VIX", "category": "macro", "required": True, "roles": ["public_report", "macro", "risk"]},
    {"key": "usd_twd", "label": "USD/TWD", "symbol": "TWD=X", "category": "fx", "required": True, "roles": ["finance", "sar"]},

    # BTC equity proxies / leveraged or income tools
    {"key": "ibit", "label": "IBIT", "symbol": "IBIT", "category": "btc_equity", "required": True, "roles": ["finance", "sar", "position"]},
    {"key": "mstr", "label": "MSTR", "symbol": "MSTR", "category": "btc_equity", "required": True, "roles": ["sar", "rotation"]},
    {"key": "bitu", "label": "BITU", "symbol": "BITU", "category": "btc_leverage", "required": False, "roles": ["sar", "tactical"]},
    {"key": "bitx", "label": "BITX", "symbol": "BITX", "category": "btc_leverage", "required": False, "roles": ["sar", "tactical"]},
    {"key": "btci", "label": "BTCI", "symbol": "BTCI", "category": "btc_income", "required": False, "roles": ["sar", "income"]},

    # Strategy capital-structure instruments
    {"key": "strc", "label": "STRC", "symbol": "STRC", "category": "strategy_security", "required": False, "roles": ["sar", "income"]},
    {"key": "strd", "label": "STRD", "symbol": "STRD", "category": "strategy_security", "required": False, "roles": ["sar", "income"]},
    {"key": "strf", "label": "STRF", "symbol": "STRF", "category": "strategy_security", "required": False, "roles": ["sar", "income"]},
    {"key": "strk", "label": "STRK", "symbol": "STRK", "category": "strategy_security", "required": False, "roles": ["sar", "income"]},

    # Taiwan holdings / recurring portfolio indicators
    {"key": "tw0050", "label": "0050", "symbol": "0050.TW", "category": "tw_etf", "required": True, "roles": ["finance", "sar", "benchmark"]},
    {"key": "tw0056", "label": "0056", "symbol": "0056.TW", "category": "tw_etf", "required": False, "roles": ["finance", "income"]},
    {"key": "tw00713", "label": "00713", "symbol": "00713.TW", "category": "tw_etf", "required": True, "roles": ["finance", "sar", "position"]},
    {"key": "tw00878", "label": "00878", "symbol": "00878.TW", "category": "tw_etf", "required": False, "roles": ["finance", "income"]},
    {"key": "tw00662", "label": "00662", "symbol": "00662.TW", "category": "tw_etf", "required": True, "roles": ["finance", "sar", "position"]},
    {"key": "tw00670l", "label": "00670L", "symbol": "00670L.TW", "category": "tw_leveraged_etf", "required": True, "roles": ["finance", "sar", "position"]},
    {"key": "tw00685l", "label": "00685L", "symbol": "00685L.TW", "category": "tw_leveraged_etf", "required": True, "roles": ["finance", "sar", "position"]},

    # Cash-flow / defensive / special-purpose ETFs used in recurring research
    {"key": "boxx", "label": "BOXX", "symbol": "BOXX", "category": "cash_etf", "required": False, "roles": ["finance", "liquidity"]},
    {"key": "qqqi", "label": "QQQI", "symbol": "QQQI", "category": "income_etf", "required": False, "roles": ["sar", "income"]},
    {"key": "spyi", "label": "SPYI", "symbol": "SPYI", "category": "income_etf", "required": False, "roles": ["sar", "income"]},
    {"key": "spcx", "label": "SPCX", "symbol": "SPCX", "category": "special_etf", "required": False, "roles": ["sar"]},

    # Recurring technology / semiconductor context
    {"key": "nvda", "label": "NVDA", "symbol": "NVDA", "category": "equity", "required": False, "roles": ["sar", "technology"]},
    {"key": "tsm", "label": "TSMC ADR", "symbol": "TSM", "category": "equity", "required": False, "roles": ["sar", "technology"]},
    {"key": "tsla", "label": "TSLA", "symbol": "TSLA", "category": "equity", "required": False, "roles": ["sar", "technology"]},
    {"key": "smh", "label": "SMH", "symbol": "SMH", "category": "sector_etf", "required": False, "roles": ["sar", "semiconductor"]},
]

# Generic relationships useful across reports. These are descriptive market
# statistics only; strategy authorization remains in downstream projects.
RELATIONSHIPS = [
    {"key": "mstr_vs_ibit", "left": "mstr", "right": "ibit", "note": "US-session BTC equity beta proxy"},
    {"key": "mstr_vs_btc", "left": "mstr", "right": "btc", "note": "Calendar-date comparison; BTC trades 24/7"},
    {"key": "bitu_vs_ibit", "left": "bitu", "right": "ibit", "note": "Daily leveraged BTC ETF versus spot ETF proxy"},
    {"key": "bitx_vs_ibit", "left": "bitx", "right": "ibit", "note": "Daily leveraged BTC ETF versus spot ETF proxy"},
    {"key": "tw00670l_vs_tw00662", "left": "tw00670l", "right": "tw00662", "note": "Taiwan-listed leveraged Nasdaq ETF versus 1x Nasdaq ETF"},
    {"key": "tw00685l_vs_tw0050", "left": "tw00685l", "right": "tw0050", "note": "Taiwan-listed leveraged market ETF versus broad-market ETF"},
]


def asset_by_key(key: str) -> dict:
    for asset in DATA_ASSETS:
        if asset["key"] == key:
            return asset
    raise KeyError(key)
