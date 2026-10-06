---
spec_version: 1
spec_id: SPEC-0040
revision: 20
status: implemented
change_set: coding-standards-migration
working_id: WORKING-SPEC-e40ab067fac8-coding-standards-migration
task_ref: 01a0eb0c-4931-7112-8cdf-8862d42e984b
---

# 既有規則搬移與程式規範治理重整

## Problem
本對話要求將既有程式規則治理重整與新增程式規則分開規劃，避免搬移時混入新限制。

## Solution
既有規則搬移與程式規範治理重整。本文件為討論中的工作 SPEC，尚未確認或取得實作授權。

## User Stories
所有專案使用共用且可持續修訂的分檔規則，依各專案平台與執行路徑套用。

## Requirements

有效條款以 Relationships 的取代關係為準：REQ-007、DEC-004、AC-004 已由本輪更正取代，僅保留追溯；不得據此合併或移除兩個 Skill。
| ID | Requirement |
|---|---|
| REQ-001 | 新增 coding-standards Skill，既有規則依責任分檔、唯一來源，所有專案共用；搬移保留原語意與 MUST/SHOULD/MAY 強度。 |
| REQ-002 | 程式規則、設計流程、檢查流程、資料格式分開；拆分後按責任重新命名並更新全部引用。 |
| REQ-003 | 新版適用性機制按專案 CPU、OS、工具鏈、記憶體預算、工作負載與路徑判斷；取代舊判斷入口。 |
| REQ-004 | 舊設計與 SPEC 自動轉換可確定部分；衝突或缺漏保留並繼續討論，不猜測、不補造有效授權。 |
| REQ-005 | 保留 SPEC 確認、開始執行授權及既有 MUST 整改／暫緩／Release 政策。修改前檢查 Git 狀態保護既有工作，不新增全倉庫乾淨限制。 |
| REQ-006 | 實作與審查使用一致版本及適用結果；同步 Skill 註冊、說明、打包與測試。 |

| REQ-007 | 已撤回：原合併兩個 Skill 的解讀由 REQ-008 取代；此 ID 保留追溯，不得據此合併或刪除入口。 |

| REQ-008 | 保留 domain-modeling 與 govern-modular-event-architecture 的不同專業職責；統一 ADR 共用管理規範，各 Skill 引用同一權威來源。domain-modeling 負責領域術語及概念，架構治理負責模組、介面、所有權及架構檢查；兩者可依職責提出或草擬 ADR。共用格式、狀態與生命週期不得重複維護；架構例外的必要核准及檢查政策保持有效。撤回 REQ-007 的合併／取消獨立入口要求，共用規範具體位置與維護歸屬仍待整理呈現。 |

| REQ-009 | ADR 共用規範採方案 A，放在插件層共用文件區，由共用規範層維護唯一來源，不新增 ADR Skill；domain-modeling 與 govern-modular-event-architecture 均引用。共用格式、管理流程與檢查規範依責任分檔；架構例外的適用及核准要求仍由架構治理管理。須調整打包、安裝及引用檢查，使發布與安裝後的 Skill 均能讀取同版共用文件；來源與產物不得形成兩套手動維護規範。 |

| REQ-010 | 採用目錄配置：skills/engineering/coding-standards/rules/ 保存純程式條款，依 module-boundaries.md、type-and-state-ownership.md、memory-management.md、boundary-validation.md、error-handling.md、data-flow.md 等主題分檔；references/applicability.md 與 rule-versioning.md 保存適用性及版本流程，SKILL.md 串接而不抄寫條款。既有其他條款須完整盤點並依責任歸檔，不因示範清單而遺漏。 |
| REQ-011 | ADR 共用文件來源為 plugins/governed-engineering-skills/references/adr/，分 format.md、workflow.md、checks.md；兩個專業 Skill 保留並引用。架構治理保留 architecture-design-workflow.md、architecture-check-workflow.md、architecture-exception-policy.md 等職責文件。打包及安裝引用須驗證，生成產物不得另行手動維護。 |
| REQ-012 | core-standard.md 依職責拆分，程式條款移入 coding-standards/rules/，流程移入架構治理對應文件；完整更新引用並移除舊混合文件。SPEC-0040 僅搬移原有語意，記憶體／異常／資料流等新增條款與模組／資料流設計表的新義務由 SPEC-0041 引入。 |

| REQ-013 | 純程式規則採規則 ID、強度、適用條件、程式要求四欄。驗證方法及工具／證據映射與程式條款分離；具體檢查文件依 REQ-014。 |

| REQ-014 | 採用 coding-standards/references/verification/ 下 design-checks.md、static-checks.md、runtime-checks.md 與 rule-verification-map.md；三類檢查定義判準，映射連結規則 ID、適用條件、方法與證據能力。既有 Skill 保留執行流程並引用判準，ADR 使用共用 checks.md，本次搬移檢查列 SPEC-0040 驗收計畫。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 使用者已採用方案 C，規則依主題分檔，不合成單一規則大全。 |
| DEC-002 | 平台條件依專案及目標決定，不設使用者全域 MCU／PC 偏好。 |
| DEC-003 | ADR 統一交架構治理管理是助理候選建議，尚未獲使用者明確採用。 |

| DEC-004 | 使用者指出兩個 Skill 不應同時存在，修正原 ADR 擁有者選項的前提；採單一入口方向。助理建議併入既有架構治理、取消 domain-modeling 的獨立註冊與路由，該具體方案仍為候選，未授權實作。 |

| DEC-005 | 使用者引用「保留不同的專業職責，統一 ADR 的共用管理規範；各 Skill 引用同一份規範」並確認「這個才是整理方向」。更正助理先前將疑問記成合併要求的解讀，取代 DEC-004；不推定選定先前 A/B/C 的具體規範擁有者。 |

| DEC-006 | 使用者回答 A，採用插件層共用文件區方案；兩個專業 Skill 保留，不新增 ADR Skill。確切目錄名稱、搬移對照與打包調整由 Codex 整理呈現，不推定已授權實作。 |

| DEC-007 | 使用者以採用確認前輪目錄配置與文件分工，包括程式規則、適用及版本流程、插件 ADR 共用文件、專業流程及 core-standard.md 的拆分移除；保留兩份 SPEC 的範圍界線。 |

| DEC-008 | 使用者在四欄規則格式的註解回答採用，同時詢問搬移對照的時機及應建立哪些檢查規範；僅確認四欄，不推定已採用尚未呈現的檢查文件方案。 |

| DEC-009 | 使用者回答採用三類檢查及映射文件，另指出模組化設計未明列，引用聊天 01a0f17f-570b-7fd3-807c-f55d38f3f47d 要求檢討；不能把新增模組化補強候選視為已採用。 |

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | 搬移對照無遺漏、無重複條款、引用可解析，強度與語意保持。 | 條款逐項對照及引用檢查；未執行。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-001-review.json |
| AC-002 | REQ-003, REQ-004 | 不同目標可得到不同適用結果；未知資料不被猜測；遷移可重跑且衝突可見，舊入口不再判定。 | 適用性與遷移契約測試；待具體情境映射。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-002-review.json |
| AC-003 | REQ-005, REQ-006 | 不因遷移或 Git 乾淨繞過授權；實作與審查一致；安裝包包含新 Skill 及引用。 | 授權回歸、打包與整合測試；未執行。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-003-review.json |

| AC-004 | REQ-007, REQ-008 | 已撤回的合併方向不被執行；兩個專業 Skill 保留，現行功能验收依 AC-005。 | 歷史取代關係與註冊檢查；未執行。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-004-review.json |

