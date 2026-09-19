---
spec_version: 1
spec_id: SPEC-0030
revision: 2
status: confirmed
change_set: governance-diagnosis-recovery
working_id: WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery
task_ref: 01a0b3c1-92b2-7401-882d-d2454d749656
---

# 通用治理能力辨識、驗收同步與自動恢復

## Problem
0.16.0 路由器以 SKILL.md 目錄名稱代表全部能力，將已整合於 architecture_cli.py layout 的 test-validation-layout 誤報為缺失。另一個獨立問題是 SPEC 新增 AC 後，機器可讀驗收對照未同步，直到後續路由才顯示阻擋。單純輸出 BLOCKED 沒有安排修復、重驗與恢復步驟，導致可處理的缺口仍中斷工作。

調查案例是 env_sensing SPEC-0058 第 6 版：AC-006～AC-008 已有驗證方法，但 acceptance JSON 僅含 AC-001～AC-005；實際 layout CLI 已執行，結果是缺少 validation/layout.yaml。此案例只作回歸依據，不構成本次修改該專案的授權。

## Solution
沿用現有 router、spec-governance、project validation adapter 及工作狀態機，區分技能清單、可執行能力與驗證結果。SPEC 變更時立即呈現驗收規劃差異，遇到阻擋則接續診斷、授權範圍內修復、重驗與恢復。主動完成能確定的部分，只詢問真正需要使用者決定的部分。

## User Stories
- 使用者只需描述工作；治理工具能找出實際檢查入口，不因技能名稱與內建能力名稱不同而誤報。
- 使用者修改 SPEC 後，立即知道驗收對照缺什麼，不需要等到執行時才發現。
- 工作受阻時，使用者能看見正在修復的項目、仍可進行的工作及恢復条件。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 分開技能探索、能力解析與檢查結果。test-validation-layout 明確解析至已存在的 architecture_cli.py layout；不得以存在同名 SKILL.md 作為必要條件，也不得僅因檔案存在就宣稱能力可用。沿用有效的既有 CLI 執行結果，避免無必要重複掃描。 |
| REQ-002 | 能力確認須核對入口、輸出契約及退出碼。有效 PASS、FAIL 或 BLOCKED 都證明入口可呼叫，但只 PASS 表示該檢查通過；缺少相依能力仍以具體診斷記錄。缺失入口、依賴載入失敗、逾時、非法輸出及退出碼不一致，須與專案設定缺口、驗證失敗分開。保留呼叫端明確能力限制，不能以自動探索擴大授權或可用能力集合。 |
| REQ-003 | SPEC 建立、reconcile、materialize 及恢復時，比對當前候選 AC 與驗收對照。辨識新增、刪除及語意變更，回報受影響 AC ID、檔案與原因；相同 ID 的需求引用、條件或驗證方法變更也需重新評估。保留未受影響資料，不把舊證據套用到新契約。 |
| REQ-004 | 分別呈現規格儲存/確認狀態、驗證規劃完整性與執行/驗收就緒狀態。允許保存需求與待修復規劃，不因缺少驗收映射而阻止討論保存；缺漏不得被描述為整體就緒，依賴該規劃的執行與驗收必須維持阻擋。 |
| REQ-005 | 每項阻擋附結構化診斷：問題類別、來源及證據、受影響範圍、修復建議、授權需求、重驗命令或可重現步驟、成功條件與恢復目標。保留原始 gate 診斷與 PASS/FAIL/BLOCKED 語意；未知原因須繼續調查，不能強制歸類為產品失敗。 |
| REQ-006 | 主動完成可從現有資料確定的調查與修復。在既有授權範圍內且不改變已確認契約時，修復後自動重驗；尚未取得修改授權時先完成可檢視的修復內容與影響。只有缺少無法查得的決策、授權或外部條件時才詢問，並合併已知必要資訊，避免同一授權重複詢問。 |
| REQ-007 | SPEC 已明確定義且可無歧義推導的驗證映射，可在授權範圍內同步；不明確的門檻、方法、依賴、模組歸屬或範圍須交回決策。禁止虛構驗證方法、降低門檻、忽略失敗、偽造證據或以 host 證據替代必要的 target/runtime 證據。 |
| REQ-008 | 以現有 task/working reference、revision/hash 綁定恢復狀態，保存阻擋、修復/重驗證據、受影響步驟及下一個恢復位置。只暫停有依賴的工作，繼續互不依賴且已授權的工作；恢復前重讀狀態，過期規格或新決策不得沿用舊執行權限。不得建立第二套互相矛盾的權威狀態。 |
| REQ-009 | 同一問題及相同輸入下，不得無新證據或修復便重複執行相同失敗動作。具體重試需記錄新輸入、修復或可恢復暫時性原因，並使用明確有限次數及時間界限。耗盡後停止該分支，保存證據、剩餘條件與恢復步驟；禁止無限重試或把未解除阻擋標成成功。 |
| REQ-010 | 同步 ask-matt、spec-governance、engineering-risk-routing、clarify-improvement-proposals 與實際受影響的交接/驗證契約及人類文件。保留既有公開欄位與退出碼語意；新增診斷/恢復欄位須有明確 schema 與舊狀態相容處理，不偽造舊記錄。驗證原始碼與組裝後插件均能重現相同行為。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 本次僅修改通用技能與治理工具；被調查的使用者專案只提供案例。 |
| DEC-002 | 採用「主動完成能確定的部分，只把真正需要決定的部分交回使用者」，不採每次缺口固定要求確認。 |
| DEC-003 | 錯誤分類必須導向修復與恢復，保留必要阻擋而不放寬驗收。 |
| DEC-004 | 沿用既有生命週期與權威工作狀態；規格保存與產品修改權限分離。 |

