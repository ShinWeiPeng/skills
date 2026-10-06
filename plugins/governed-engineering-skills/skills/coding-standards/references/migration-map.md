# Migration record

Source baseline: SPEC-0040; additions/refinements: SPEC-0041. Workflow/format moves retain their own owners.

| Rule ID | Original source |
|---|---|
| MOD-DEP-001 | core-standard / Dependency rules 1 |
| MOD-DEP-002 | core-standard / Dependency rules 2 |
| MOD-DEP-003 | core-standard / Dependency rules 3 |
| MOD-DEP-004 | core-standard / Dependency rules 4 |
| MOD-DEP-005 | core-standard / Dependency rules 5 |
| MOD-DEP-006 | core-standard / Dependency rules 6 |
| MOD-DEP-007 | core-standard / Dependency rules 7 |
| MOD-DEP-008 | core-standard / Dependency rules 8 |
| MOD-LEVEL-001 | core-standard / Levels L0 |
| MOD-LEVEL-002 | core-standard / Levels L1 |
| MOD-LEVEL-003 | core-standard / Levels L2 |
| MOD-LEVEL-004 | core-standard / Levels L3+ |
| MOD-LEVEL-P001 | core-standard / Levels prose |
| MOD-LEVEL-P002 | core-standard / Levels prose |
| TYPE-001 | core-standard / Named-type ownership 1 |
| TYPE-002 | core-standard / Named-type ownership 4 |
| TYPE-003 | core-standard / Named-type ownership 5 |
| TYPE-004 | core-standard / Named-type ownership 6 |
| TYPE-005 | core-standard / Named-type ownership 7 |
| MOD-MAP-001 | core-standard / Contract and mapping rules 1 |
| MOD-MAP-002 | core-standard / Contract and mapping rules 2 |
| MOD-MAP-003 | core-standard / Contract and mapping rules 3 |
| MOD-MAP-004 | core-standard / Contract and mapping rules 4 |
| MOD-MAP-005 | core-standard / Contract and mapping rules 5 |
| STATE-001 | core-standard / Runtime-state ownership 1 |
| STATE-002 | core-standard / Runtime-state ownership 2 |
| STATE-003 | core-standard / Runtime-state ownership 3 |
| STATE-004 | core-standard / Runtime-state ownership 4 |
| STATE-005 | core-standard / Runtime-state ownership 5 |
| STATE-006 | core-standard / Runtime-state ownership 6 |
| STATE-007 | core-standard / Runtime-state ownership 7 |
| TYPE-006 | core-standard / Choose owner |
| MOD-META-001 | core-standard / Description and navigation |
| FLOW-INPUT-001 | event-contract / Inputs |
| FLOW-OUTPUT-001 | event-contract / Outputs |
| FLOW-FANOUT-001 | event-contract / Fan-out 1 |
| FLOW-FANOUT-002 | event-contract / Fan-out 2 |
| FLOW-FANOUT-003 | event-contract / Fan-out 3 |
| FLOW-FANOUT-004 | event-contract / Fan-out 4 |
| FLOW-FANOUT-005 | event-contract / Fan-out 5 |
| FLOW-EVENT-001 | event-contract / Event envelope |
| FLOW-LIFE-001 | event-contract / Lifecycle |
| FLOW-DELIVERY-001 | event-contract / Delivery |
| MEM-ALLOC-001 | SPEC-0041 / adopted rule draft |
| MEM-CAP-001 | SPEC-0041 / adopted rule draft |
| MEM-OWNER-001 | SPEC-0041 / adopted rule draft |
| MEM-LIFE-001 | SPEC-0041 / adopted rule draft |
| BND-CHECK-001 | SPEC-0041 / adopted rule draft |
| ERR-PROTECT-001 | SPEC-0041 / adopted rule draft |
| ERR-REPORT-001 | SPEC-0041 / adopted rule draft |
| ERR-QUEUE-001 | SPEC-0041 / adopted rule draft |
| ERR-STATE-001 | SPEC-0041 / adopted rule draft |
| ERR-RECOVER-001 | SPEC-0041 / adopted rule draft |
| ERR-RESULT-001 | SPEC-0041 / adopted rule draft |
| FLOW-BOUND-001 | SPEC-0041 / adopted rule draft |
| FLOW-BATCH-001 | SPEC-0041 / adopted rule draft |
| FLOW-STOP-001 | SPEC-0041 / adopted rule draft |
| FLOW-FANIN-001 | SPEC-0041 / adopted rule draft |
| FLOW-FANOUT-006 | SPEC-0041 / adopted rule draft |
| FLOW-SHARE-001 | SPEC-0041 / adopted rule draft |
| FLOW-SOURCE-001 | SPEC-0041 / adopted rule draft |
| MOD-CONTRACT-001 | SPEC-0041 / adopted rule draft |
| API-COMPLETE-001 | SPEC-0041 / adopted rule draft |
| API-ACCESS-001 | SPEC-0041 / adopted rule draft |
| EXEC-OPT-001 | execution-efficiency / Tier 0 |
| EXEC-OPT-002 | execution-efficiency / Tier 0 |
| MOD-OBS-001 | runtime-validation / Boundaries 1 |
| MOD-OBS-002 | runtime-validation / Boundaries 2 |
| MOD-OBS-003 | runtime-validation / Boundaries 3 |
| MOD-OBS-004 | runtime-validation / Boundaries 4 |
| EXEC-OBS-001 | runtime-validation / High-frequency instrumentation |