| AC-005 | REQ-008 | 兩個 Skill 專業職責與入口保留；ADR 共用格式／狀態／生命週期有單一權威來源且引用可解析，沒有平行重複定義；架構例外核准政策仍可檢查，不因一般 ADR 格式而繞過。 | 職責與引用對照、一般 ADR 與例外 ADR 正反案例及既有功能回歸；待建立。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-005-review.json |

| AC-006 | REQ-009 | 共用 ADR 格式、流程、檢查規範分檔且只有一個可編輯權威來源；兩個 Skill 及打包安裝後的引用均可解析到一致版本；缺檔或失效引用可檢出，架構例外核准要求未遺失。 | 來源／產物引用檢查、安裝布局案例及既有 ADR 例外回歸；待具體映射。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-006-review.json |

| AC-007 | REQ-010, REQ-011, REQ-012 | 檔案職責及位置符合採用配置，rules/ 無階段流程；原條款完整搬移且強度不變，舊混合文件與失效引用清除；來源及安裝產物引用可解析，新增要求可追溯至 SPEC-0041。 | 文件責任盤點、搬移對照、引用／產物檢查及兩份 SPEC 範圍審查；待具體映射。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-007-review.json |

| AC-008 | REQ-013 | 純程式條款以四欄呈現，檢查方法透過規則 ID 引用且不混入條款；工具或證據位置不被當作程式要求。 | 格式與規則引用檢查；待映射。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-008-review.json |

| AC-009 | REQ-014 | 四份檢查文件依職責分開，使用同一規則 ID 並明示工具覆蓋與限制，既有執行流程引用而不重複定義；ADR 與遷移驗收範圍獨立。 | 文件與引用檢查及設計／靜態／執行期案例；待映射。 | PASS: artifacts/validation/9db7882061184940914b09e07790e46a/AC-009-review.json |

## Relationships
| Source | Relation | Target | Rationale |
|---|---|---|---|
| REQ-013 | refines | REQ-010 | 確認純程式條款格式。 |
| REQ-010 | refines | REQ-001 | 具體化程式規則與治理流程位置。 |
| REQ-011 | refines | REQ-009 | 確認 ADR 共用文件路徑及分檔。 |
| REQ-012 | refines | REQ-002 | 確認 core-standard 拆分移除與引用遷移。 |
| REQ-009 | refines | REQ-008 | 選定共用規範的插件層維護位置。 |
| DEC-006 | supersedes | DEC-003 | 原架構 Skill 擁有共用規範的候選改由插件共用層方案取代；保留架構例外政策。 |
| REQ-008 | supersedes | REQ-007 | 使用者明確保留不同專業職責，撤回先前合併解讀。 |
| DEC-005 | supersedes | DEC-004 | 本輪更正整理方向。 |
| AC-005 | supersedes | AC-004 | 改驗收共用 ADR 規範與職責保留，不驗收單一 Skill 入口。 |

新增程式規則由另一份獨立工作 SPEC 管理；本次不新增其限制。

## Out of Scope
未取得「開始執行」前不修改 Skill、程式、插件設定或執行發布。不將先前舉例視為已採用條款。

## Open Decisions
None.

## Specification Preparation
- 插件層共用文件區及具體目錄配置已確認。完整搬移對照、格式欄位與驗收映射由 Codex 整理後呈現；整份 SPEC 尚未正式確認，不合併兩個 Skill。

## Candidate Migration Mapping
以下是文件／章節層級候選對照，尚未完成逐條編號、語意核對及所有消費端盤點，不宣稱完整搬移清單已驗收。
| Existing source | Rule destination | Workflow or format destination |
|---|---|---|
| core-standard.md | module-boundaries.md、type-and-state-ownership.md | 架構設計／檢查流程、版本流程及例外政策；文件 metadata 留格式規範 |
| event-contract.md | data-flow.md 的埠、順序、交付及既有生命週期要求 | 規定的事件欄位仍是程式契約，示例另放 examples；不把跨模組義務擴大到所有局部資料 |
| execution-efficiency.md | 候選 execution-and-platform.md，承載既有平台、配置、布局及最佳化條款 | execution-design-workflow.md：平台確認、候選比較、成本分析；量測驗收歸檢查流程 |
| realtime-scheduling-analysis.md | execution-and-platform.md 中可歸為程式時間與阻塞契約的內容 | 排程研究流程、分析公式、報告格式與驗收；保留現有適用條件 |
| runtime-validation.md | 程式的觀測邊界／有界 instrumentation 條款按主題歸規則 | 證據選擇、採集、關聯及驗收流程 |
| algorithm-design.md | 其中若有純演算法實作限制，逐條歸對應程式規則 | 演算法設計流程與 ALG 紀錄格式分開；ALG 不等於 ADR |
| flow-cost-review.md | 可識別的純程式要求依主題歸規則 | Flow 設計比較、成本審查流程與紀錄格式 |
| description-views.md | 無須將文件欄位移入程式規則 | 架構視圖格式、產生流程與一致性檢查 |
| manifest-schema.md | 已在程式規則定義的義務以 ID 引用，避免重複規範 | 維持 manifest 格式權威來源，既有欄位與版本相容行為依原契約 |
| c-analyzer.md | 不將分析器操作說明當程式條款 | 分析器設定與檢查說明，檢查能力映射規則 ID |
| test-validation-architecture.md | 涉及程式邊界的要求引用共用規則 | 測試／驗證目錄、角色、產物與證據生命週期；不塞入純程式規則 |
| domain-modeling/ADR-FORMAT.md、架構 adr-policy.md | 無 | 共用 format/workflow/checks；架構例外專屬政策留架構 Skill。一般與例外 ADR 的欄位／核准依原用途保留，不全面套用最嚴格式 |
| domain-modeling/CONTEXT-FORMAT.md | 無 | 留 domain-modeling，維持詞彙表語意 |
| codebase-design/SKILL.md | 盤點封裝、介面契約、可替換性等既有條款，依責任歸 module-boundaries.md 等；不改原強度 | 保留設計方法及詞彙指引，引用共用規則；與正式架構所有權規範的衝突不得自動加嚴解決 |
| SKILL.md、呼叫端、工具與測試 | 引用規則唯一來源 | 更新載入／呼叫／解析與安裝引用，原始碼與發布產物均查核 |

## Candidate Rule Format and Verification Mapping
- 純規則候選欄位：規則 ID、強度、適用條件、程式要求。目的／流程／工具命令／驗收證據不混入純條款。
- 程式形式例：ID MEM-LIFETIME-001（示例，非已定編號）；MUST；適用於仍被非同步操作持有的資料；操作完成或安全解除持有前不得釋放或重用記憶體。
- 對照表候選欄位：舊文件與條款定位、新文件與規則 ID、原強度與適用條件、處理類型、引用消費端、對應 AC。新舊差異不得在純搬移時擅自採較嚴條款解決。
- 驗收映射：完整盤點→條款對照；語意保持→逐條審查與正反案例；唯一來源→重複規範審查；引用及安裝→來源和產物解析；例外政策→一般／例外 ADR 案例；授權與遷移→既有入口回歸及可重跑案例。
- 每項映射明示設計審查／靜態工具／執行期證據、能力限制及預期結果，未知工具覆蓋不可宣稱已驗證。SPEC-0041 的新增行為另建對應驗收。
## Candidate Verification Documents
候選配置為 coding-standards/references/verification/ 下的 rule-verification-map.md、design-checks.md、static-checks.md、runtime-checks.md。三類文件各定義設計審查、靜態檢查、執行期驗證的判準；映射文件透過規則 ID 連結適用條件、方法、工具能力、所需證據與預期结果。既有架構、code-review、驗證 Skill 保留執行流程，引用判準，不建立第二套檢查器或重複流程。
ADR 的 checks.md 為已採用的文件一致性檢查；本次搬移另外在 SPEC-0040 驗收計畫定義一次性遷移檢查，不混成專案日常程式規則。實際工具未覆蓋的條款須明示審查或執行期證據需求。
搬移對照的時機說明：現在規格準備階段建立逐條來源／目標／強度／適用條件及引用對照，供整體 SPEC 確認；實際搬移需本次開始執行授權，執行期間更新對照，完成時逐項驗收。先前表為文件層級候選，尚非完整逐條清冊。
## Routing/Gates
Spec review: PASS
SPEC 確認與「開始執行」授權維持。工作草稿不表示實作授權。驗收情境與工具映射須於正式確認前補全。

