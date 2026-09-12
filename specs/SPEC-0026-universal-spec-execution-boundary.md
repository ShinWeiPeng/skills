---
spec_version: 1
spec_id: SPEC-0026
revision: 4
status: confirmed
change_set: universal-spec-execution-boundary
---

# 所有專案的 SPEC 與執行授權流程

## Problem

任務 01a094ac-579f-7923-9494-ffaa0ff3efb0 在需求討論後直接修改產品程式；後續增加跨分頁 Log 接收需求時也完成修改。既有規則與受控入口存在，但實際工具操作仍可繞過流程。先前本任務只在對話確認規則，未即時提供持久化 SPEC 與連結。

## Solution

在共用 governed-engineering 外掛落實「先建立並確認本次 SPEC，再由使用者明確說開始執行，才進行程式修改」。討論與 SPEC 寫入繼續進行；產品執行獨立判定。重用既有授權綁定與受控入口，補強每輪接續、原始工具紀錄稽核和真實多輪驗收。此規格確認不代表執行授權。

## User Stories

使用者需要所有專案都遵守同一討論、規格與執行流程，不必在各專案另外安裝規則或反覆提醒，且能開啟檢視已確認的 SPEC。

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | 所有新舊專案、語言、新任務與後續對話均使用共用流程；涵蓋新功能、修 bug、重構、測試程式與格式化，不依變更大小豁免。 |
| REQ-002 | 任何程式編寫或修改前，先建立並確認本次變更的 canonical SPEC，再取得使用者明確的「開始執行」。回答選項、確認需求、補充條件、提出方案、逾時或模型自身宣告均不構成授權。 |
| REQ-003 | 授權限定於目前專案、任務、SPEC 與已確認版本；新需求超出範圍時暫停相關修改，更新或建立相關 SPEC，再取得新的開始執行。沿用既有任何 SPEC 修訂使授權失效的規則。範圍與規格不變時持續完成必要實作與驗證，不逐步重問。 |
| REQ-004 | 未授權期間允許唯讀調查、討論及 SPEC 生命週期寫入；不得藉測試、設定、架構文件、格式化、產物生成或建置繞過產品修改限制。停止產品修改不等於停止 SPEC 討論。使用者明確停止全部或 SPEC 寫入時尊重該範圍。 |
| REQ-005 | 每輪恢復目前規格與授權狀態；產品修改前檢查既有受控入口的 admission。拒絕後不得改用直接 patch 或 Shell 寫入。先觀察檢查結果，再選擇依賴操作。 |
| REQ-006 | 稽核原始使用者訊息、工具呼叫順序與檔案變更；直接繞過、舊授權重用、缺失證據均不能以功能測試通過抵銷。發布驗收須包含真實新任務多輪紀錄，不能只以受控入口單元測試替代。 |
| REQ-007 | 每次 SPEC 建立完成或修訂確認後，必須在使用者可見回覆貼出 SPEC 編號、名稱、可點擊連結、本次規格重點或修訂差異、明確授權狀態；不得以檔案寫入、側邊面板或口頭宣告取代。未授權顯示等待開始執行；已取得本次有效授權則明示已授權範圍，不虛稱仍在等待。SPEC 建立無須等待開始執行。 |
| REQ-008 | 明確區分外掛流程控制與宿主硬性攔截；外掛可拒絕受控操作及稽核繞過，但不得宣稱任意工具在宿主層皆不可寫入。缺少真實紀錄或所需能力時報告 BLOCKED，不能宣告驗收完成。 |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | 使用者確認先有 SPEC，再明確說開始執行，才可修改。 |
| DEC-002 | 使用者確認此流程必須適用所有專案；由共用外掛承擔，不要求各專案額外提醒。 |
| DEC-003 | 使用者要求可見的規格連結；立即補建規格，產品執行仍未授權。 |

## Discussion Context

### DISC-001: 執行前提

- **Situation:** 實際對話中需求補充後已完成產品修改。
- **Question:** 共用流程的必要執行條件是什麼？
- **Options and tradeoffs:** SPEC 討論可持續；產品修改另需明確授權，增加一次範圍確認但避免默認開工。
- **User answer:** 就是在任何編寫程式前，都必須要有SPEC的建立，使用者說開始執行，才能進行修改
- **Explicit rationale:** 使用者未另述理由。
- **Resulting impact:** REQ-002, REQ-003, REQ-004, DEC-001.

### DISC-002: 適用範圍

- **Situation:** 需避免此修正僅套用單一 Log 專案。
- **Question:** 流程適用哪些專案？
- **Options and tradeoffs:** 共用外掛統一流程，需跨專案驗收。
- **User answer:** 這是要所有專案都必須的流程。
- **Explicit rationale:** 使用者明確要求所有專案適用。
- **Resulting impact:** REQ-001, REQ-006, DEC-002.

