# 去識別化與公開範圍

這個網站只放**公開版**內容，目的在於提供台灣讀者閱讀的每週市場觀察。

## 不會放在這個專案的內容
- 個人資金配置
- 借貸細節
- 私有交易規則
- 未公開的持倉資訊
- 任何可直接辨識個人的紀錄

## 公開版保留內容
- 市場階段判斷
- 標的相對位置與趨勢
- 每週觀察摘要
- 一般性的現金流 / 部位配置原則

## 呈現原則
- 用繁體中文撰寫
- 優先顯示「判斷結果」而不是完整過程
- 階段分類表只保留最終結論
- 若資料不足，直接標示 N/A

## GitHub branch protection 清單

如果這個 repo 是公開的，建議把 `main` 分支設成 *protected branch*，這樣可以明確降低「別人亂改」的風險：

- [ ] **Require a pull request before merging**
- [ ] **Require at least 1 review approval**
- [ ] **Dismiss stale approvals when new commits are pushed**
- [ ] **Require status checks to pass before merging**
- [ ] **Require branches to be up to date before merging**
- [ ] **Restrict who can push to matching branches**
- [ ] **Block force pushes**
- [ ] **Block branch deletions**
- [ ] **Only allow GitHub Actions / Pages workflow to publish site output**
- [ ] **Limit write access to trusted collaborators only**

## 驗證重點

- 不是每個人都能直接改 `main`
- 任何變更都應先經過 PR
- PR 需要 review 與 CI / build 通過
- GitHub Pages 的發佈來源只保留自動化 workflow

## 目的
把每週的市場報告做成可閱讀、可追蹤、可公開分享的靜態頁面。