## Discussion Context
### DISC-001: 從本對話整理決策
- **Situation:** 先前多輪討論已選定方案 C，並陸續討論新增記憶體規則。
- **Question:** 是否將搬移與新增規則分成不同 SPEC？
- **Options and tradeoffs:** 分開可獨立確認與驗收，新增規則透過搬移後的治理入口發布。
- **User answer:** 本輪明確要求「把搬移寫成一個spec，新增規格寫成另一個spec」。
- **Explicit rationale:** 使用者未另外提供理由；不得推定整份修改方案已確認。
- **Resulting impact:** REQ-001；由本對話可見決策重建摘要，沒有補造過往保存或授權紀錄。

### DISC-002: 修正為單一治理入口
- **Situation:** 原選項 A/C 均保留兩個現有 Skill，使用者指出不應並存。
- **Question:** ADR（架構決策紀錄）的格式與生命週期，由哪個 Skill 統一管理？
- **Options and tradeoffs:** A．由現有 govern-modular-event-architecture 統一管理（建議）：集中 ADR 格式、狀態及例外所需欄位；domain-modeling 等 Skill 可提出或草擬並引用同一規範。沿用既有架構例外政策、整合改動較少，但架構 Skill 需管理一般決策與例外紀錄兩種用途。
B．新增獨立 ADR 治理 Skill：集中格式與生命週期，各領域 Skill 負責決策內容及適用政策。責任獨立，適合未來多領域大量共用；代價是增加 Skill、呼叫與整合維護，架構例外檢查仍由架構治理負責。
C．由現有 domain-modeling 統一管理：延續目前 ADR-FORMAT.md 的位置，各 Skill 引用；架構治理另管理例外適用與審查要求。可保留既有入口，但需擴大 domain-modeling 的責任，並明確接合例外必填欄位。
- **User answer:** domain-modeling 跟 govern-modular-event-architecture。我的認知是不該有兩個同時存在
- **Explicit rationale:** 使用者認為不應有兩個 Skill 同時存在。
- **Resulting impact:** REQ-007、DEC-004、AC-004；接受對選項前提的修正，不強迫映射 A/B/C。保留架構 Skill 並整合領域能力是助理候選，需區分詞彙語意與實作設計；未修改 Skill 或授權實作。

### DISC-003: 更正為職責保留與 ADR 共用規範
- **Situation:** 助理先前將使用者對功能重複的疑問直接記成合併要求；後續說明確認兩者主要功能不同，ADR 為共用文件機制。
- **Question:** 整理方向是合併 Skill，還是保留專業職責並統一 ADR 共用管理規範？
- **Options and tradeoffs:** 合併會改動主要功能入口；保留職責並共用規範可保留領域建模及架構治理能力，同時消除 ADR 共用格式及生命週期的重複維護。
- **User answer:** 這個才是整理方向
- **Explicit rationale:** 使用者引用並確認「保留不同的專業職責，統一 ADR 的共用管理規範；各 Skill 引用同一份規範。」
- **Resulting impact:** REQ-008、DEC-005、AC-005 取代 REQ-007、DEC-004、AC-004；保留历史但明示舊解讀不生效。規範位置與維護歸屬未定，未修改 Skill 或取得實作授權。

### DISC-004: 採用插件層 ADR 共用文件區
- **Situation:** 已確認保留兩個專業 Skill 並統一 ADR 共用規範，待選存放與維護方式。
- **Question:** ADR 共用規範採哪一種存放與維護方式？三種方案都保留 domain-modeling 與 govern-modular-event-architecture，不合併兩個 Skill。
- **Options and tradeoffs:** A．設立插件層的共用文件區（建議）：共用 ADR 格式、生命週期流程與檢查要求分檔，由插件共用規範層維護，兩個 Skill 引用；架構例外條件仍由架構治理負責。責任中立且無須新增 Skill，但要調整打包、安裝及引用檢查，確保共用文件隨插件提供。
B．共用文件放在 domain-modeling：由它維護共用 ADR 格式及流程，架構 Skill 引用並保留例外政策。延續現有格式位置、較少增加結構，但其他 Skill 的共用文件依賴領域建模 Skill。
C．共用文件放在架構治理 Skill：由它維護共用 ADR 格式及流程，domain-modeling 引用。接近現有例外治理，但架構 Skill 要同時維護一般決策文件的共用規範。
- **User answer:** A
- **Explicit rationale:** 使用者未補充理由。
- **Resulting impact:** REQ-009、DEC-006、AC-006；回答 Q-ADR-SHARED-LOCATION-001 第 5 版；插件共用層維護規範，專業 Skill 保留。尚未授權實作。

### DISC-005: 採用目錄配置與文件分工
- **Situation:** 已採用插件層 ADR 共用規範，前輪呈現具體來源目錄、程式規則分檔及架構流程分工。
- **Question:** 是否採用這個目錄配置：coding-standards/rules/ 保存依主題分檔的純程式规则，coding-standards/references/ 保存規則版本及適用性流程；插件來源 plugins/governed-engineering-skills/references/adr/ 保存 format.md、workflow.md、checks.md 三份 ADR 共用文件；兩個專業 Skill 保留，架構設計與檢查各自分檔並引用共用規範；core-standard.md 拆分後更新全部引用並移除舊混合文件；SPEC-0040 僅搬移既有語意，新增條款與設計表要求由 SPEC-0041 引入？
- **Options and tradeoffs:** 按條款、流程、共用文件拆分可避免重複维护；需要完整更新引用並驗證來源與安裝結構，不能只搬檔案。
- **User answer:** 採用
- **Explicit rationale:** 使用者未补充理由。
- **Resulting impact:** REQ-010、REQ-011、REQ-012、DEC-007、AC-007；回答 Q-DIRECTORY-LAYOUT-001 第 8 版，尚未授權實作。

### DISC-006: 規則四欄格式與檢查規範問題
- **Situation:** 前輪呈現文件層級搬移表、四欄格式及驗收映射。
- **Question:** 純程式規則是否採用「規則 ID、強度、適用條件、程式要求」四個欄位，驗證方法與工具／證據映射另放檢查規範？
- **Options and tradeoffs:** 四欄格式維持純程式條款；檢查方法透過 ID 另連結。使用者追問時機與具體檢查規範，需要先呈現候選，不能當作已採用。
- **User answer:** 採用
- **Explicit rationale:** 本輪第二則註解採用四欄；第一則詢問何時搬移對照，第三則詢問應建立哪些檢查規範。
- **Resulting impact:** REQ-013、DEC-008、AC-008；回答 Q-RULE-FORMAT-001 第 11 版，保存時機說明與檢查文件候選。未授權實作。