The former accepted-command completion restriction is explicitly refined by API-COMPLETE-001 (SPEC-0041), not silently changed during migration.

| MOD-DEP-009 | core-standard / Dependency rules 7; mandatory cycle prohibition separated from the adapter permission |

MIG-039 accepted asynchronous work and synchronous queries are now covered by API-COMPLETE-001 under SPEC-0041. FLOW-INPUT-001 retains admission and immediate rejection. FLOW-EVENT-001 includes both envelope and conditional reliability metadata; FLOW-DELIVERY-001 includes all three delivery cases. These consolidations retain each condition. Execution design and runtime checks use the renamed references; algorithm/flow record formats remain separate.

## Source-clause checklist

The following 69 entries retain the source-clause scope from the confirmed migration SPEC. Current file names are resolved below; the earlier table gives actual rule IDs. Event completion is the explicit SPEC-0041 refinement, not an unnoticed migration change.

| Migration ID | Original scope | Responsibility and retained conditions |
|---|---|---|
| MIG-001 | core-standard / Rule levels 三項 | rule-versioning：強度含義；architecture-exception-policy：偏離及核准；每條規則保留強度欄 |
| MIG-002 | core / Levels：L0、L1、L2、L3+ 表與責任段 | module-boundaries / MOD-LEVEL-001..004、MOD-LEVEL-P001/P002；層級是語意，不要求空資料夾 |
| MIG-003 | core / Dependency rules 1 | module-boundaries / MOD-DEP-001：L1/L2 parent |
| MIG-004 | 同章 2 | MOD-DEP-002：兄弟依賴與父層協調 |
| MIG-005 | 同章 3 | MOD-DEP-003：L0/L1 公開契約方向 |
| MIG-006 | 同章 4 | MOD-DEP-004：組裝具體 adapter 的允許用途 |
| MIG-007 | 同章 5 | MOD-DEP-005：功能模組不得依賴具體外部技術或外洩框架型別 |
| MIG-008 | 同章 6 | MOD-DEP-006：需求側擁有 port |
| MIG-009 | 同章 7 | MOD-DEP-007（adapter 依賴許可）及 MOD-DEP-009（禁止循環） |
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
| MIG-039 | event-contract / Inputs | data-flow / FLOW-INPUT-001：typed admission／立即拒絕；API-COMPLETE-001：SPEC-0041 明確修訂後的同步完成及非同步接受／完成 |
| MIG-040 | event / Outputs 首段 | FLOW-OUTPUT-001：單一 sink、父層/adapter fan-out |
| MIG-041 | event / Fan-out 1..5 | FLOW-FANOUT-001..005：lock 外呼叫、失敗繼續、順序、匯總錯誤、不能假回滾 |
| MIG-042 | event / Event envelope | FLOW-EVENT-001：六欄、可信 clock 條件與 at-least-once metadata；schema 僅描述結構 |
| MIG-043 | event / Lifecycle | FLOW-LIFE-001：commit-before-publish、同 stream 序列且不可重入、跨 stream 可並行；狀態圖保留條件 |
| MIG-044 | event / Delivery 三項 | FLOW-DELIVERY-001：預設 at-most、重試/持久化 at-least、exactly-once 證明及 ADR |
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

## Current destination files

- Architecture design/check/exception: govern-modular-event-architecture/references/architecture-design-workflow.md, architecture-check-workflow.md and architecture-exception-policy.md.
- Execution and runtime: execution-design-workflow.md and runtime-checks.md; scheduling formulas remain in realtime-scheduling-analysis.md.
- Algorithms: algorithm-design-workflow.md and algorithm-record-format.md.
- Flow review: flow-cost-checks.md and flow-review-format.md.
- C port shape: event-port-example.md.
- General ADR trigger/examples: domain-modeling/SKILL.md; shared format/workflow/checks: plugin references/adr.
- Codebase-design vocabulary and DEEPENING remain professional design heuristics, with formal rules referenced from coding-standards.

The destination names above resolve the workflow/format shorthand used in the source checklist. Schema descriptions, scheduling formulas, analyzer capabilities and test storage policies retain their existing owners; they are not duplicate editable program-rule catalogs.