## Discussion Context
### DISC-001: 確認通用範圍
- **Situation:** 原專案被用來調查能力誤報及 AC 不同步。
- **Question:** 修改對象是原專案還是通用技能？
- **Options and tradeoffs:** 原專案補設定只解決單一案例；通用技能修正可避免其他專案重現。
- **Explicit rationale:** 保存使用者已確認之需求、授權邊界及接續原則，避免重複詢問或任意放行。
- **User answer:** 目前不是都在討論通用技能的事情?
- **Decision:** DEC-001。
- **Resulting impact:** REQ-001～REQ-010 皆以通用治理為範圍。

### DISC-002: 阻擋後接續
- **Situation:** 僅分類錯誤仍可能停在 BLOCKED。
- **Question:** 分類後如何繼續？
- **Options and tradeoffs:** 保留必要阻擋並自動修復可確定部分；直接忽略阻擋會破壞驗收可信度。
- **Explicit rationale:** 保存使用者已確認之需求、授權邊界及接續原則，避免重複詢問或任意放行。
- **User answer:** 能夠區分這些錯誤訊息後，後續該如何繼續進行，不能卡住在哪邊。
- **Decision:** DEC-003、DEC-004。
- **Resulting impact:** REQ-005、REQ-008、REQ-009。

### DISC-003: 自動處理邊界
- **Situation:** 已比較固定修復清單、每次修復包確認、預先約定範圍及依已確認契約判定等選項，並說明實例。
- **Question:** 是否主動完成可確定部分，只詢問真正的決策？
- **Options and tradeoffs:** 自動完成已授權且明確的修復可減少中斷；不明確契約仍需使用者決定，以免擅自改需求。
- **Explicit rationale:** 保存使用者已確認之需求、授權邊界及接續原則，避免重複詢問或任意放行。
- **User answer:** 對。
- **Decision:** DEC-002。
- **Resulting impact:** REQ-006、REQ-007。

