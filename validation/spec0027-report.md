# SPEC-0027 驗證紀錄

日期：2026-09-16。驗收對象為 confirmed revision 3；完成狀態轉換另由 SPEC lifecycle 記錄。

## 已實作

- 修改既有技能及內部工具，未新增 skill。入口重新讀取專案政策、SPEC 與驗證映射，合併必要關卡。
- 驗證計畫綁定 SPEC、政策、技能及裝置 profile；相關輸入變動使舊證據失效。
- 分開規劃、enablement、acceptance 與 release；最終證據缺漏不阻止產生證據所需的授權工作。
- managed completion 與 SPEC PASS/implemented 更新共用驗證；缺漏、過期或低層替代證據均不接受。
- 保留原有層級選擇與 FAIL > BLOCKED > PASS；需要硬體驗證的專案不因簡短指令而被降級。

## 執行結果

使用 Windows Python 3.12.14；本輪未在 Linux 或實體硬體執行。

| 檢查 | 結果 | 原始紀錄 |
|---|---|---|
| verification-ladder unittest discover | PASS，29 tests | [ladder](spec0027/ladder.log) |
| plugins/governed-engineering-skills/tests unittest discover | PASS，271 tests | [plugin tests](spec0027/plugin-tests.log) |
| scripts/validate_distribution.py | PASS | [distribution](spec0027/distribution.log) |
| assembled scripts/validate_integration.py | PASS，30 skills | [integration](spec0027/integration.log) |
| architecture development gate | PASS；既有 SHOULD 警告 | [development](spec0027/development.log) |
| architecture release gate | PASS；既有 SHOULD 警告，無 MUST 阻擋 | [release gate](spec0027/release-gate.log) |
| Ruff format --check，8 個變更 Python 檔 | PASS | 本輪命令輸出：8 files already formatted |
| git diff --check | PASS | 本輪命令 exit 0、無輸出 |
| Standards / Spec 雙軸審查 | PASS | 下方審查紀錄 |

完整套件回歸須從 source plugins 測試入口執行。一次誤用 dist 測試入口，使 source-only fingerprint 測試失敗；改回既有 source 入口後 271 項全通過，未修改該測試。組裝產物另由 integration validator 驗證。

## AC 對照

| AC | 證據 |
|---|---|
| AC-001 | git diff 與執行紀錄：僅技能 repo；未操作韌體、硬體、安裝或發布 |
| AC-002 | 實際 production router 對開始執行／繼續／重新載入技能的短指令回歸 |
| AC-003 | required policy 缺 matrix、未知 claim、缺 AC 映射阻擋與 host-only 正向回歸 |
| AC-004 | SPEC/policy/profile/build 綁定、reload 不變與輸入变動失效回歸 |
| AC-005 | planning/enablement 可進行、缺最終 HIL 驗收阻擋、不授予 device 權限回歸 |
| AC-006 | host/smoke/partial/stale/profile/build/artifact 阻擋、完整證據 PASS、FAIL 優先序與 managed completion |
| AC-007 | 實際 reconcile/materialize/implemented、confirmed evidence-only 更新與 direct CLI 阻擋回歸 |
| AC-008 | legacy host 相容性、schema/runtime、29 + 271 tests、架構、格式、雙軸審查與 distribution/integration |

本次修改屬 host 治理工具，所有 AC 使用 module-contract / SIL；未宣稱目標時間、實體整合或硬體性能，因此不需為本次技能修改操作 HIL。

## 審查紀錄

- standards_review：PASS。需求端 callable 注入符合依賴方向；功能模組不匯入具體 adapter；大檔 hash 採 streaming。
- spec_review：PASS。release 使用真實 runner acceptance 結果及独立 release report；無未覆蓋阻擋需求。
- 最後限縮複查：PASS。缺 review placeholder 時在 Routing/Gates 補入 Spec review: PASS；semantic 僅排除完整 review 狀態行，其餘契約內容仍比對。

## 範圍與限制

僅更新此技能原始碼與本地組裝產物；未修改 env_sensing、未刷寫硬體、未安裝或發布 plugin。既有安裝版本不因這次原始碼修改自動更新。

工具只強制管理入口，不能攔截任意模型文字或非管理檔案寫入。證據 artifact 由呼叫端提供並核對 hash，沒有宣稱為 host 認證的觀察紀錄。架構 release gate PASS 不代表已發布插件或取得硬體 release acceptance。