### DISC-007: 檢查規範採用與模組化設計缺口
- **Situation:** 前輪提出三類檢查及規則映射，使用者同時指出模組化設計未被明確涵蓋。
- **Question:** 是否採用三類檢查規範加一份規則驗證映射：在 coding-standards/references/verification/ 分設 design-checks.md、static-checks.md、runtime-checks.md、rule-verification-map.md；既有 Skill 保留執行流程並引用這些判準，ADR 檢查仍用共用 checks.md，本次搬移檢查另列於 SPEC-0040 驗收計畫？
- **Options and tradeoffs:** 三類檢查與映射分開，不能僅有容量與記憶體檢查而漏掉模組責任、封裝與共同契約；補強義務須另辨識原有規則及新增政策。
- **User answer:** 採用
- **Explicit rationale:** 使用者引用「規劃碰撞與加速度事件」聊天，認為 Codex 未嚴格落實模組化設計。
- **Resulting impact:** REQ-014、DEC-009、AC-009；Q-VERIFICATION-DOCS-001 第 13 版獲回答。讀取引用任務確認先問外部事件是否只涵蓋 FIR，經使用者提醒才回到碰撞模組統一契約；該任務亦明言既有 Skill 有要求但未落實。唯讀查看 collision_detector.h 確認已有共用 Process 入口，fir_algorithm.cpp 的鎖定／解除目前仍由 FIR 管理。這些不是新方案已實作的證據。既有 codebase-design 規範未納入前輪搬移表是本次盤點遺漏，需補齊；更嚴格的設計確認／替換測試候選屬 SPEC-0041。未修改引用專案。

## Revision History
- Revision 14: 2026-09-30，採用檢查文件配置，記錄引用任務的模組化設計缺口。
- Revision 12: 2026-09-30，採用規則四欄格式，保存搬移時機及檢查規範候選。
- Revision 9: 2026-09-30，採用具體目錄配置與文件分工；尚未實作。
- Revision 6: 2026-09-30，採用插件層 ADR 共用文件區，納入打包與引用檢查；尚未實作。
- Revision 4: 2026-09-30，更正為保留專業職責、統一 ADR 共用規範；撤回合併要求，尚未實作。
- Revision 3: 2026-09-30，記錄單一治理入口要求與合併候選；尚未實作。
- Revision 1: 2026-09-29，依本對話建立工作草稿；歷史回合未逐輪保存，本文為可見對話的回顧整理。
| 17 | 2026-10-02 | Reopened before clarification: Bind the legacy unbound specification to its actual current task without changing the adopted contract. |
| 18 | 2026-10-02 | Reopened before clarification: Add the missing Evidence column required by the execution planner; preserve every acceptance criterion and threshold. |
| 20 | 2026-10-02 | Recorded implementation PASS evidence. |


## Implementation preparation — 2026-10-02

本節將已採用決策整理成可執行的搬移方案；不是新增使用者決策，也不是實作或驗收結果。前文 Candidate 章節作為討論歷史保留；與本節重疊時，按後續已採用 REQ／DEC 及 Relationships 解讀。REQ-007／AC-004 為已撤回的合併方向，不能成為產品驗收義務。DEC-003、DEC-004 不生效。

### 文件責任及修改邊界