### DISC-004: 正式建檔
- **Situation:** 使用者確認無其他核心待決事項後要求建立正式規格。
- **Question:** 本次要完成什麼交付？
- **Options and tradeoffs:** 建立可檢查的正式 SPEC，實作另依既有執行授權規則接續。
- **Explicit rationale:** 保存使用者已確認之需求、授權邊界及接續原則，避免重複詢問或任意放行。
- **User answer:** 建立正式SPEC。
- **Decision:** DEC-004。
- **Resulting impact:** 保存 REQ-001 至 REQ-010 及驗收方式；不代表產品實作授權。

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | 沒有同名 SKILL.md 但有有效 layout 結果時不誤報能力缺失；有效 FAIL/BLOCKED 保留原 gate 結果；明確能力限制仍生效。 | 能力解析單元測試及 CLI 路由整合測試。 | PENDING |
| AC-002 | REQ-002, REQ-005 | 入口缺失、依賴失敗、逾時、非法 JSON、退出碼不符、設定缺失、產品違規各自得到正確診斷與下一步，不被誤報 PASS。 | 可控 subprocess fixtures 與真實 CLI 暫存專案。 | PENDING |
| AC-003 | REQ-003, REQ-004 | 從五項 AC 增加到八項時立即列出三項缺漏；刪除及相同 ID 語意變更均可偵測；保存成功與規劃受阻同時正確呈現。 | SPEC 生命周期整合測試；核對輸出與持久化內容。 | PENDING |
| AC-004 | REQ-006, REQ-007 | 已授權明確修復自行完成並重驗；未授權時只產出修復內容；不明門檻提出決策；不重問既有授權，不偽造方法與證據。 | 合成多回合工作流程 fixtures 與權限/副作用斷言。 | PENDING |
| AC-005 | REQ-008 | 受阻分支暫停而獨立分支繼續；修復通過後回到原步驟；跨回合恢復與規格過期可正確辨識。 | 保存/重載整合測試，檢查 task、revision/hash 及下一步。 | PENDING |
| AC-006 | REQ-009 | 相同失敗不無限重試；有限暫時性重試耗盡後保存待恢復狀態；新修復才重啟相關驗證。 | 假時鐘、執行次數斷言、失敗序列及恢復案例。 | PENDING |
| AC-007 | REQ-010 | 舊狀態可安全讀取；新契約通過 schema 檢查；技能及 docs 一致；組裝後插件通過同一能力與恢復回歸。 | 契約/文件檢查、插件組裝、發行包驗證與整合測試。 | PENDING |
| AC-008 | REQ-003, REQ-005, REQ-007, REQ-010 | 使用合成 SPEC-0058 類型案例同時重現能力誤報、AC 缺漏及 layout 設定缺失；逐項修復不會掩蓋其餘阻擋，不讀寫真實案例專案。 | 隔離暫存專案端到端 CLI 回歸，核對診斷及檔案副作用。 | PENDING |

## Relationships
| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-004 | depends_on | REQ-003 |
| REQ-006 | depends_on | DEC-002 |
| REQ-007 | refines | REQ-006 |
| REQ-008 | depends_on | REQ-005 |
| REQ-009 | refines | REQ-008 |
| REQ-010 | depends_on | DEC-004 |

## Implementation and Validation Plan
1. 建立可重現原缺陷的隔離 fixtures；以 Python 3 執行相關 unittest，保存命令、退出碼及診斷 JSON。
2. 修正能力解析及分類，再驗證有效結果與故障矩陣；依既有公開輸出契約加入必要欄位。
3. 接入候選 SPEC 的驗收差異檢查；保存不得依賴執行授權，修復產品/設定則仍依授權。
4. 在既有工作狀態中加入修復與恢復資料，驗證權限、過期資料、分支及有限重試。
5. 同步技能、docs、schema 與必要架構描述；執行相關完整回歸、架構公開 gate 及 deterministic views 檢查。
6. 使用經確認的 Python 3 執行 `scripts/assemble_plugin.py assemble --marketplace-publication` 與 `scripts/validate_distribution.py`，對組裝後插件執行相同整合案例。此步驗證發行包，不自動發布或安裝。

每項 AC 必須有測試斷言、退出碼及可追溯結果；目前全部 PENDING。實作時在 validation/ 建立此 SPEC 的驗收對照，測試置於 tests/ 既有 Module/Flow 歸屬，生成證據使用 artifacts/ 唯一 run；不以建置成功替代行為驗證。

## Impact and Tradeoffs
受影響範圍為治理路由、規格生命週期、驗證介接與管理流程；沿用現有模組邊界及單一權威狀態。新增分類與恢復契約會增加測試及相容性維護成本，換取可觀察的接續行为。演算法屬確定性的能力解析、AC 差異及狀態轉移；需以反例驗證優先順序與分支，不涉及數值最佳化、排程或硬體效能主張。實作前依架構治理確認實際 symbol/owner 和必要 manifest/generated view 差異。

