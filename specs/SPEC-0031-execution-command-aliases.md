---
spec_version: 1
spec_id: SPEC-0031
revision: 2
status: confirmed
change_set: execution-command-aliases
---

# 執行指令簡寫與一致授權辨識

## Problem
使用者已要求「開始執行」與「開始執行 SPEC」均可使用。現有 workflow_selection.py 僅識別無目標指令或完整 canonical 路徑，spec_delivery.py 亦只接受無目標或精確路徑。SPEC 編號簡寫會在不同入口遭拒；先前提供完整路徑的說明也造成必填的誤解。

## Solution
統一執行指令解析、目標規格解析及授權核對，允許短指令並保留完整路徑。規格保存與產品執行授權分離。沿用現有模組與權威工作狀態，不建立第二套授權來源。

## User Stories
- 使用者說「開始執行」即可接續本任務目前已確認的 SPEC。
- 使用者可用 SPEC 編號明確指定規格，不必記住檔名。
- 多份候選或錯誤編號不會造成誤執行。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 接受「開始執行」、「開始執行SPEC」、「開始執行 SPEC」作為無顯式目標的等價指令。接受「開始執行SPEC-0029」及「開始執行 SPEC-0029」形式的四位數 SPEC 編號；數字依實際目標變動。保留原本完整 canonical 路徑寫法。去除首尾空白，指令與 SPEC 間允許零或多個空白。 |
| REQ-002 | 指定編號或路徑時精確解析該規格；不存在、編號對應多個檔案、路徑非法或指定目標與授權綁定不一致時明確阻擋，不回退到其他規格。 |
| REQ-003 | 無顯式目標時使用本任務目前已確認且可唯一識別的 SPEC。新任務沒有有效綁定時可選唯一有效 confirmed 候選；多個候選且無法從任務脈絡唯一判定時才詢問。不得以檔名順序、最新時間或最新編號代替選擇依據。 |
| REQ-004 | 路由、規格解析及執行授權檢查共用同一辨識契約與解析結果。保留原始使用者指令及其來源，綁定解析後 canonical path、task、working reference、revision/hash；不得偽造完整路徑授權文字。 |
| REQ-005 | 簡寫不得略過 confirmed 狀態、待決事項、衝突、版本及既有執行檢查。否定、詢問、引用或解說中的字串不構成執行授權；implemented 規格、過期授權及原本應阻擋的條件仍按既有生命週期處理。 |
| REQ-006 | 同步 ask-matt、spec-governance、implement、受影響的共用契約、人類文件及必要路由契約。預設指引使用短指令，完整路徑標為選填；不要求使用者重複已有效提供的本次授權。 |
| REQ-007 | 驗證來源與組裝後插件行為一致，涵蓋所有允許寫法、目標消歧義與授權反例，並保留 SPEC-0029 討論保存、task/turn 綁定及補存額度。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 短指令為正常支援介面；完整路徑僅供明確指定目標。依據使用者明確要求，不另要求選擇是否支援。 |
| DEC-002 | 以現有任務脈絡與精確 SPEC 身分解析目標；不以模糊匹配或最新規格猜測。 |
| DEC-003 | 本次採統一契約的相容性修正，實作時依現有模組邊界放置共用解析入口；不擴大為任意自然語言授權。 |

## Discussion Context
### DISC-001: 短指令需求
- **Situation:** 先前以完整路徑示範執行 SPEC-0029，使使用者質疑原本短指令為何不能使用。
- **Question:** 使用者直接提出介面要求，沒有額外決策問題。
- **Options and tradeoffs:** 僅接受完整路徑要求使用者記住檔名；接受簡寫並精確解析保留易用性與原有授權綁定。
- **Explicit rationale:** 使用者要求「記得下開始執行或是開始執行SPEC都要可以」；未聲稱使用者另行選擇內部程式設計。
- **User answer:** 為什麼開始執行變成這樣?記得下開始執行或是開始執行SPEC都要可以
- **Decision:** DEC-001。
- **Resulting impact:** REQ-001、REQ-006。