| 責任 | 唯一維護來源 | 消費者 |
|---|---|---|
| 純程式條款 | skills/engineering/coding-standards/rules/*.md | 設計、實作、審查及各類檢查 |
| 規則載入、適用性、版本 | coding-standards/SKILL.md、references/applicability.md、references/rule-versioning.md | ask-matt 與既有階段 Skill |
| 設計、靜態、執行期判準與能力映射 | coding-standards/references/verification/ 四份已採用文件 | 架構檢查、code-review、verification-ladder、validate-on-device |
| 架構設計／檢查／例外 | govern-modular-event-architecture/references/architecture-design-workflow.md、architecture-check-workflow.md、architecture-exception-policy.md | 架構 Skill；其餘 Skill 透過引用使用 |
| 專案資料結構 | 現有 manifest-schema.md 及對應工具 schema | manifest 編輯、解析、檢查、文件產生器 |
| 模組／介面／資料流文件格式 | SPEC-0041 的 module-design-format.md、data-flow-design-format.md | 同一 manifest 的生成視圖 |
| ADR 格式／流程／檢查 | plugins/governed-engineering-skills/references/adr/format.md、workflow.md、checks.md | domain-modeling 與架構 Skill |
| 領域詞彙與設計方法 | domain-modeling、codebase-design 原職責文件 | 討論／設計階段；不重複定義正式程式條款 |

上表省略完整路徑的條目皆相對於 skills/engineering/ 下所列 Skill。插件來源與安裝包可有不同相對路徑，由組裝流程處理；不得建立第二份手動维护的規範。規則 ID 取代重複全文，schema 只定義欄位／值與結構約束，不以引用規則為由刪掉解析器需要的欄位。

### 條款搬移對照

來源定位採文件名＋章節＋原條號；不依賴搬移後變動的行號。下列目標 ID 為本次實作配置，原條文全文及條件是語意審查基準。明示 MUST／SHOULD／MAY 原樣保留；禁止句仍為禁止，不把設計偏好升格 MUST。混合段落按表拆分，不能將文件流程抄入四欄程式規則。

| 搬移 ID | 原位置／內容 | 目標與處理 |
|---|---|---|
| MIG-001 | core-standard / Rule levels 三項 | rule-versioning：強度含義；architecture-exception-policy：偏離及核准；每條規則保留強度欄 |
| MIG-002 | core / Levels：L0、L1、L2、L3+ 表與責任段 | module-boundaries / MOD-LEVEL-001..004；層級是語意，不要求空資料夾 |
| MIG-003 | core / Dependency rules 1 | module-boundaries / MOD-DEP-001：L1/L2 parent |
| MIG-004 | 同章 2 | MOD-DEP-002：兄弟依賴與父層協調 |
| MIG-005 | 同章 3 | MOD-DEP-003：L0/L1 公開契約方向 |
| MIG-006 | 同章 4 | MOD-DEP-004：組裝具體 adapter 的允許用途 |
| MIG-007 | 同章 5 | MOD-DEP-005：功能模組不得依賴具體外部技術或外洩框架型別 |
| MIG-008 | 同章 6 | MOD-DEP-006：需求側擁有 port |
| MIG-009 | 同章 7 | MOD-DEP-007：adapter 依賴與禁止循環 |
| MIG-010 | 同章 8 | MOD-DEP-008：局部純計算不強制 port |
| MIG-011 | core / Named-type ownership 1 | type-and-state-ownership / TYPE-001：唯一語意 owner；登錄欄位與 schema 版本留 manifest-schema |
| MIG-012 | 同章 2 | architecture-design-workflow：先分類 source sets；schema 保留 production/generated-production 範圍 |
| MIG-013 | 同章 3 | architecture-design-workflow：field roles 盤點；枚舉值留 schema |
| MIG-014 | 同章 4 | TYPE-002：公開型別禁止 adapter/framework/wire/storage 外洩 |
| MIG-015 | 同章 5 | TYPE-003：私有 runtime/helper 及 mutation authority |
| MIG-016 | 同章 6 | TYPE-004：混合 domain 與 adapter 欄位的合法私有位置 |
| MIG-017 | 同章 7 | TYPE-005：型別引用遵守依賴方向 |
| MIG-018 | 同章 8 | design-checks：改名／別名／搬欄位不足以證明責任分離 |
| MIG-019 | 同章 Type Ownership Matrix 段 | architecture-design-workflow：修改前盤點；schema 保留矩陣欄位及未知阻擋 |
| MIG-020 | 同章 generated declarations 段 | architecture-check-workflow：整改在 owner/consumer/template，不手改生成碼 |
| MIG-021 | 同章 Choose owner 段 | design-checks：語意、invariants、生命週期、修改權限作為 owner 依據；TYPE-006 禁止父層 DTO 因重用而進子層公開 API |
| MIG-022 | core / Contract and mapping 1 | MOD-MAP-001：合法依賴且語意匹配才可直接傳 producer contract |
| MIG-023 | 同章 2 | MOD-MAP-002：兄弟或子到父的非法依賴改由父層轉換兩側契約 |
| MIG-024 | 同章 3 | MOD-MAP-003：parent-private mapping 不進 child public contract |
| MIG-025 | 同章 4 | MOD-MAP-004：primitive／standard type 不強制 wrapper DTO |
| MIG-026 | 同章 5 | MOD-MAP-005：DTO 只有契約語意 |
| MIG-027 | core / Runtime-state ownership 1 | STATE-001：唯一 owner；state_objects 登錄另留 schema |
| MIG-028 | 同章 2 | STATE-002：完整 runtime 定義在 owner 私有實作 |
| MIG-029 | 同章 3 | STATE-003：禁止非 owner 藉 globals/extern/pointer/getter 取得私有狀態 |
| MIG-030 | 同章 4 | STATE-004：query 回語意值／immutable snapshot |
| MIG-031 | 同章 5 | STATE-005：command 不轉移可變 authority |
| MIG-032 | 同章 6 | STATE-006：opaque handle 只能透過 owner API 操作 |
| MIG-033 | 同章 7 | STATE-007：L0 wrapper 不能掩蓋違法存取 |
| MIG-034 | 同章 State Object Matrix 段及 Authoring-first | architecture-design-workflow：先確認 boundary/type/state/mapping，再編碼；不得為 checker 反改設計標籤 |
| MIG-035 | core / Logical and execution architecture | execution-design-workflow：Module 與 execution unit 多對多、平台確認與工作負載驅動分析 |
| MIG-036 | core / New projects、Existing projects | architecture-design-workflow：新舊入口；architecture-exception-policy：MUST 整改、精確暫緩、人類核准、Release 零暫緩 |
| MIG-037 | core / Every architecture-affecting change 五步 | architecture-design-workflow＋architecture-check-workflow，保留每一步及證據義務 |
| MIG-038 | core / Description and navigation | schema＋description-views：描述與生成唯一來源；MOD-META-001：沒有產品需求不得新增 runtime 描述 struct/ABI |
| MIG-039 | event-contract / Inputs | data-flow / FLOW-INPUT-001..003：typed admission、立即拒絕、接受後事件完成、純 query 同步；SPEC-0040 保留原語意，SPEC-0041 才改完成方式 |
| MIG-040 | event / Outputs 首段 | FLOW-OUTPUT-001：單一 sink、父層/adapter fan-out |
| MIG-041 | event / Fan-out 1..5 | FLOW-FANOUT-001..005：lock 外呼叫、失敗繼續、順序、匯總錯誤、不能假回滾 |
| MIG-042 | event / Event envelope | FLOW-EVENT-001：六欄；FLOW-EVENT-002：可信 clock 條件與 at-least-once metadata；schema 僅描述結構 |
| MIG-043 | event / Lifecycle | FLOW-LIFE-001：commit-before-publish、同 stream 序列且不可重入、跨 stream 可並行；狀態圖保留條件 |
| MIG-044 | event / Delivery 三項 | FLOW-DELIVERY-001..003：預設 at-most、重試/持久化 at-least、exactly-once 證明及 ADR |
| MIG-045 | event / C port shape | 範例移 architecture references/examples；需求側型別與組裝 binding 引用 MOD-DEP-006，不再重複條款 |
| MIG-046 | execution-efficiency / Required workflow 1..5 與 RT 段 | execution-design-workflow：平台、workload、baseline、比較、human acceptance、排程相容性 |
| MIG-047 | execution / Tier 0 | execution-and-platform / EXEC-OPT-001..002：條件式偏好、不把 SoA/padding/SIMD/PGO 等當無條件預設 |
| MIG-048 | execution / Tier 1、Tier 2 | execution-design-workflow：成本欄位／升級觸發／候選；runtime-checks：代表性 release build、baseline 與指標，不以平均值取代 RT 上界 |
| MIG-049 | execution / Data and branch planning | execution-design-workflow：working set 公式、cache headroom、branch 分布及候選；檢查判準留 design-checks |
| MIG-050 | execution / Runtime acceptance | runtime-checks：全 flow budgets、其他關鍵指標不回退、mechanism claim 需 counters/equivalent |
| MIG-051 | runtime-validation / Boundaries 前四項 | MOD-OBS-001..004：L3+ 技術、需求側 port、test-only composition、hot-path bounded observation；prefer 維持偏好 |
| MIG-052 | runtime / Boundaries 後二項 | runtime-checks：guided actor/source、immutable facts、不能信任手改 PASS |
| MIG-053 | runtime / Evidence routing 全項 | runtime-checks：平台/provider/fallback/clock/run/profile/hash/SLO/baseline；採集流程仍屬 validate-on-device |
| MIG-054 | runtime / High-frequency instrumentation 第一段 | execution-and-platform / EXEC-OBS-001：避免每樣本擾動、有界無配置統計與快照；量測成本/丟失欄位留 runtime-checks |
| MIG-055 | runtime / 同章第二段與 Governance data | runtime-checks：樣本/時間/warmup/budget、BLOCKED vs FAIL；schema/description-views：IDs/links；架構檢查後才採集 |
| MIG-056 | algorithm-design 全文 | algorithm-design-workflow＋algorithm-record-format：觸發/N-A、ALG owner/path/狀態/13欄、方法分類/證據/更新/既有盤點；演算法紀錄不當 ADR，私有 L2 步驟不抬升 flow |
| MIG-057 | flow-cost-review 全文 | flow-cost-review-workflow＋flow-cost-record-format：四維審查、九欄、候選與升級、stack/units/callgraph/reserve、Pareto、八個反例；runtime-checks 引用原判準 |
| MIG-058 | realtime-scheduling-analysis 全文 | 保留排程研究、精確公式、支援演算法/schema/報告契約，拆流程與檢查責任引用；不改 RTA 公式、不降低證據要求、不將 RM 套全部 scheduler |
| MIG-059 | description-views 全文 | 保留生成路徑、marker、ID、語言與 navigation；architecture-check-workflow 引用生成一致性，禁止平行手寫來源 |
| MIG-060 | manifest-schema 全文 | 保留格式唯一來源，重複程式要求換 ID 引用；SPEC-0040 不引進 SPEC-0041 新欄位 |
| MIG-061 | c-analyzer 全文 | 保留工具設定/診斷/能力；將義務連到 rule-verification-map；AST/lexical/未支援語言能力界線不得模糊 |
| MIG-062 | test-validation-architecture 全文 | 測試布局及 artifact 生命週期留原 owner；程式邊界引用共用規則；歷史 run 不補造，ignored/untracked 掃描義務保留 |
| MIG-063 | domain-modeling/ADR-FORMAT：路徑、模板、optional、numbering | ADR format/workflow：一般 ADR 格式與序號，保留 optional 語意 |
| MIG-064 | 同檔 When to offer / What qualifies | domain-modeling 保留領域決策觸發與例子，引用共用 ADR 文件 |
| MIG-065 | adr-policy / Required sections、Approval boundary | ADR format/checks 定義架構決策 profile 的九欄；architecture-exception-policy 定適用、批准、精確規則/位置，不推廣至全部一般 ADR |
| MIG-066 | adr-policy / Versioning | rule-versioning 接手版本流程；依已採用 REQ-004 自動轉換可確定部分，衝突留討論；不能藉更新 pins 造出核准 |
| MIG-067 | codebase-design/SKILL：Glossary/Deep/Principles/Testability/Relationships/Rejected framings | 設計詞彙、啟發式與示例保留；正式邊界／所有權改引 coding-standards；不把小介面或 return 偏好升格絕對禁副作用 |
| MIG-068 | codebase-design/DEEPENING | 方法與測試策略保留，正式 Module/Port 依既有架構優先關係；不因只有一個 adapter 撤掉必需技術邊界 |
| MIG-069 | 各 SKILL 入口、docs、README、插件 manifest、組裝與測試 | 更新註冊、路由、文件連結及 source/installed 布局；不複製新條款全文 |

MIG-056..062 是完整文件保留及責任拆分的範圍；實作 review 須逐段對照 diff，不得以表格一行即宣稱內容未遺失。core-standard 所有章節及 event-contract 所有章節已列定位；搬移後舊 core-standard 移除，歷史 SPEC／journal 的文字引用保留為歷史，不批量改寫。

### 引用盤點與既有差異

2026-10-02 對 skills、docs、plugins、tests、.claude-plugin、.agents、README 的 core-standard.md/event-contract.md/ADR-FORMAT.md/adr-policy.md 文字引用查找，直接命中兩個入口：domain-modeling/SKILL.md 與 govern-modular-event-architecture/SKILL.md。此結果不代表只有兩個整合點：動態打包、schema/checker ID、docs 註冊另依 MIG-069 驗證；不掃生成 dist 當可編輯來源。

讀取 c-analyzer.md 發現 provider 開頭要求 clang 20.1.5／Espressif native 20.1.1，但 Inputs 仍列 libclang 18.1.1。這是既有文件矛盾，需以工具鎖及實際 provider owner 核對後修正過時說明，不能在搬移時任選版本、安裝套件或改工具鏈政策。不得將此誤報為使用者尚未決定。

### 適用性、更新與階段銜接

1. 討論取得平台事實；目前不知道的資料保持 unknown，允許與它無關的邏輯設計繼續。平台資料由專案 manifest/profile 維護，不寫進共用規則。
2. coding-standards 按同一版規則 ID＋條件，輸出適用、不適用（理由）、尚缺資料（來源）。設計、實作、review 共用結果，不保留舊入口並行裁決。
3. 修改前比對規則版本與專案設計；可確定的對應自動更新。未實作 SPEC 由 owner 更新；已實作 SPEC/audit/evidence 不改寫，另建關聯修訂。新需求或不確定決策回討論；不可自動補 human approval。
4. 設計前呈現方式與審查判準由各階段流程負責；純程式條款只保留四欄。實作後逐項比對程式與已確認設計，不以文件填完當完成。
5. Git 狀態檢查用於保護既有改動；不自動 stash/reset/覆寫，不要求整個 repo 乾淨。

### 驗收情境映射

| AC | 正向情境 | 反向情境／預期結果 | 方法與證據 |
|---|---|---|---|
| AC-001 | MIG 清冊每項有目的地、強度和適用條件 | 漏一條／規則重複／默默加嚴：不通過 | 逐項 diff review＋來源/產物引用檢查，保留完整清冊與版本 |
| AC-002 | MCU、RTOS、PC 同規則依 path/profile 得不同適用結果；可確定舊資料可重跑遷移 | 未知 RAM/CPU 當既知、重跑改寫已轉換值、舊入口仍裁決：拒絕 | host applicability/migration fixtures；未知只阻擋相依決策 |
| AC-003 | 相同規則版本由設計到 review；dirty 無關檔保留；安裝 Skill 可載入 | stale version、無授權、缺文件：不准入 | routing/admission 回歸及組裝安裝整合；不宣稱 host 攔截所有寫入 |
| AC-004 | 已由 AC-005 取代 | 不能執行已撤回的合併／取消 Skill | 歷史追溯檢查；現行義務依 AC-005 |
| AC-005 | domain-modeling 與 architecture 各維持專業入口、共用 ADR | 一般 ADR 被強制套全部例外欄位，或例外漏批准：不通過 | 一般與架構/例外 profile 正反文件案例 |
| AC-006 | 原始樹與安裝包均找到同版共用 ADR | 缺共用目錄、來源相對路徑在包內失效：不通過 | 隔離組裝/安裝檢查，驗證唯一可編輯來源 |
| AC-007 | 職責/新名稱與清冊相符、舊 core 已移除 | 舊活動引用殘留、混入新 memory/event 行為：不通過 | MIG-001..069 review＋兩 SPEC 範圍對照 |
| AC-008 | 每條四欄，工具證據外部引用 ID | 缺 ID/重複 ID/把命令放 requirement：不通過 | 格式與連結檢查；語意仍須審查 |
| AC-009 | 每項規則明列設計/靜態/runtime 判準及限制 | 未支援工具聲稱通過、用 AST PASS 代表無碎片化：不通過 | 能力映射審查＋代表性缺證據案例 |

以上均為預定驗收，不是已執行證據。此插件變更驗證 host 上的規則、文件、路由和檢查行為；不替任何產品宣稱記憶體、RT 或硬體效能驗收通過。

## Acceptance Mapping
```json
{
  "AC-001":{"evidence_claims":["host-semantics"],"rationale":"Migration coverage, references and preservation are host artifact contracts; semantic preservation also requires recorded review."},
  "AC-002":{"evidence_claims":["host-semantics"],"rationale":"Profile applicability and deterministic document migration are exercised in isolated host fixtures."},
  "AC-003":{"evidence_claims":["host-semantics"],"rationale":"Routing, authorization and installed-package loading are host integration contracts."},
  "AC-004":{"evidence_claims":["host-semantics"],"rationale":"Superseded by AC-005; retain history and verify that the withdrawn merger is not executed, not that one merged skill exists."},
  "AC-005":{"evidence_claims":["host-semantics"],"rationale":"Separate skill responsibilities and conditional ADR profiles are host document contracts."},
  "AC-006":{"evidence_claims":["host-semantics"],"rationale":"Source and assembled package references are verified on the host."},
  "AC-007":{"evidence_claims":["host-semantics"],"rationale":"Responsibility partition and migration scope are verified by host checks and review."},
  "AC-008":{"evidence_claims":["host-semantics"],"rationale":"Rule format and ID links are host artifact contracts."},
  "AC-009":{"evidence_claims":["host-semantics"],"rationale":"Verification coverage declarations and missing-evidence handling are host governance contracts; no target-runtime proof is claimed."}
}
```

## Current Specification

See Problem, Solution, Requirements and Acceptance Criteria above.

## Decision History

See Decisions, Discussion Context and the sourced Discussion History below.

## Pending Discussion

None.

## Completeness Gaps

None.

<!-- spec-audit:start -->
## Discussion History



### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"baa7a59918e59870bc34fcb98a370257152c79a3e9a1b9dcd7eaa67874e02e4f","event_type":"start","event_version":1,"open_decisions":["ADR 擁有者、完整條款搬移表、格式欄位及驗收情境待確認；整體方案尚未正式確認。"],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-29T10:13:57.464837+00:00","relationships":[],"revision":1,"snapshot_hash":"aa0310f3126fd2ba765fe1bd4c925331a7004951c06891b8636a432357caf7e1","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"328092a582e097fcfa93dac72cf88fadfa66142a9d9ea4d57264c4cf80cf82fb","event_type":"reconcile","event_version":1,"open_decisions":["ADR 擁有者、完整條款搬移表、格式欄位及驗收情境待確認；整體方案尚未正式確認。","Q-ADR-OWNER-001@2"],"previous_event_hash":"baa7a59918e59870bc34fcb98a370257152c79a3e9a1b9dcd7eaa67874e02e4f","previous_snapshot_hash":"aa0310f3126fd2ba765fe1bd4c925331a7004951c06891b8636a432357caf7e1","recorded_at":"2026-09-30T06:25:20.263002+00:00","relationships":[],"revision":2,"snapshot_hash":"9b7ec0c73ee286603e1ad442e6cb94c9607aa00d95968326579c0d3caa760e6b","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-004","DEC-004","DISC-002","REQ-007"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-004","DEC-004","DISC-002","REQ-007"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"89148b216e42f4ca898bd72e93cc8c51b9fda927848008b714392ec60f8f592b","event_type":"reconcile","event_version":1,"open_decisions":["單一治理入口方向已確認；具體合併及命名方案待確認。候選為併入既有架構治理並取消 domain-modeling 獨立入口。完整搬移表、格式欄位及驗收情境由 Codex 整理後呈現，整體方案尚未正式確認。"],"previous_event_hash":"328092a582e097fcfa93dac72cf88fadfa66142a9d9ea4d57264c4cf80cf82fb","previous_snapshot_hash":"9b7ec0c73ee286603e1ad442e6cb94c9607aa00d95968326579c0d3caa760e6b","recorded_at":"2026-09-30T06:30:37.817229+00:00","relationships":[],"revision":3,"snapshot_hash":"6522db681ac0d3bc9525f4774649ec4e337fa382eeb3eeb3fdb9a842fb0852ae","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-005","DEC-005","DISC-003","REQ-008"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-005","DEC-005","DISC-003","REQ-008"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"18a19d5cdff63434dfd79a87077243b7f08c57339aed26f19ae61828896b009a","event_type":"reconcile","event_version":1,"open_decisions":["保留不同專業職責並共用 ADR 規範已確認；共用規範具體存放位置與維護歸屬尚未選定。完整搬移表、格式欄位及驗收情境由 Codex 整理後呈現；不再討論或執行先前誤記的必須合併 Skill。"],"previous_event_hash":"89148b216e42f4ca898bd72e93cc8c51b9fda927848008b714392ec60f8f592b","previous_snapshot_hash":"6522db681ac0d3bc9525f4774649ec4e337fa382eeb3eeb3fdb9a842fb0852ae","recorded_at":"2026-09-30T06:53:09.460154+00:00","relationships":[{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":4,"snapshot_hash":"1058625ca56c56ef88d5e45f4c2cd404572f04fcc92179eba171f01a32f5aee0","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"870939c98cdedf37fc05337bdc4d51acb09eb6ccc9c4b4a207a5b78a84dad26d","event_type":"reconcile","event_version":1,"open_decisions":["保留不同專業職責並共用 ADR 規範已確認；共用規範具體存放位置與維護歸屬尚未選定。完整搬移表、格式欄位及驗收情境由 Codex 整理後呈現；不再討論或執行先前誤記的必須合併 Skill。","Q-ADR-SHARED-LOCATION-001@5"],"previous_event_hash":"18a19d5cdff63434dfd79a87077243b7f08c57339aed26f19ae61828896b009a","previous_snapshot_hash":"1058625ca56c56ef88d5e45f4c2cd404572f04fcc92179eba171f01a32f5aee0","recorded_at":"2026-09-30T06:55:01.584978+00:00","relationships":[{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":5,"snapshot_hash":"6a9a0031a6047f12e03b558cd5113e38775328e8b7c6755800cd14536afa0cbc","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-006","DEC-006","DISC-004","REQ-009"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-006","DEC-006","DISC-004","REQ-009"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"59cca12ebd714942b045b65a5e7d5a37cf4bc719409beea84a3c3ebf9995bb76","event_type":"reconcile","event_version":1,"open_decisions":["保留不同專業職責並共用 ADR 規範已確認；共用規範具體存放位置與維護歸屬尚未選定。完整搬移表、格式欄位及驗收情境由 Codex 整理後呈現；不再討論或執行先前誤記的必須合併 Skill。"],"previous_event_hash":"870939c98cdedf37fc05337bdc4d51acb09eb6ccc9c4b4a207a5b78a84dad26d","previous_snapshot_hash":"6a9a0031a6047f12e03b558cd5113e38775328e8b7c6755800cd14536afa0cbc","recorded_at":"2026-09-30T06:57:32.539313+00:00","relationships":[{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":6,"snapshot_hash":"a09cfbbfc9396d5a6623f86accc2ed8bc971e98295c14b35d439d1dd8a1879ca","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"9aae1887c6cc91b0863603489bb949a555748786598ab41d1fb520999750ebcd","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"59cca12ebd714942b045b65a5e7d5a37cf4bc719409beea84a3c3ebf9995bb76","previous_snapshot_hash":"a09cfbbfc9396d5a6623f86accc2ed8bc971e98295c14b35d439d1dd8a1879ca","recorded_at":"2026-09-30T06:57:52.582572+00:00","relationships":[{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":7,"snapshot_hash":"fccea9437b5b52b72b0c20be9e3dd20cdd6d38b57f09d89e586891f3957ae1a2","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"8f3a289d146f6d06dcdce8e487421f0e933821a3bd7db1bca6d62163e77bb9b5","event_type":"reconcile","event_version":1,"open_decisions":["Q-DIRECTORY-LAYOUT-001@8"],"previous_event_hash":"9aae1887c6cc91b0863603489bb949a555748786598ab41d1fb520999750ebcd","previous_snapshot_hash":"fccea9437b5b52b72b0c20be9e3dd20cdd6d38b57f09d89e586891f3957ae1a2","recorded_at":"2026-09-30T06:59:32.802079+00:00","relationships":[{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":8,"snapshot_hash":"62d82bbb1fc8394c4113266c2f642df66bc09a47e33ed6b94083bae6cb96406d","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-007","DEC-007","DISC-005","REQ-010","REQ-011","REQ-012"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-007","DEC-007","DISC-005","REQ-010","REQ-011","REQ-012"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"729f07c0e27d5861a66e8bb5be58c5d6bacc426e06ab1043696ed1f205d087d5","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"8f3a289d146f6d06dcdce8e487421f0e933821a3bd7db1bca6d62163e77bb9b5","previous_snapshot_hash":"62d82bbb1fc8394c4113266c2f642df66bc09a47e33ed6b94083bae6cb96406d","recorded_at":"2026-09-30T07:07:35.599772+00:00","relationships":[{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":9,"snapshot_hash":"99eaacd5632dcd63f977a6fc99b86b2870e198cf3c2485d3aea8a465b1db252f","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"572e5f4a46037d4ff8bdf8fabdb74baef34e2a7b0052a2bbee1f1084d1f072d7","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"729f07c0e27d5861a66e8bb5be58c5d6bacc426e06ab1043696ed1f205d087d5","previous_snapshot_hash":"99eaacd5632dcd63f977a6fc99b86b2870e198cf3c2485d3aea8a465b1db252f","recorded_at":"2026-09-30T07:15:30.772784+00:00","relationships":[{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":10,"snapshot_hash":"2a3d4bfd864477acdcf0a5c81d40f7151668958ffbeba81ba682fd7d0b881a77","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"649e609b90034889a73e021e2dbfc39beb280a50b107e912562e663b783b4244","event_type":"reconcile","event_version":1,"open_decisions":["Q-RULE-FORMAT-001@11"],"previous_event_hash":"572e5f4a46037d4ff8bdf8fabdb74baef34e2a7b0052a2bbee1f1084d1f072d7","previous_snapshot_hash":"2a3d4bfd864477acdcf0a5c81d40f7151668958ffbeba81ba682fd7d0b881a77","recorded_at":"2026-09-30T07:15:43.326503+00:00","relationships":[{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":11,"snapshot_hash":"1b783996f79d98590d04cd3ae97b0d792bb9363e74cd78fe5e895b1c448668d0","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-008","DEC-008","DISC-006","REQ-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-008","DEC-008","DISC-006","REQ-013"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"b6700a0e6573c7e67dd40ec9a84a8dc6973c588014eb96f6ca3d3342e3005f68","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"649e609b90034889a73e021e2dbfc39beb280a50b107e912562e663b783b4244","previous_snapshot_hash":"1b783996f79d98590d04cd3ae97b0d792bb9363e74cd78fe5e895b1c448668d0","recorded_at":"2026-09-30T08:36:15.429087+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":12,"snapshot_hash":"acf0f25dfdfa4213ccf1e6d31d07d601e9b11e18b7c5214aa5b1e6e2f5ac892e","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"a1878c3a8797143879d383fe46a8d2b62788ea6cc16b1748b61e777a4a568560","event_type":"reconcile","event_version":1,"open_decisions":["Q-VERIFICATION-DOCS-001@13"],"previous_event_hash":"b6700a0e6573c7e67dd40ec9a84a8dc6973c588014eb96f6ca3d3342e3005f68","previous_snapshot_hash":"acf0f25dfdfa4213ccf1e6d31d07d601e9b11e18b7c5214aa5b1e6e2f5ac892e","recorded_at":"2026-09-30T08:36:30.547062+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":13,"snapshot_hash":"568c6db220bb0eedb768ece48ba26a8e0d2040e1ead7c45fa473ffcc2982f282","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-009","DEC-009","DISC-007","REQ-014"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-009","DEC-009","DISC-007","REQ-014"],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"1187a2442ffbcf829a7d51ada62bebcb5ab3002b1f904822e7c8e2eda0fa527e","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"a1878c3a8797143879d383fe46a8d2b62788ea6cc16b1748b61e777a4a568560","previous_snapshot_hash":"568c6db220bb0eedb768ece48ba26a8e0d2040e1ead7c45fa473ffcc2982f282","recorded_at":"2026-09-30T10:28:59.492726+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":14,"snapshot_hash":"baf5ace09554e23ab12f16c313290129dae1a737f79e418737199a38c12ba55a","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-004","REQ-007","REQ-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":["AC-004"],"added_ids":[],"changed_ids":["AC-004","REQ-007","REQ-013"],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"4f3b59b909274767eb2b63576528325c82ea4048a24c05583aa1576651103b45","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"1187a2442ffbcf829a7d51ada62bebcb5ab3002b1f904822e7c8e2eda0fa527e","previous_snapshot_hash":"baf5ace09554e23ab12f16c313290129dae1a737f79e418737199a38c12ba55a","recorded_at":"2026-10-02T01:03:21.128283+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":15,"snapshot_hash":"29753d015c4c52be1e9e250803f012ad6a60849cc77f88bba5ed6b18493bf47d","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"f691c3a1f52f0f5ca2f6631d5043b2742627f0e22f33e9ab34d5c988cac74f2a","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"4f3b59b909274767eb2b63576528325c82ea4048a24c05583aa1576651103b45","previous_snapshot_hash":"29753d015c4c52be1e9e250803f012ad6a60849cc77f88bba5ed6b18493bf47d","recorded_at":"2026-10-02T02:10:22.145587+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":16,"snapshot_hash":"85075d0be71481328dcd0f4c35e30f4c156d54fb82c6808a722e2a921bce687b","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"32221e7e9ca87832df79c3027205d1c95f4573ad378879aeb74b2fbb4e010616","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"f691c3a1f52f0f5ca2f6631d5043b2742627f0e22f33e9ab34d5c988cac74f2a","previous_snapshot_hash":"85075d0be71481328dcd0f4c35e30f4c156d54fb82c6808a722e2a921bce687b","recorded_at":"2026-10-02T02:10:39.689685+00:00","relationships":[],"revision":16,"snapshot_hash":"862006203ea885e9d4006658d64e9bdc5fe8548085ff178e3c2009b2ea271b6b","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"baseline_contract_hash":"82a4b09e7590347da77580b12bdcf43f768c55c766ad3f2910738367087bcebe","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"4797c3df535760bca61692347c1d7716c08ccb3deb92d46def1525004e1faac6","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"32221e7e9ca87832df79c3027205d1c95f4573ad378879aeb74b2fbb4e010616","previous_snapshot_hash":"862006203ea885e9d4006658d64e9bdc5fe8548085ff178e3c2009b2ea271b6b","recorded_at":"2026-10-02T02:10:58.138284+00:00","relationships":[],"revision":17,"snapshot_hash":"62be44e0cba1ca326ca3c8ed3f76a05d152e7957286d91d33315da8fcdf7470e","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"d186df35792c5b25e0613fac23b47dcb5a9dd760c1ff8e40527d58a41dae8c6f","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"4797c3df535760bca61692347c1d7716c08ccb3deb92d46def1525004e1faac6","previous_snapshot_hash":"62be44e0cba1ca326ca3c8ed3f76a05d152e7957286d91d33315da8fcdf7470e","recorded_at":"2026-10-02T02:11:23.730412+00:00","relationships":[],"revision":17,"snapshot_hash":"dd0c66c44d1541eaf5af795cd21e5c9659db137fd17100e5e82610fac24625aa","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"baseline_contract_hash":"82a4b09e7590347da77580b12bdcf43f768c55c766ad3f2910738367087bcebe","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"03c6233530cc4f2d4c0ad9d30ddb313c1293c132598975fbbb8c496e6f2e7763","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"d186df35792c5b25e0613fac23b47dcb5a9dd760c1ff8e40527d58a41dae8c6f","previous_snapshot_hash":"dd0c66c44d1541eaf5af795cd21e5c9659db137fd17100e5e82610fac24625aa","recorded_at":"2026-10-02T02:15:01.469881+00:00","relationships":[],"revision":18,"snapshot_hash":"d0cd03693bb10c5000f4375289f65b3b5224d1f0f6df8fd0c96e6fb99e3e3513","verdict":"BLOCKED","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009"],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"0e8e332b4b985d772f6975de3935d43f99f07615ce01ebf84d94fd043a7c75ef","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"03c6233530cc4f2d4c0ad9d30ddb313c1293c132598975fbbb8c496e6f2e7763","previous_snapshot_hash":"d0cd03693bb10c5000f4375289f65b3b5224d1f0f6df8fd0c96e6fb99e3e3513","recorded_at":"2026-10-02T02:15:02.230625+00:00","relationships":[{"relation":"refines","source":"REQ-013","target":"REQ-010"},{"relation":"refines","source":"REQ-010","target":"REQ-001"},{"relation":"refines","source":"REQ-011","target":"REQ-009"},{"relation":"refines","source":"REQ-012","target":"REQ-002"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"supersedes","source":"DEC-006","target":"DEC-003"},{"relation":"supersedes","source":"REQ-008","target":"REQ-007"},{"relation":"supersedes","source":"DEC-005","target":"DEC-004"},{"relation":"supersedes","source":"AC-005","target":"AC-004"}],"revision":19,"snapshot_hash":"7b80a8bd2836d4eec9b3eeb273fe9ae27cb9743a05a3ab3ef634aec3fef277d2","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"8a406f019ef944379d7a140e4e803891","event_hash":"19cd1e6548847d156a69c4beb615749f27ad91a85c9a6e961d37ae957f48ae42","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"0e8e332b4b985d772f6975de3935d43f99f07615ce01ebf84d94fd043a7c75ef","previous_snapshot_hash":"7b80a8bd2836d4eec9b3eeb273fe9ae27cb9743a05a3ab3ef634aec3fef277d2","recorded_at":"2026-10-02T02:15:02.950637+00:00","relationships":[],"revision":19,"snapshot_hash":"ac4f227211fa86fffe2676879b9cc0105d42ed63c8dcdb3e761e8c34445a7667","verdict":"PASS","working_id":"WORKING-SPEC-e40ab067fac8-coding-standards-migration"}
```
<!-- spec-audit:end -->
