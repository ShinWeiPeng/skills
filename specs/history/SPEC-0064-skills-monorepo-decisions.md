# SPEC-0064 討論紀錄

本檔依維護者選擇，只封存整理後的決策；不包含原始對話、授權 receipt 或本機執行狀態。正式需求與驗收仍以 [SPEC-0064](../SPEC-0064-skills-monorepo-independent-releases.md) 為準。

## Decisions
| ID | Decision | Source |
| --- | --- | --- |
| DEC-001 | 後續明確 monorepo 樹狀結構取代最初兩個獨立 repo 的選擇。 | user:所以不能在ShinWeiPeng下新增skill，變成樹狀結構 |
| DEC-002 | 方案須涵蓋現有 PR 版本控管方式。 | user:因為目前是透過PR進行版本控管的 |
| DEC-003 | 採用 Q-001@2 選項 1：同時支援 Codex 與 Claude，保留原有協作流程。 | user:採用1 |
| DEC-004 | 使用者確認完整 SPEC-0064 修訂6方案並授權開始執行；平台、目錄、版本與驗收範圍維持既有完整提案。 | user:adopt-plan-start |
| DEC-005 | 本次 SPEC-0064 允許原生 Git／檔案工具補齊驗證設定並執行已核准搬移與修改；來源雜湊、範圍限制及原訂驗收維持。原開始執行授權繼續適用同一產品範圍。 | user:allow-native-tools |

## Decision History

See Decisions, Discussion Context and the sourced Discussion History below.


## 封存選擇

2026-10-22：維護者選擇「只把整理後的討論紀錄封存到 specs/history/」。原始工作檔不提交。

## 後續調整

- 補作文件套件整合到 main，保留已發布工程 0.23.2 的內容與 tag。
- 使用者決定保留必要 CI 測試與設定；來源放在 .github/tests 與 .github/validation。
- spec-governance、artifacts 與生成的 validation 內容只留本機並忽略；先保存既有檔案，不清除 Git 歷史。
- .github 的發版流程與兩平台 marketplace catalog 保留；非必要 issue 模板與標籤自動化只留本機。