## Out of Scope
原專案 SPEC-0058、驗收對照及 layout 設定修復；韌體、設備操作、全域 Python 修改；降低驗收門檻；繞過 managed admission；插件安裝、發布、Git 提交；另個任務 SPEC-0029 的方案入口修改。

## Open Decisions
None.

## Routing/Gates
本次為 spec-only 保存；產品修改尚未授權。實作前須通過本 SPEC 驗證、formatter/architecture 等適用 gate。阻擋只限制依賴動作，允許唯讀調查與規格保存。相關 runtime 指通用工具在主機上的真實 CLI 行為，不要求實體裝置驗證。

## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-18 | 依本任務已確認討論建立通用能力辨識、驗收同步、診斷修復重驗恢復與授權邊界。 |

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

- 01a0b500-9da6-7352-ae72-801f6c530932: 完成 SPEC-0029/0030 原始碼、skill 與人類文件修改。單檔工作 SPEC、持續保存、完整性審查、自動確認、舊雙檔驗證遷移；能力與 gate 結果分離、AC 新增刪除與同 ID 語意差異、criterion_sha256、結構化診斷及有限恢復；組合 SPEC 授權完整綁定。SPEC0029 r22 和 SPEC0030 r2 僅補上派生閱讀視圖，未變更確認需求。來源與補存額度保留。插件回歸 308 項 PASS: artifacts/tests/e25d227a3eaf418298d8deabe2e48178/manifest.json；驗證規劃 31 項 PASS: artifacts/tests/536b8233fc6e432cbaaed0aba51aa918/manifest.json；封裝 38 項中 36 PASS/2 skipped: artifacts/tests/5091a3291a4a43e493039f03fc6d300d/manifest.json。實際當前來源事件組合授權 admission 已 PASS（非宿主認證）。未執行安裝、信任變更、提交或發布。真實桌面 hook firing、多輪 trace 與完整 AC 驗收仍未證明，不能以單元測試代替。狀態保持 confirmed，未標記 implemented。
- 01a0b54d-1aaa-7390-a0c3-a7cd312b2df2: 使用者明確授權安裝測試版並測試。已用目前桌面實際 runtime 0.155.0-alpha.9 的 plugin add 成功安裝 governed-engineering-skills@governed-engineering-development 0.16.0+codex.local-20260918161704513960，快取內容雜湊293檔一致。以該安裝快取執行 Windows launcher/owner smoke：初始化、工程分類、單檔保存、正確回覆Stop、漏存最多一次修復、Python缺失拒絕，共4檢查PASS。不可冒稱真實桌面事件觸發。證據 artifacts/tests/116bbe01f01040cf927b4b1729f11667/manifest.json；spec-governance/installed-package-test.json。用相同桌面runtime app-server hooks/list只讀查詢，四事件sessionStart/userPromptSubmit/preToolUse/stop loaded enabled但全部untrusted。未修改信任、未使用bypass。真實桌面驗收仍BLOCKED等待宿主hook審閱/信任。當前任務cwd在父目錄，測試需以實際repo根C:/Users/hugo_peng/skill/skills開新任務以匹配紀錄/Python。已開啟插件頁並排入hook定義檢視。正式release未替換，未提交發布。

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"cba7bfdf3b8645d0eea2caa233c1912e8244671995198fe66ce736d7a6fbebb9","event_type":"start","event_version":1,"open_decisions":[],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-18T09:42:23.937336+00:00","relationships":[{"relation":"depends_on","source":"REQ-001","target":"DEC-001"},{"relation":"depends_on","source":"REQ-004","target":"REQ-003"},{"relation":"depends_on","source":"REQ-006","target":"DEC-002"},{"relation":"refines","source":"REQ-007","target":"REQ-006"},{"relation":"depends_on","source":"REQ-008","target":"REQ-005"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"depends_on","source":"REQ-010","target":"DEC-004"}],"revision":1,"snapshot_hash":"2fb89ee340b180ea299434a149606331d28934efce442045c389175ef769a20c","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"0c11eb457c7aa970f7efef6f0248f29c42ffa60801c1c4679b5e9b3e406d7842","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"cba7bfdf3b8645d0eea2caa233c1912e8244671995198fe66ce736d7a6fbebb9","previous_snapshot_hash":"2fb89ee340b180ea299434a149606331d28934efce442045c389175ef769a20c","recorded_at":"2026-09-18T09:42:31.289379+00:00","relationships":[],"revision":1,"snapshot_hash":"aa3a8b0503b9f1182a0eed768dd73ebc378c5e0da90527c499b1a52e3d8d59a4","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"baseline_contract_hash":"95ac8100333aae7e917ef32aa2d7763fbe8d542462068aa541d5595f4934f98f","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"c3cac3e25f210804f043d511812df47dacdcc5290f128d8eec3e5e0bde890932","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"0c11eb457c7aa970f7efef6f0248f29c42ffa60801c1c4679b5e9b3e406d7842","previous_snapshot_hash":"aa3a8b0503b9f1182a0eed768dd73ebc378c5e0da90527c499b1a52e3d8d59a4","recorded_at":"2026-09-18T15:37:55.837111+00:00","relationships":[],"revision":1,"snapshot_hash":"199e3d84b2e6a7ef0fa48835d517648475cf8b326213bab0e2ed5628b8fbef05","verdict":"BLOCKED","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"legacy_journal":"spec-governance/WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery.journal.jsonl","legacy_notes":[],"legacy_snapshot":"spec-governance/WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery.md","removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"135e72c3118da8a87ace7bc5e5755e300c7bf738a0bb872a75bd8c2beb3bc1e4","event_type":"migration","event_version":1,"open_decisions":[],"previous_event_hash":"c3cac3e25f210804f043d511812df47dacdcc5290f128d8eec3e5e0bde890932","previous_snapshot_hash":"199e3d84b2e6a7ef0fa48835d517648475cf8b326213bab0e2ed5628b8fbef05","recorded_at":"2026-09-18T15:37:55.854049+00:00","relationships":[],"revision":1,"snapshot_hash":"199e3d84b2e6a7ef0fa48835d517648475cf8b326213bab0e2ed5628b8fbef05","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"a8999392f2353c441ac3cc74a5a3bbfcbde84b991bfc4c8b3e38d3d08eaaa88f","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"135e72c3118da8a87ace7bc5e5755e300c7bf738a0bb872a75bd8c2beb3bc1e4","previous_snapshot_hash":"199e3d84b2e6a7ef0fa48835d517648475cf8b326213bab0e2ed5628b8fbef05","recorded_at":"2026-09-18T15:50:11.871710+00:00","relationships":[{"relation":"depends_on","source":"REQ-001","target":"DEC-001"},{"relation":"depends_on","source":"REQ-004","target":"REQ-003"},{"relation":"depends_on","source":"REQ-006","target":"DEC-002"},{"relation":"refines","source":"REQ-007","target":"REQ-006"},{"relation":"depends_on","source":"REQ-008","target":"REQ-005"},{"relation":"refines","source":"REQ-009","target":"REQ-008"},{"relation":"depends_on","source":"REQ-010","target":"DEC-004"}],"revision":2,"snapshot_hash":"ea49be63c40e09752d2e8a3206f36e54c0ea62cca5859af425abd7e5b0ecd33e","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"74ea3f54373fee401844f936a23d456875a46dfa4bc8df5c1f1cabd9fb806de1","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"a8999392f2353c441ac3cc74a5a3bbfcbde84b991bfc4c8b3e38d3d08eaaa88f","previous_snapshot_hash":"ea49be63c40e09752d2e8a3206f36e54c0ea62cca5859af425abd7e5b0ecd33e","recorded_at":"2026-09-18T15:50:11.974683+00:00","relationships":[],"revision":2,"snapshot_hash":"caca5112bcf8fe9e041a9c938244676a5bdd5162f6102459cc3d1e90206c678b","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"kind":"verification-summary","source_ref":"01a0b500-9da6-7352-ae72-801f6c530932","summary":"完成 SPEC-0029/0030 原始碼、skill 與人類文件修改。單檔工作 SPEC、持續保存、完整性審查、自動確認、舊雙檔驗證遷移；能力與 gate 結果分離、AC 新增刪除與同 ID 語意差異、criterion_sha256、結構化診斷及有限恢復；組合 SPEC 授權完整綁定。SPEC0029 r22 和 SPEC0030 r2 僅補上派生閱讀視圖，未變更確認需求。來源與補存額度保留。插件回歸 308 項 PASS: artifacts/tests/e25d227a3eaf418298d8deabe2e48178/manifest.json；驗證規劃 31 項 PASS: artifacts/tests/536b8233fc6e432cbaaed0aba51aa918/manifest.json；封裝 38 項中 36 PASS/2 skipped: artifacts/tests/5091a3291a4a43e493039f03fc6d300d/manifest.json。實際當前來源事件組合授權 admission 已 PASS（非宿主認證）。未執行安裝、信任變更、提交或發布。真實桌面 hook firing、多輪 trace 與完整 AC 驗收仍未證明，不能以單元測試代替。狀態保持 confirmed，未標記 implemented。","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b500-9d21-7001-b6f9-aa12d74a43c0"},"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"e43fe41770c1e374a8eb1982a8c3033cbce8944843f7ff899b21592c613d82e3","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"74ea3f54373fee401844f936a23d456875a46dfa4bc8df5c1f1cabd9fb806de1","previous_snapshot_hash":"caca5112bcf8fe9e041a9c938244676a5bdd5162f6102459cc3d1e90206c678b","recorded_at":"2026-09-18T15:51:02.956593+00:00","relationships":[],"revision":2,"snapshot_hash":"caca5112bcf8fe9e041a9c938244676a5bdd5162f6102459cc3d1e90206c678b","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"kind":"installation-test-summary","source_ref":"01a0b54d-1aaa-7390-a0c3-a7cd312b2df2","summary":"使用者明確授權安裝測試版並測試。已用目前桌面實際 runtime 0.155.0-alpha.9 的 plugin add 成功安裝 governed-engineering-skills@governed-engineering-development 0.16.0+codex.local-20260918161704513960，快取內容雜湊293檔一致。以該安裝快取執行 Windows launcher/owner smoke：初始化、工程分類、單檔保存、正確回覆Stop、漏存最多一次修復、Python缺失拒絕，共4檢查PASS。不可冒稱真實桌面事件觸發。證據 artifacts/tests/116bbe01f01040cf927b4b1729f11667/manifest.json；spec-governance/installed-package-test.json。用相同桌面runtime app-server hooks/list只讀查詢，四事件sessionStart/userPromptSubmit/preToolUse/stop loaded enabled但全部untrusted。未修改信任、未使用bypass。真實桌面驗收仍BLOCKED等待宿主hook審閱/信任。當前任務cwd在父目錄，測試需以實際repo根C:/Users/hugo_peng/skill/skills開新任務以匹配紀錄/Python。已開啟插件頁並排入hook定義檢視。正式release未替換，未提交發布。","task_ref":"01a0b3c1-92b2-7401-882d-d2454d749656","turn_id":"01a0b54d-19e8-7912-b91c-9d50e22b92ac"},"removed_ids":[]},"epoch":"a5319a65be77444ba44ef2ff8159a1f1","event_hash":"fa3a9bbaf7873f16622165b52328c2b411c9b1ed8099cd51bd1983bd4c4ecfae","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"e43fe41770c1e374a8eb1982a8c3033cbce8944843f7ff899b21592c613d82e3","previous_snapshot_hash":"caca5112bcf8fe9e041a9c938244676a5bdd5162f6102459cc3d1e90206c678b","recorded_at":"2026-09-18T16:24:37.387078+00:00","relationships":[],"revision":2,"snapshot_hash":"caca5112bcf8fe9e041a9c938244676a5bdd5162f6102459cc3d1e90206c678b","verdict":"PASS","working_id":"WORKING-SPEC-1fe31cd056d3-governance-diagnosis-recovery"}
```
<!-- spec-audit:end -->