### DISC-002: 方案與規格保存
- **Situation:** 助理提出統一指令辨識方案，但只保存為候選紀錄，沒有建立正式 SPEC。
- **Question:** 使用者要求說明為何未寫入 SPEC。
- **Options and tradeoffs:** 完整方案保留在聊天或候選紀錄不足以作為實作契約；正式 SPEC 可追蹤範圍、行為及驗收。保存本身不授權程式修改。
- **Explicit rationale:** 需求已明確；方案需落入可檢視的規格，不要求使用者再次採納已明確提出的短指令要求。
- **User answer:** 提出方案；為何麼沒有寫入SPEC?
- **Decision:** DEC-002、DEC-003 為依需求整理的技術方案，並非虛構使用者逐項作答。
- **Resulting impact:** REQ-002～REQ-007；建立獨立相容性規格，不改寫 SPEC-0029 的既有驗收結果。

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 各短指令及完整路徑均能辨識；零、多個及首尾空白正確處理。 | 參數化解析測試與 CLI 正例矩陣。 | PENDING |
| AC-002 | REQ-002 | 正確編號選中唯一 canonical；不存在、重複、非法路徑與綁定不符不會選別份。 | 以暫存倉庫建立明確及衝突候選，核對結果、退出碼與無執行副作用。 | PENDING |
| AC-003 | REQ-003 | 本任務、新任務唯一候選可接續；多候選無脈絡時要求選擇，不按最新猜測。 | 跨任務及多候選整合測試，交換檔名排序及修改時間。 | PENDING |
| AC-004 | REQ-004 | 每種允許寫法在路由至 admission 的結果一致，保留原始指令與來源，最終綁定同一規格。 | 端到端路由/解析/managed admission 正反例及 receipt 內容斷言。 | PENDING |
| AC-005 | REQ-005 | 否定、詢問、引用不啟動；未確認、待決、衝突及過期版本仍阻擋。 | 反例矩陣與既有 SPEC 生命週期、授權回歸。 | PENDING |
| AC-006 | REQ-006 | 文件一致列出短指令及可選路徑；有效授權不被要求重複輸入。 | 技能/共用契約/docs 檢查及同任務授權接續測試。 | PENDING |
| AC-007 | REQ-007 | 來源及組裝產物結果一致，SPEC-0029 保存與補存限制回歸不退化。 | 完整相關測試、assembly/distribution validation、架構與格式檢查。 | PENDING |

## Relationships
| Source | Relation | Target |
|---|---|---|
| REQ-004 | refines | SPEC-0024 |
| REQ-007 | refines | SPEC-0029 |

## Implementation and Validation Plan
先建立指令與目標解析正反例，再接到路由與 admission；保留現有組合層與模組依賴邊界。同步文件、架構描述及驗收對照，檢查來源和組裝產物。語法採確定性規則，無統計、效能或硬體時序主張。實作前依現有治理流程準備驗證規劃與檢查必要的架構/演算法紀錄更新。

## Impact and Tradeoffs
使用者可用短指令；需同步多個既有入口與其測試。採精確解析而非寬鬆語句匹配，避免將討論誤視為授權。產品修改與發布仍沿用既有授權邊界。

## Out of Scope
不實作 SPEC-0030 通用恢復，不變更 SPEC-0029 hook 信任或桌面驗收，不新增任意自然語言授權、批次執行多份規格、Git 提交或發布。

## Open Decisions
None.

## Routing/Gates
grilling 管理已保存需求，spec-governance 建立正式規格；尚未取得本變更的產品執行授權。後續執行需 formatter、project-validation、相關架構檢查及 code-review；本次僅保存 SPEC，不宣稱執行/驗收就緒。

## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-18 | 依使用者短指令要求與已提出方案補建正式規格；全部 AC 待驗證，尚未授權實作。 |

