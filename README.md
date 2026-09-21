# market-regime-weekly

公開市場週報與共用 Market Data Hub。

網站：<https://larry-kang.github.io/market-regime-weekly/>

本 repo 有兩個明確責任：

1. **Market Data Hub**：定時保存多資產日線歷史與機器可讀的最新市場快照，供 SAR、Finance 衍生報表與其他專案重用。
2. **Public Market Report**：維持精簡的公開週報／日報，只呈現少數核心市場，不因 Data Hub 擴充而無限增加頁面。

即時階段以首頁與標的頁為準；週報檔與週報索引是當週產出時的快照，不會被日報覆寫。

## 公開範圍

本 repo 只處理公開市場資訊，資料與報告均來自公開市場行情及公開資料來源。私人持倉、借款、LTV、現金等 Current State 不應寫入本 repo。

## Market Data Hub

### 資料來源與保存

`python scripts/update_market_data.py` 使用 `yfinance` 從 Yahoo Finance 公開行情介面更新日線資料。

- 首次加入標的：下載最多最近 10 年可取得歷史。
- 已有 cache：只重抓最近 45 天並合併校正。
- 新上市產品不再要求至少 1,000 筆歷史才可增量更新；只要已有完整 cache，後續即走增量模式。
- 歷史資料保存於 `data/market_history/`。
- `--full-rebuild` 僅用於 cache 修復或重新建置。
- 每個標的保留自己的 `latest_date`，不得把休市或延遲資料冒充成即時資料。

### 機器可讀資料契約

更新成功後會發布：

- `docs/data/latest.json`：最新價格、1/7/20 日報酬、20/50/200 日均線、RSI(14)、20 日高點與回撤，以及共用 cross-asset beta / correlation。
- `docs/data/universe.json`：Data Universe 與 relationship registry。

GitHub Pages 對應固定路徑：

- `/data/latest.json`
- `/data/universe.json`

下游專案應優先依穩定的 `key` 取值，不要直接依 Yahoo Finance symbol 寫死商業邏輯。任何策略 Authority、持倉、LTV 或買賣決策仍由下游專案負責；Data Hub 只提供描述性市場資料。

### Data Universe

目前共 36 個共享標的。這個清單刻意比公開報表大，但不等同 SAR 的完整 deep-dive universe。

| 類別 | 標的 |
|---|---|
| Crypto | `BTC-USD`, `ETH-USD` |
| 市場基準 | `^TWII`, `^GSPC`, `^NDX`, `QQQ` |
| Macro / FX | `GC=F`, `SI=F`, `^TNX`, `DX-Y.NYB`, `^VIX`, `TWD=X` |
| BTC 股票代理／槓桿／收益 | `IBIT`, `MSTR`, `BITU`, `BITX`, `BTCI` |
| Strategy 資本結構 | `STRC`, `STRD`, `STRF`, `STRK` |
| 台股與目前策略標的 | `0050.TW`, `0056.TW`, `00713.TW`, `00878.TW`, `00662.TW`, `00670L.TW`, `00685L.TW` |
| 現金流／防禦／特殊 ETF | `BOXX`, `QQQI`, `SPYI`, `SPCX` |
| 科技／半導體脈絡 | `NVDA`, `TSM`, `TSLA`, `SMH` |

其中 `required=true` 的核心市場、目前持倉與主要策略資料若抓取失敗，更新 workflow 會 fail closed；較新的候選工具屬 optional，單一來源暫時缺失時不阻塞整個 Hub，並由快照中的 freshness / status 反映。

### Cross-asset relationship

`latest.json` 目前集中計算：

- MSTR vs IBIT：30/90 日 beta、correlation、20 日相對報酬。
- MSTR vs BTC：日曆日期對齊的描述性比較；BTC 為 24/7 市場，使用時必須保留這個限制。
- BITU / BITX vs IBIT：監測 daily-leverage 實際 beta 漂移。
- 00670L vs 00662：同市場的 Nasdaq 2x / 1x 代理比較。
- 00685L vs 0050：同市場的台股 2x / 1x 代理比較。

這些統計只描述市場關係，不直接授權槓桿或輪動。

## Public Report Universe

公開網站維持原本 8 個核心市場：

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

Data Universe 的增加不會自動增加公開標的頁。

## 判斷邏輯

公開報表中的每個標的同時提供兩層訊號：

1. **週期階段**：20／50／200 日與週均線、RSI(14)、MACD、距離 200W 均線，用於熊底／過渡／復甦／牛初／過熱分類。
2. **日報式短線 overlay**：最近 7 日報酬、3／5／7 日均線、短樣本 RSI(6)、最近 7 日高低區間、成交量相對 7 日均值、短線支撐／壓力與資料限制。

短線 overlay 是輔助層，不會覆蓋週期階段。

## 排程與部署

- **08:20 台灣時間，每日**：更新 BTC、Crypto 與前一個美股交易日資料；也讓週一 09:05 週報可使用較新的資料。
- **13:50 台灣時間，週一至週五**：台股收盤後再次刷新整個 Data Hub。
- **14:10 台灣時間，週一至週五**：使用 repo 內 cache 產生公開日報，不再由每次 data refresh 觸發。
- **每週一 09:05 台灣時間**：產生公開週報。
- 價格更新、日報與週報均保留 `workflow_dispatch`。
- GitHub Pages 會在資料或文件 push 後自動建置發布。

Yahoo Finance 是資料分發來源；不同標的可能有交易所延遲、休市、代理商品與資料缺漏限制。資料層保留 `status`、`latest_date` 與 `generated_at`，下游必須檢查 freshness，不得把 stale value 當即時值。

## 本地驗證

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/update_market_data.py
python scripts/generate_site.py --mode weekly --cached-only
python scripts/validate_generated_site.py
python scripts/generate_site.py --mode daily --cached-only
python scripts/validate_generated_site.py "$(TZ=Asia/Taipei date +%F)" . daily
mkdocs build --strict
```

## 部署

所有自動產物均由 GitHub Actions 產生並 commit。Data Hub 與報表 generation 已解耦，讓其他專案能只依賴市場資料，不必觸發或解析公開報表。
