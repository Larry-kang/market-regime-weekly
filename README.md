# market-regime-weekly

公開版市場週報網站，使用繁體中文產出週期階段與短線 daily overlay。

網站：<https://larry-kang.github.io/market-regime-weekly/>

## 公開範圍

本 repo 只處理公開市場資訊，資料與報告均來自公開市場行情及公開資料來源。

## 目前資料來源

`python scripts/generate_site.py` 使用 `yfinance` 從 Yahoo Finance 公開行情介面取得最近 10 年日資料。歷史資料會保存在 `data/market_history/`，作為可重現的本地基準；後續執行只會重新抓取最近 45 天並合併校正，避免每次重複下載完整歷史。GitHub Actions 同時使用 pip 與市場歷史資料 cache 加速執行，但 cache 被淘汰時仍可由 repo 內資料正常重建。

| 標的 | Ticker | 用途 |
|---|---|---|
| BTC | `BTC-USD` | Bitcoin 現貨價格代理 |
| TAIEX | `^TWII` | 台灣加權指數 |
| S&P 500 | `^GSPC` | 美國主要基準 |
| QQQ | `QQQ` | 可交易的高 beta 成長 ETF |
| 黃金 | `GC=F` | 黃金期貨代理 |
| 美國 10Y | `^TNX` | 美國十年期殖利率代理 |
| DXY | `DX-Y.NYB` | 美元指數代理 |
| VIX | `^VIX` | 波動率指數 |

Yahoo Finance 是資料分發來源；不同標的可能有交易所延遲、休市、代理商品與資料缺漏限制，報告會保留 `N/A` 或標示限制，不手動填造資料。

## 判斷邏輯

每個標的同時提供兩層公開訊號：

1. **週期階段**：20／50／200 日與週均線、RSI(14)、MACD、距離 200W 均線，用於熊底／過渡／復甦／牛初／過熱分類。
2. **日報式短線 overlay**：最近 7 日報酬、3／5／7 日均線、短樣本 RSI(6)、最近 7 日高低區間、成交量相對 7 日均值、短線支撐／壓力與資料限制。

短線 overlay 是輔助層，不會覆蓋週期階段；例如同一標的可以同時呈現「週期階段：復甦」與「日線：偏多震盪／接近壓力」。

## 報告產出與部署

- **日報**：每週一至週五台灣時間約 14:05 產出 `docs/daily/YYYY-MM-DD.md`，以各市場最近可取得的公開收盤資料為準。
- **週報**：每週一台灣時間約 09:05 產出 `docs/weekly/YYYY-MM-DD.md`。
- 兩個 workflow 共用 concurrency，避免同時 commit／push 造成衝突。
- GitHub Pages 會在文件 push 後自動建置發布；兩者都保留 `workflow_dispatch` 手動執行入口。

## 本地驗證

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_site.py --mode weekly
python scripts/validate_generated_site.py
python scripts/generate_site.py --mode daily
python scripts/validate_generated_site.py "$(TZ=Asia/Taipei date +%F)" . daily
mkdocs build --strict
```

## 部署

GitHub Actions 每週一台灣時間約 09:05 產生週報，並由 Pages workflow 建置發布；也保留 `workflow_dispatch` 手動執行入口。