### DISC-003: 規格可見性

- **Situation:** 助理先前只在對話確認，尚未建立可開啟規格。
- **Question:** 缺少的交付內容是什麼？
- **Options and tradeoffs:** 立即補存討論規格並提供連結，不啟動產品修改。
- **User answer:** 我沒有看到規格鏈結
- **Explicit rationale:** 使用者需要看到規格連結。
- **Resulting impact:** REQ-007, DEC-003.

### DISC-004: 每次 SPEC 完成都必須貼出與執行授權

- **Situation:** 規格完成後的可見呈現需要成為所有專案的固定行為。
- **Question:** 是否將本次規格呈現要求一併實作？
- **Options and tradeoffs:** 回覆提供完整規格識別、連結、摘要及正確授權狀態；不靠面板開啟當作已呈現。
- **User answer:** 每次完成SPEC時，必須要SPEC貼出來，不然使用者不知道；隨後明確回覆「開始執行」。
- **Explicit rationale:** 不貼出，使用者不知道規格已完成。
- **Resulting impact:** REQ-007, AC-004. Current execution message: 01a09530-4568-74b1-ab93-1c1542283ab5. This authorizes the just-discussed scope after reconciliation; no unrelated or later changes are covered.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-004 | 新舊 Web、Python、韌體專案提出需求、回答選項及補充條件時，SPEC 可更新，所有產品目標雜湊不變。 | 在隔離專案執行參數化流程測試及真實多輪任務；保存初末檔案清單與 SHA-256、原始訊息、工具紀錄和 SPEC 差異。 | Pending implementation and actual validation. |
| AC-002 | REQ-002, REQ-003, REQ-005 | 當前規格獲開始執行後可修改；舊版本、跨任務、跨專案及新需求不能沿用授權；拒絕後目標不變。 | 擴充 plugins/governed-engineering-skills/tests/test_managed_delivery.py；執行 python -m unittest discover -s plugins/governed-engineering-skills/tests -p test_managed_delivery.py，要求 exit 0 且所有拒絕案例目標雜湊不變。 | Pending implementation and actual validation. |
| AC-003 | REQ-005, REQ-006, REQ-008 | 本次 Log 失敗紀錄、直接寫入繞過、gate 與無條件寫入合併案例均判 FAIL；真實合規授權與修改案例判 PASS；紀錄不足判 BLOCKED。 | 保存原始來源與可核對的事件映射，使用 managed_delivery.py --audit-trace 稽核及補充整合案例；人工核對映射並記錄觀察者、步驟與結果。人工核對用以防止正規化漏記原始事件。 | Pending implementation and actual validation. |
| AC-004 | REQ-004, REQ-007 | 每次 SPEC 完成時回覆包含編號、名稱、可開啟連結、非空重點或差異與真實授權狀態；只開面板、只有檔名、舊版本連結或未貼摘要不得通過；停止產品修改後繼續討論仍更新 SPEC，不修改產品。 | 檢查 Markdown 呈現、檔案連結、spec_contract.py validate 與新任務暫停後補充需求的原始回覆及差異。 | Pending implementation and actual validation. |
| AC-005 | REQ-001, REQ-006, REQ-008 | 發布候選使用共用原始碼與同步文件；在實際候選版本完成多輪矩陣，個別報告腳本與模型證據，不以建置代替行為驗收。 | 執行候選組裝與 distribution 驗證，保存版本與雜湊；在新任務重現提出需求、確認、開始執行、補充新需求、再次開始執行；必要證據全部具備且各案通過才整體 PASS。 | Pending implementation and actual validation. |

## Relationships

- depends_on: none
- refines: SPEC-0022, SPEC-0020
- conflicts_with: none
- supersedes: none

## Out of Scope

本次規格建立不授權產品程式、測試、設定、架構產物、Git、安装、發布或裝置修改。不修改 Log 專案，不直接編輯外掛安裝快取，不新增使用者全域或逐專案 AGENTS.md。宿主層任意工具硬性攔截不在本外掛實作承諾內。

## Open Decisions

None.

## Routing/Gates

本變更接續共用治理流程；先保留真實失敗案例，補驗收，再整合每輪狀態、受控入口與稽核，同步文件，最後驗證實際候選版本。重用現有模組，若實作設計涉及架構變更，依既有架構檢查處理。產品 execution authorization:[REDACTED: credential]

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-12 | 補存本任務已確認需求、全專案適用範圍、規格連結要求及待執行驗收；未授權產品修改。 |
| 3 | 2026-09-12 | Reopened before clarification: Persist user requirement to present every completed SPEC in the reply, and latest explicit execution instruction covering the discussed change. |

