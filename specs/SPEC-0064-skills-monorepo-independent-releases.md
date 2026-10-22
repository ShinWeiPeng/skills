---
spec_version: 1
spec_id: SPEC-0064
revision: 17
status: confirmed
change_set: skills-monorepo-independent-releases
working_id: WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases
task_ref: 01a16186-7170-76d2-9ee2-dd2fcd07d43f
---
# Skills monorepo 與獨立 PR 升版方案

## Acceptance Criteria
以下是計畫驗收；Evidence 全部 NOT RUN，沒有實作完成或平台相容性 PASS 的宣稱。

| ID | Criterion | Requirements | Validation Method | Expected Output / Pass condition | Evidence |
| --- | --- | --- | --- | --- | --- |
| AC-001 | 一個來源 repo 中可取得兩個套件，repo URL 與 root specs canonical 路徑維持不變。 | REQ-001 | 乾淨 tracked checkout 檢查、git ls-files 目錄對照及相對連結檢查。 | 並列兩套件、只有一個 Git root，來源無遺漏與重複可編輯副本。 | NOT RUN |
| AC-002 | 工程版本、changeset 歷史、既有 tag、安裝身分與 consumer artifact 邏輯路徑保留。 | REQ-001 REQ-002 | 遷移前後組裝 inventory 比對、版本檢查、tag SHA 比對、既有安裝 fixture。 | 只有規劃內變動；無非預期版本重設或 tag 移動，原安裝入口仍成功。 | NOT RUN |
| AC-003 | 僅工程產物變更時，只產生工程 Version PR／tag／發佈更新。 | REQ-002 REQ-003 | 臨時 Git repo 與 GitHub boundary fake，注入工程 changeset/intent 後重現功能合併及升版合併。 | 文件版本、changesets、PR 及發佈 ref 均不變。 | NOT RUN |
| AC-004 | 僅文件產物變更時，只產生文件 Version PR／tag／發佈更新。 | REQ-002 REQ-003 | 同 AC-003，僅注入 doc-coauthoring 變更。 | 工程版本、changesets、PR 及發佈 ref 均不變。 | NOT RUN |
| AC-005 | 兩套件同時變更時，各自獨立版本與 Version PR；任一可先合併。 | REQ-002 REQ-003 | 兩套件 bump 等級不同且以兩種合併順序重現。 | 版本各依其 intent；未發佈者不被帶入另一套件 artifact。 | NOT RUN |
| AC-006 | root 文件不升版，共用設定驗證兩套件；產物變更缺 intent 應失敗。 | REQ-002 REQ-003 | changed-path／rename／delete／shared path／missing base／missing intent 契約 fixtures。 | 所有預期套件被檢查，未知範圍不靜默略過；純文件無發佈，缺 intent 阻擋。 | NOT RUN |
| AC-007 | 重跑與別套件的新 commit 不會重複 bump，也不因原 tag 位於較舊 commit 而錯誤失敗。 | REQ-002 REQ-003 | 同版相同 fingerprint、同版不同內容、重跑、先 tag 後 publication failure 等 fixtures。 | 相同產物不改 tag；同版不同產物阻擋；可重跑補發且保持同一版本。 | NOT RUN |
| AC-008 | 兩套件並行 PR 更新及 publication 不會相互覆蓋；競爭更新保留舊可用版本。 | REQ-002 REQ-003 | expected-base/lease 與 concurrent publication boundary fixtures。 | 正確分支被更新；過期寫入拒絕；可從記錄 SHA 回復／重試。 | NOT RUN |
| AC-009 | doc-coauthoring 只有一份可編輯流程，兩平台 manifest、版本及技能引用正確。 | REQ-004 | source inventory、YAML/JSON/schema、相對路徑、platform manifest 及版本一致性檢查。 | 同版、無失效引用，安裝產物完整。 | NOT RUN |
| AC-010 | Codex 與 Claude 均可從安裝／載入開始完成三階段文件協作。 | REQ-004 | 兩平台隔離設定實測：技術文件、提案、決策文件案例；記錄 harness/tool 版本與輸出。 | 各案例包含上下文蒐集、逐段起草修訂及獨立讀者測試；不使用不存在工具。 | NOT RUN |
| AC-011 | 無 sub-agent 或缺少必要能力時明確提供原流程人工 fallback，不虛報測試成功；工程流程不被一般文件寫作取代。 | REQ-004 | no-subagent／missing-tool fixtures 及工程技能、一般文件觸發案例對照。 | fallback 與狀態明確，工程既有治理及一般寫作邊界符合方案。 | NOT RUN |
| AC-012 | doc 上游來源、固定 commit、適配差異與適用授權完整可追溯。 | REQ-004 | UPSTREAM.md、來源檔 SHA、授權依據與差異的人工 review 加結構檢查。 | 來源與適配可重現，沒有把另一套件授權自動套用。 | NOT RUN |
| AC-013 | 全部搬移後組裝、既有測試、版本、架構及 generated-view 檢查可從乾淨 checkout 重現。 | REQ-001 REQ-002 REQ-003 REQ-004 | 延續 Windows/Ubuntu 與 Python 3.11/3.12/3.13 既有 matrix；suite assembly/validation/version、repo gate release 及 render check。 | 命令 exit 0，無失效來源路徑或過期 generated view，正式產物通過對應 release gate。 | NOT RUN |
| AC-014 | Git tracked tree 不含四類指定 root 目錄；必要 CI 來源保留且乾淨 checkout 可重建驗證設定，本機產物不刪除、不覆蓋人為修改。 | REQ-005 | Git inventory、設定產生器保護契約、原 CI matrix 與正式 release gate。 | root 無指定追蹤項目，原檢查全數通過；相容設定可重建且衝突時拒絕覆寫。 | NOT RUN |

## Decisions
| ID | Decision | Source |
| --- | --- | --- |
| DEC-001 | 後續明確 monorepo 樹狀結構取代最初兩個獨立 repo 的選擇。 | user:所以不能在ShinWeiPeng下新增skill，變成樹狀結構 |
| DEC-002 | 方案須涵蓋現有 PR 版本控管方式。 | user:因為目前是透過PR進行版本控管的 |
| DEC-003 | 採用 Q-001@2 選項 1：同時支援 Codex 與 Claude，保留原有協作流程。 | user:採用1 |
| DEC-004 | 使用者確認完整 SPEC-0064 修訂6方案並授權開始執行；平台、目錄、版本與驗收範圍維持既有完整提案。 | user:adopt-plan-start |
| DEC-005 | 本次 SPEC-0064 允許原生 Git／檔案工具補齊驗證設定並執行已核准搬移與修改；來源雜湊、範圍限制及原訂驗收維持。原開始執行授權繼續適用同一產品範圍。 | user:allow-native-tools |

| DEC-006 | 使用者要求來源 repo 僅上傳必要且需要追蹤的檔案，並指出 spec-governance、artifacts、tests/flows/plugin-integration/monorepo、validation 非必要；CI 使用中之測試與設定如何保留待 Q-004。 | user:minimal-tracked-files |
| DEC-008 | 保留必要 CI 測試與設定；非必要內容只留本機並放在對應資料夾。必要來源整理至 .github；舊工具的 validation 設定以可重建本機副本供應且拒絕覆蓋人為修改，不降低 CI 檢查。 | user:necessary-ci-locals |
| DEC-007 | 補作文件套件進入 main 的整合，完成原先相依 PR 尚未帶回 main 的部分；不回退已發布的工程 0.23.2。 | user:integrate-doc-main |

## Discussion Context
### DISC-001: 目錄與發佈範圍
- **Situation:** 使用者以後續樹狀結構修正最初兩個 repo 的回答。
- **Question:** 集中 clone 後是否可透過 PR 各自管理版本？
- **Options and tradeoffs:** 單一 repo 共享 Git 歷史與 PR 列表；套件版本、tag 及升版 PR 可分別管理。獨立 repo 則 Git 歷史也分開。
- **User answer:** 使用者確認一次 clone 兩套件，關切獨立版本與既有 PR 流程，並要求提出修改方案。
- **Explicit rationale:** 現有版本控管透過 PR。
- **Resulting impact:** REQ-001 REQ-002 REQ-003 DEC-001 DEC-002

### DISC-002: doc-coauthoring 雙平台範圍
- **Situation:** 兩個套件獨立 PR 升版已確定，doc-coauthoring 平台範圍尚待選擇。
- **Question:** doc-coauthoring 第一版是否同時支援 Codex 與 Claude，保留原有協作流程，只調整平台工具與安裝設定？
- **Options and tradeoffs:** 同時支援 Codex 與 Claude（建議）：保留原有三階段協作流程，調整平台工具與安裝設定；可在兩邊使用，但需驗證兩套平台設定。；原樣匯入 Anthropic 版本：最容易追蹤上游，先不承諾 Codex 相容；後續使用 Codex 時再另行適配。；只支援 Codex：集中驗證你目前使用的環境，但需維護與上游 Claude 版本的差異。
- **User answer:** 採用1
- **Explicit rationale:** 使用者未另行說明理由。
- **Resulting impact:** REQ-004 DEC-003

### DISC-003: 完整方案確認與執行授權
- **Situation:** 完整修訂6方案已呈現，等待整體確認。
- **Question:** 是否確認這份 SPEC-0064 的完整修改方案？確認代表方案定稿，尚不授權實作。
- **Options and tradeoffs:** 開放文字確認；沒有新增選項。確認與開始執行分別記錄。
- **User answer:** 採用方案，開始執行
- **Explicit rationale:** 使用者未另行補充理由。
- **Resulting impact:** DEC-004 REQ-001 REQ-002 REQ-003 REQ-004

### DISC-004: 本次原生工具例外
- **Situation:** 已核准方案的驗證準備與定稿入口循環依賴；現有 writer 不支援來源搬移。
- **Question:** 是否允許本次 SPEC-0064 使用原生 Git／檔案工具，補齊驗證設定並執行已核准的搬移與修改，同時保留來源雜湊檢查、範圍限制及原訂驗收？
- **Options and tradeoffs:** 開放文字授權本次工具例外；不降低原訂驗收，不修改治理器以製造 PASS。
- **User answer:** 允許
- **Explicit rationale:** 使用者未另行補充理由。
- **Resulting impact:** DEC-005 DEC-004 REQ-001 REQ-002 REQ-003 REQ-004

### DISC-005: 必要追蹤範圍
- **Situation:** 使用者檢視 GitHub 根目錄後，希望精簡來源 repo。
- **Question:** CI 測試與驗證設定是否保留並移出根目錄，或連同執行產物一起停止追蹤？
- **Options and tradeoffs:** 保留必要來源並搬到 .github 或套件內，可維持現有發版檢查；全部停止追蹤則須移除或替換相關 CI 檢查。
- **User answer:** 我認為只要上傳必要的及需要追蹤的檔案就可以了。spec-governance、artifacts、tests/flows/plugin-integration/monorepo、validation都是非必要的。
- **Explicit rationale:** 只上傳必要且需要追蹤的檔案。
- **Resulting impact:** DEC-006 REQ-001 REQ-003 AC-013；Q-004@12 待回答，尚未實施精簡。

### DISC-006: 隱藏目錄的用途
- **Situation:** 使用者也詢問為何 .github、.claude-plugin、.agents/plugins 被上傳。
- **Question:** 這些目錄是否屬於必要來源？
- **Options and tradeoffs:** .github 的發版 workflow/script 與 Codex/Claude marketplace catalog 支援既有自動升版及安裝；issue 模板與標籤自動化可獨立精簡。
- **User answer:** 還有為什麼.github、.calude-plug、.agents/plugins都上傳了
- **Explicit rationale:** 未另行說明。
- **Resulting impact:** REQ-003 REQ-004 DEC-006；本題為用途說明，不視為移除兩平台支援的決定。

### DISC-007: 文件套件回到主分支
- **Situation:** #55 已進 main；#56 合併目標仍為 codex/skills-monorepo，main 缺少文件套件。
- **Question:** 使用者註記要求一併處理未完成的 main 整合。
- **Options and tradeoffs:** 以目前 main 為基底重放 #56 的兩個提交，不變更已發布工程套件內容。
- **User answer:** 這邊也要處理。
- **Explicit rationale:** 完成原先預期的主分支套件結構。
- **Resulting impact:** DEC-007 REQ-001 REQ-004；草稿 PR #58 以 main 為目標，20 項測試及 doc check/assemble/validate 通過。目錄精簡待 Q-004。

### DISC-008: CI 來源與本機內容的處理決定
- **Situation:** Q-004 區分必要 CI 來源與執行產物。
- **Question:** 你希望這四個目錄中的檔案全部停止 Git 追蹤，還是保留必要的 CI 測試與設定、移到其他位置？建議執行紀錄只留本機，必要的測試與設定移入 .github 或套件內，保留目前的自動升版檢查。
- **Options and tradeoffs:** 保留必要來源可維持發版檢查；產物不追蹤可精簡 clone。
- **User answer:** 保留必要的 CI 測試與設定  。非必要的保留本機，但要在正確的資料夾內
- **Explicit rationale:** 必要來源保留，其他內容本機保存。
- **Resulting impact:** DEC-008 REQ-005 AC-014。

## Open Decisions
None.

## Out Of Scope
不改 GitHub repo 名稱，不建立第二個來源 repo，不使用 submodule，不將兩套件改成同版，不重設或移動既有 tag，不重寫工程技能的治理行為，不統一工程既有 Claude／Codex 歷史版本，不移除未追蹤檔或使用者本機產物。完整方案確認與精確的開始執行授權前，不搬移來源、不改 workflow、不建立分支或 PR、不發佈及安裝產品。

## Problem
使用者要求將 ShinWeiPeng/skills 整理為一個 repo 下的 governed-engineering-skills 與 doc-coauthoring，clone 一起取得，但套件版本及升版 PR 分開。最初兩個 repo 選擇已由後續明確樹狀結構修正取代。

## Relationships
None.

## Requirements
| ID | Requirement | Source |
| --- | --- | --- |
| REQ-001 | 保留 ShinWeiPeng/skills，兩套技能位於同一個 repo 的並列資料夾。 | user:所以不能在ShinWeiPeng下新增skill，變成樹狀結構 |
| REQ-002 | 一次 clone 取得兩套件，各自管理版本。 | user:那版本控管可以分開 |
| REQ-003 | 保留 PR 升版流程。 | user:因為目前是透過PR進行版本控管的 |
| REQ-004 | doc-coauthoring 同時支援 Codex 與 Claude，保留原有三階段流程，適配平台工具與安裝設定。 | user:採用1 |
| REQ-005 | 來源 repo 不再追蹤 root spec-governance/、artifacts/、tests/flows/plugin-integration/monorepo/、validation/。必要 CI 測試及設定保留於 .github；產物與執行狀態保留本機對應目錄並忽略。維持原自動升版、兩平台安裝與 CI 檢查。 | DEC-006 DEC-008 |

## Revision History
None.
| 11 | 2026-10-22 | Reopened before clarification: User requests a minimal tracked repository and identifies four root paths for exclusion; required CI source/configuration retention requires one clarified decision. |
| 16 | 2026-10-22 | Reopened before clarification: Align rendered tables and target directory sketch with the adopted cleanup; no requirement or acceptance delta. |

## Routing/Gates
Q-001@2 的採用1已確認雙平台範圍；本回合再由 Q-002@6 的「採用方案，開始執行」確認整份方案並提供本次執行授權。保存實際原始授權，交付 admission 通過前不寫產品。

- Discussion owner：grilling；reconcile：spec-governance；完整方案：clarify-improvement-proposals；架構路徑與 source sets：govern-modular-event-architecture。
- 路由 CLI 在既有大型 workspace inventory 的有界時間內未完成時，保留該能力缺口；僅依 ask-matt 既有合約繼續 read-only discovery／document synthesis，不授予產品實作權限。
- Validation Enablement：確認兩平台 harness／CLI 能力、既有 matrix 與乾淨 checkout 基線，先演練臨時 Git／fake GitHub 邊界。缺能力為 BLOCKED，不能以 manifest 檢查代替平台實測。
- Per-change Development Validation：套件 inventory、path mapping、版本判斷、shared-path、重跑、lease 與兩個 PR merge order 的單元／契約測試。
- Final Runtime Acceptance：隔離 Codex、Claude 載入 doc-coauthoring 並完成三階段案例；既有工程安裝入口回歸。沒有硬體或 OS 排程資源證據需求。
- Release Acceptance：正式來源重新組裝、版本／fingerprint／tag 身分、產物相對路徑、完整既有 matrix、架構與 generated-view gate，再允許 reviewed release flow。
- 證據留於不可變 artifacts run，記錄命令、argv、exit code、fixture結果、產物 SHA 與平台輸出。此提案未執行上述驗收。

## Solution
使用者已於本回合確認完整修訂6方案，並明示開始執行；範圍依 DEC-004 維持不變。產品寫入仍須正式交付 admission 與其範圍檢查通過。

### 目標結構

```text
skills/                              # ShinWeiPeng/skills；唯一 Git root
├── .github/workflows/                # PR、檢查與兩套件發佈入口
├── .agents/plugins/marketplace.json  # 本機開發用目錄；不冒充正式產物
├── .claude-plugin/marketplace.json   # Claude 共用套件目錄
├── AGENTS.md / CLAUDE.md             # 共用規則及套件導覽
├── README.md                        # 各套件用途、安裝、升版說明
├── release-packages.json             # 套件路徑與發佈身分的宣告設定
├── architecture/                     # repo 架構與跨套件發佈契約
├── specs/                            # 既有 canonical SPEC 路徑不搬移
├── .github/tests/flows/plugin-integration/monorepo/ # 必要跨套件發佈契約測試
├── .github/validation/                # 必要 CI 設定與平台案例
├── governed-engineering-skills/
│   ├── skills/engineering/
│   ├── skills/productivity/
│   ├── skills/<其他既有 buckets>/
│   ├── plugins/governed-engineering-skills/
│   │   ├── package.json              # 工程 Codex 既有版本權威
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .changeset/
│   │   └── CHANGELOG.md
│   ├── .claude-plugin/plugin.json    # 保留既有 Claude 身分及歷史版本
│   ├── scripts/ / distribution/ / tests/ / tools/
│   ├── docs/ / AGENTS.md / CLAUDE.md / LICENSE
│   └── Install Governed Engineering Skills.*
└── doc-coauthoring/
    ├── skills/doc-coauthoring/SKILL.md  # 唯一可編輯的共同流程來源
    ├── skills/doc-coauthoring/references/
    ├── .codex-plugin/plugin.json
    ├── .claude-plugin/plugin.json
    ├── package.json / .changeset/ / CHANGELOG.md
    ├── scripts/
    ├── README.md / UPSTREAM.md
    └── 授權與來源聲明
```

原有 repo-root 安裝啟動器暫保留為轉呼叫入口，目標為工程套件子目錄的同名啟動器。既有開發指令若保留相容入口，入口只轉呼叫，不保留第二份實作。其他既有 buckets 與資源依已審閱的 tracked inventory 搬移；不刪除或自動搬走未追蹤的使用者資料。root specs 的 canonical 路徑保持穩定。

### 版本權威與升版 PR

| 項目 | 工程套件 | 文件套件 |
| --- | --- | --- |
| 版本來源 | 搬移後原有 plugin package.json 與 release-state | doc-coauthoring/package.json 與其 release-state |
| 版本起點 | 延續現有正式版本與最高 changeset bump，不重設 | 第一個正式套件版本提案為 0.1.0 |
| changesets | 套件內原有 .changeset | 文件套件自己的 .changeset |
| 升版分支 | 保留 plugin-release/main | plugin-release/doc-coauthoring |
| 升版 PR | 保留既有工程升版 PR 身分 | 獨立文件套件升版 PR |
| tag | 保留 governed-engineering-skills@<version> | doc-coauthoring@<version> |
| Codex 產物分支 | 保留 marketplace-release | doc-coauthoring-release |

工程套件原有 Claude plugin 版本與 Codex 版本目前不同。本次遷移保持既有兩者歷史及身分，不直接把 Claude 1.3.1 改寫成 Codex 0.23.1。文件套件的新 Codex／Claude manifest 則由其唯一 package version 產生同版產物。未來工程雙平台統一版本若有需求，另列變更契約。

維持既有流程：功能 PR 宣告該套件 changeset 及 release intent；合併 main 後只建立或更新該套件 Version PR；Version PR 經檢查與人工合併後，才為該套件建立 tag、組裝並發佈產物。此方案不新增功能 PR 合併即自動跳過 Version PR 的路徑。

升版與 git staging 使用目標套件的明確 allowlist，不使用 repo-wide git add -A。工程及文件各自的 CI／Version PR 不得順帶消耗另一套件 changesets、改版本、changelog、release-state 或發佈分支。

### 變更辨識與檢查

root CI 永遠在 PR 上建立整體檢查，再判定受影響套件，避免只在 workflow 最外層使用 paths 過濾而讓必要檢查永遠 pending。

- 套件內 changeset／版本／產物相關路徑：驗證該套件。
- 兩套件皆有變更：兩套件各自驗證，各自開升版 PR，不強制同版或同日發佈。
- 根 README 等明確列出的導覽文件：只執行文件檢查，不自動升任何套件。
- root workflow、宣告設定、架構或其他共用／未分類路徑：保守驗證兩套件；再由各套件的組裝來源、production fingerprint、pending intent 判定是否需升版。共用檔案變更本身不等於兩套件都要升版。
- 產物內容改變但缺少該套件 changeset／intent：檢查失敗，不靜默發佈。只有文件或驗證設定變更且產物相同：不建立升版 PR。
- 所有選擇以實際 PR base/head 或 push before/after 的明確範圍與完整歷史為依據。刪除／搬移涵蓋舊、新路徑；資料不足則阻擋該次發佈，不假設無變更。

### 發佈身分、重跑與並行

維持工程套件的 repository URL、Marketplace 名稱、Plugin ID、marketplace-release ref 及正式產物內 plugins/governed-engineering-skills 路徑。main 上的來源資料夾搬移不改寫既有安裝的 consumer tree。doc 使用自己的 Marketplace／Plugin 身分及 consumer branch，因此文件發佈不能覆寫工程發佈。

tag 已存在但指向早期 commit，不能因為 main 後來只有另一套件或 root 文件的新 commit 就判定 tag 過期。檢查該 tag 的套件版本、已記錄的來源與實際套件產物 fingerprint：完全相同則不再升版、不移動 tag；同版本內容不同則阻擋，要求正確的 changeset／新版本。既有正式 tag 全部不可移動。

每套件的 Version PR 更新與產物分支更新使用各自 concurrency group。PR 及分支在副作用前重讀目前身分，並以明確 expected base／force-with-lease 防止覆蓋競爭更新。重跑可補齊同一版缺少的產物步驟；不得產生第二次 bump。發佈失敗保留上一個可安裝分支，記錄 source SHA、version、fingerprint、tag SHA、previous publication SHA 及可重現的補發步驟；不假稱 tag 與 branch 能跨 ref 原子交易。

### doc-coauthoring 雙平台適配

保留 Context Gathering → Refinement & Structure → Reader Testing 三階段。共同 SKILL.md 加上小型平台 reference，明確映射 Codex／Claude 可用的檔案編輯、工具、artifact 與讀者測試機制，避免兩份手動維護的流程。新 manifest、安裝說明及來源記錄獨立於工程套件。

有可用 sub-agent 時以全新上下文做讀者測試；沒有時依原流程提供人工測試步驟，明確回報測試狀態。缺少工具或平台能力不能宣稱 Reader Testing 通過。一般文件共同撰寫不自動帶入工程套件的 SPEC／開始執行要求；工程規格或程式修改仍遵守工程套件既有治理。根 AGENTS 只描述共用管理及套件導覽，工程專用規則留於工程套件邊界。

上游匯入固定到經查驗的 commit，UPSTREAM.md 記錄 anthropics/skills、skills/doc-coauthoring、來源 SHA、匯入日期、適配差異與更新方法。匯入時核對適用授權並保存著作權／授權依據，不將工程套件的 MIT 自動套用到 Anthropic 內容；沒有足夠依據時阻擋內容再發佈，其他遷移調查仍可進行。

### 相容性與遷移順序

PR A：工程來源搬移、root 套件登錄、既有安裝轉呼叫入口、CI 與工程發佈相容性一起完成。先建立 tracked-only 的乾淨 checkout baseline，更新 PACKAGE_ROOT 與 GIT_ROOT 的明確分工；所有 git inventory 以 repo root 取得路徑，組裝再正規化為原來 artifact logical path。不可只把 scripts 的 cwd 改成子目錄就當作搬移完成。保留原 SemVer、changeset 歷史、tag、consumer ref 及既有工程升版 PR；有未合併 Version PR 時以新 main 重新產生同一分支，保留其待發版本意圖，不強推舊路徑內容。合併仍由使用者審查。

PR B：導入 doc-coauthoring、雙平台適配、獨立升版 PR 與發佈分支；工程套件不得因此自動升版。兩個功能 PR 可分別衍生自己的自動 Version PR。

每一階段均以既有安全安裝版本為回退來源。未完成包裝驗證前，不切換正式 consumer branch。文件與 root 列表、workflow、AGENTS/CLAUDE、CLAUDE marketplace source path、Codex 開發 catalog、測試路徑、架構 source_sets 與宣告符號連結需在對應 PR 一起更新。

### 選項比較

| 選項 | 效益 | 成本與取捨 | 本案處理 |
| --- | --- | --- | --- |
| 單 repo、各自 Version PR 與發佈分支 | 符合一起 clone、分開升版；保留工程既有發佈來源 | 多一套件設定與發佈維護 | 建議採用 |
| 單 repo、單一 Version PR 與共用版本 | 發佈入口少 | 文件變更會耦合工程版本，與獨立升版目標不合 | 不採用 |
| 單 repo、共用 Marketplace 產物分支 | 可用一個 catalog 看見所有正式套件 | 每次發佈須合併另一套件最後已發布產物，並處理共享分支序列化與競爭 | 本次不採用；保留未來獨立提案空間 |
| 兩個 repo | Git 與權限完全分開 | clone、PR 及管理分散，與後續指定樹狀結構不合 | 已由 DEC-001 排除 |

增加套件設定、獨立發佈驗證與雙平台實測成本，是換取獨立升版的主要代價。本案不宣稱執行效能改善。

### 必要追蹤與本機狀態

- 必要 CI 測試移至 .github/tests/flows/plugin-integration/monorepo；設定與平台案例移至 .github/validation。
- root spec-governance、artifacts、validation、tests 不再追蹤；原檔保留本機。
- CI 從追蹤來源重建 ignored validation 相容設定，先檢查所有檔案再更新，拒絕覆寫人為修改與 symlink/junction。
- .github 發版流程、兩平台 catalog 保留；非必要 issue 模板與標籤自動化保留本機但停止追蹤。
- 套件版本不因搬移 CI 來源而變動；工程內容維持 0.23.2，文件初版仍透過自己的 Version PR。

## User Stories
- 維護者一次 clone skills repo 取得兩套技能來源。
- 文件套件的功能 PR 合併後只產生文件套件 Version PR。
- 工程套件既有安裝者在來源重整後仍可升級及安裝。
- Codex 與 Claude 使用者可各自載入 doc-coauthoring，完成相同三階段協作。

## Architecture Impact
維持現有責任與方向；資料夾名稱不是 L0/L1 模組宣告。本次主要是 source path／套件發佈單元邊界調整。現有 guided_workflow_router、plugin_assembly_composition、plugin_release_governance_technical、codex_plugin_adapter 與安裝 adapters 的 paths、入口、來源 inventory、source_sets、參照 manifest／測試定義路徑均需精確遷移。release module 的「唯一套件／唯一版本權威」不變式改為每套件一個版本權威，共用 CI 只選擇及呼叫套件，不擁有它們的版本狀態。

root repository architecture manifest 與 canonical specs 保持 repo 級；package root 與 git root 顯式區分。工程現有 Type/State/Catalog owner 不因路徑搬移而更換；若新 release selector 或 adapter 引入 production types／state／ports，先完成 Boundary、Type Ownership、State Ownership、父層 mapping 的設計 gate，禁止藉重新標籤略過完整性。

正式實作需提出與 ADR-0013 stable versioning、ADR-0014 consumer branch 契約相關的獨立 suite release ADR，及套件 root relocation 的路徑／權威變更說明；均維持 proposed，等使用者整體審查。不是 MUST-rule 例外授權。

### Description Views impact

更新 manifest 中源碼路徑、entrypoint/public symbol 連結、source set 與每套件 release invariant，重新產生 System、plugin assembly 與受影響 Parent／Flow pages、adoption readiness。generated pages 不手改。驗收由公共 architecture_cli.py gate --phase release 及 deterministic render --check 執行，不以單一內部 checker 當完整 PASS。

### Algorithm impact

來源搬移與保留既有三階段提示流程沒有選擇新的文件生成演算法；現有 SemVer highest-bump 演算法保留。新的受影響套件選擇、同版 identity 判斷、重跑補發與 lease 拒絕涉及可觀察結果及 failure policy，必須在設計階段對既有 release decision records 做差異篩選，必要時提出完整 ALG 記錄與正確功能 owner。不得直接把 L3 技術 adapter 冒稱演算法功能 owner。設計使用 deterministic truth table 與臨時 Git fixtures 比較路徑僅選擇及產物／intent 身分判斷；發佈以後者作最終權威，路徑僅決定檢查範圍。

### Execution efficiency / Flow / Evolution impact

本案沒有裝置、硬即時、soft SLO、Task/core/Queue 或 CPU 資源目標，不建立效能／排程優越性主張。受影響的 end-to-end Flow 為功能 PR → per-package intent → Version PR → reviewed merge → immutable tag → generated publication。每一階段的成功、缺資料、競爭與部分失敗規則見 Solution 與 AC-003 至 AC-008。新增套件場景只增 registry、套件來源、該套件 release entry 與測試；共用 schema／workflow 改變須回歸兩套件。維護成本增加是明示取捨，不以未測的「更快」或「更易擴充」當作證據。

## Acceptance Mapping

```json
{
  "AC-001": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units"
    ],
    "execution_changes": [],
    "rationale": "Repository layout and tracked inventory are host file/Git semantics."
  },
  "AC-002": {
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "contract_dimensions": [
      "input-output-units",
      "external-port"
    ],
    "execution_changes": [],
    "rationale": "Version/tag identity and installer adapters require inventory checks plus installer adapter contracts."
  },
  "AC-003": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "state-transition",
      "call-order",
      "error-reset"
    ],
    "execution_changes": [],
    "rationale": "Scoped Version PR creation and release decisions are deterministic host state transitions."
  },
  "AC-004": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "state-transition",
      "call-order",
      "error-reset"
    ],
    "execution_changes": [],
    "rationale": "The independent doc release uses the same host state-transition proof with an isolated package fixture."
  },
  "AC-005": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "state-transition",
      "call-order",
      "error-reset"
    ],
    "execution_changes": [],
    "rationale": "Both merge orders require host orchestration and per-package state assertions."
  },
  "AC-006": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units"
    ],
    "execution_changes": [],
    "rationale": "Changed-path selection, unknown ranges and intent validation are host semantics with negative fixtures."
  },
  "AC-007": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "state-transition",
      "call-order",
      "error-reset"
    ],
    "execution_changes": [],
    "rationale": "Idempotence and immutable version/fingerprint identity are host state transitions; tag and publication steps remain separately recoverable."
  },
  "AC-008": {
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "contract_dimensions": [
      "state-transition",
      "call-order",
      "error-reset",
      "external-port"
    ],
    "execution_changes": [],
    "rationale": "Lease conflict and external publication rejection require host decision tests and reusable Git publication adapter contracts."
  },
  "AC-009": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units"
    ],
    "execution_changes": [],
    "rationale": "Common skill inventory, manifests and version equality are host schema and path semantics."
  },
  "AC-010": {
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "contract_dimensions": [
      "input-output-units",
      "external-port"
    ],
    "execution_changes": [],
    "rationale": "Two real hosted CLI/harness compositions must complete the documented workflow; platform adapter conformance supplements host checks."
  },
  "AC-011": {
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "contract_dimensions": [
      "input-output-units",
      "external-port"
    ],
    "execution_changes": [],
    "rationale": "Missing-tool/no-subagent handling and platform calls need failure-path host tests plus applicable adapter contracts."
  },
  "AC-012": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units"
    ],
    "execution_changes": [],
    "rationale": "Provenance, fixed source identities and license applicability are inspectable host artifacts with recorded human review; no legal conclusion is inferred."
  },
  "AC-013": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units"
    ],
    "execution_changes": [],
    "rationale": "Clean-checkout assembly, existing matrix and architecture/path verification are host source and build semantics."
  },
  "AC-014": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset"
    ],
    "execution_changes": [],
    "rationale": "Tracked inventory, reproducible CI configuration and preservation of edited local settings are bounded host file semantics."
  }
}
```

## Validation Commands

以下命令為遷移後計畫；尚未執行。所有命令保存 argv、工作目錄、exit code 與不可變 run 輸出。

- Cross-package contracts: python -m unittest discover -s .github/tests/flows/plugin-integration/monorepo -p "test_*.py" -v。新 fixture 由實作階段建立；涵蓋 AC-003 至 AC-008。
- Engineering assembly: python governed-engineering-skills/scripts/assemble_plugin.py assemble --marketplace-publication；接著 python governed-engineering-skills/scripts/validate_distribution.py；python governed-engineering-skills/scripts/assemble_plugin.py validate。必須使用明確 package/git roots，產物不得混入 doc。
- Engineering version: python governed-engineering-skills/plugins/governed-engineering-skills/scripts/version_governance.py check。
- Architecture: python governed-engineering-skills/tools/architecture/architecture_cli.py gate --phase release --manifest architecture/manifest.yaml --adoption architecture/adoption.yaml --baseline architecture/baseline.yaml；generated views 由同一 public CLI 的 release gate 驗證；render 用於重建，不使用不存在的 --check 選項或 legacy internal script。
- Doc package contracts: python -m unittest discover -s .github/tests/flows/plugin-integration/monorepo -p "test_doc_release.py" -v。包含兩份平台 manifest 及共同來源、固定版本／來源 SHA、相對引用與 fallback。
- Platform cases: 在隔離設定的 Codex 與 Claude session 各載入該次組裝的 doc-coauthoring；輸入固定技術文件、提案、決策文件案例；逐次記錄三階段輸出、獨立 reader context 與人工 fallback；關閉 sub-agent／移除工具的負例必須顯示對應狀態，不能宣稱讀者檢驗成功。安裝／載入失敗是 BLOCKED 或 FAIL，不能由靜態 manifest 通過代替。
- Migration link and source review: compare git ls-files tracked paths and artifact inventory before/after; check every moved relative Markdown link, launcher target, manifest reference and tag SHA; record observer, commands, before/after hashes, observed output and pass condition.

Acceptance Mapping 是已規劃的 evidence 分類，不是測試結果。schema-2 projection 應由 managed generate-acceptance 從此 SPEC 生成；不手寫第二份驗收定義。mapping 投影與完整 planning/profile gate 在交付 admission 前必須完成，禁止把生成成功當驗收成功。

- Fresh checkout preparation: python .github/scripts/prepare_validation.py；來源設定在 .github/validation，root validation 為忽略的相容副本；已修改的本機設定拒絕覆寫。

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

- user:提出修改方案: 提出修改方案：單一 skills repo 內並列兩套件，各自以 PR 管理版本。
- user:提出修改方案: 提出修改方案：single skills monorepo, independent package Version PRs; doc-coauthoring platform support unresolved
- assistant:prepared-monorepo-proposal-scope: Saved current monorepo and independent PR release requirements; discovered existing two-stage Version PR release flow. Platform scope Q-001 remains pending. No product execution authority.
- user:採用1: 採用1
- user:採用1: 採用1: doc-coauthoring Codex and Claude; synthesize complete monorepo independent Version PR proposal, no implementation grant
- assistant:complete-monorepo-proposal: User adopted dual-platform option 1; reconciled REQ-004 DEC-003 and DISC-002. Completed source layout, independent Version PR/tag/publication and backward compatibility proposal, 13 acceptance criteria and evidence mappings. Full proposal confirmation Q-002 remains pending; no implementation authority.
- user:adopt-plan-start: 採用方案，開始執行
- assistant:confirmed-execution-entry: User explicitly adopted the complete proposal and authorized execution with 採用方案，開始執行. No semantic scope delta; transcript source reference is caller-attested, native user-message UUID unavailable.
- assistant:native-tool-exception: Preserved actual full-plan execution authorization. Found confirmed-spec/preparation circular dependency and unsupported rename/control operations. Prepared additive verification patch plus 485 hashed tracked-source relocations. No product changes applied. Q-003 requests task-scoped native-tool exception preserving hash/scope/acceptance constraints.
- user:allow-native-tools: 允許
- assistant:authorized-native-entry: Reconciled explicit native-tool exception without changing the approved product scope. Applied only reviewed additive verification matrix patch after exact hash check; verified all 485 relocation hashes and no destination conflicts. Original execution authorization retained.
- user:directory-not-split: 說明為何 GitHub main 尚未顯示兩個套件目錄，只核對 PR 與目前來源狀態，不變更方案或產品
- assistant:directory-diagnosis: Read-only follow-up: verified PR55 merged to main while PR56 merged to codex/skills-monorepo; main therefore lacks doc-coauthoring. No new scope or execution authority. Original native exception remains recorded by DEC-005.
- user:minimal-tracked-files: User requests tracking only necessary files and identifies spec-governance, artifacts, tests/flows/plugin-integration/monorepo, validation as unnecessary. Clarify whether required CI source tests/configuration can be retained at another path; no product changes in this turn.

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"b889072e629720a88d3674fc956018308707b911293057e7d396132bd2657c3e","event_type":"start","event_version":1,"open_decisions":[],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-10-22T03:08:48.827775+00:00","relationships":[],"revision":1,"snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"提出修改方案：單一 skills repo 內並列兩套件，各自以 PR 管理版本。","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:提出修改方案","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-propose-modification-plan"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"a81b001879bd4d9dedee4f2b5c7cb5ab2c967e257de45d62321b99ff0e41d188","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"b889072e629720a88d3674fc956018308707b911293057e7d396132bd2657c3e","previous_snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","recorded_at":"2026-10-22T03:09:09.784194+00:00","relationships":[],"revision":1,"snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"提出修改方案：single skills monorepo, independent package Version PRs; doc-coauthoring platform support unresolved","kind":"entry-update","source_ref":"user:提出修改方案","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-propose-modification-plan"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"bb892757edc8671d920ed89d47f90da07906c07ff42bc0b704a42370f217d625","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"a81b001879bd4d9dedee4f2b5c7cb5ab2c967e257de45d62321b99ff0e41d188","previous_snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","recorded_at":"2026-10-22T03:09:36.671103+00:00","relationships":[],"revision":1,"snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"e684ebe529fde10655b9f9c77e118d397567981d85f9277aa986844a4c1fd3fa","event_type":"reconcile","event_version":1,"open_decisions":["Q-001@2"],"previous_event_hash":"bb892757edc8671d920ed89d47f90da07906c07ff42bc0b704a42370f217d625","previous_snapshot_hash":"aa4268c5132d0f41035c2512539673d47daf4bdb95b8bfe22a0db83818876f2d","recorded_at":"2026-10-22T03:10:45.547324+00:00","relationships":[],"revision":2,"snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":2,"snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[],"completeness_review":null,"identified_items":{"CAND-001":{"id":"CAND-001","kind":"candidate","source_ref":"assistant:monorepo-proposal-outline","text":"Keep one repository with sibling package directories; preserve the existing two-stage PR release process and isolate package versions, release PRs, checks and publications."},"FACT-001":{"id":"FACT-001","kind":"fact","source_ref":"github:ShinWeiPeng/skills/.github/workflows/release.yml","text":"Current workflow creates Version PR on plugin-release/main, then tags and publishes marketplace-release after version intent has been applied."},"Q-001":{"id":"Q-001","kind":"question","source_ref":"assistant:doc-platform-scope","text":"doc-coauthoring platform scope: Codex and Claude, original Anthropic only, or Codex only."}},"item_bindings":{"CAND-001":[],"FACT-001":[],"Q-001":[]},"kind":"saved","reply_sha256":"8224bf90ec6cf04d95da7aef33c77caf6ba6a2c69a4cc592c063772f41101fea","reply_stage":"prepared-until-host-stop","reviewed_sources":["assistant:doc-platform-scope","assistant:monorepo-proposal-outline","github:ShinWeiPeng/skills/.github/workflows/release.yml","user:提出修改方案"],"source_ref":"assistant:prepared-monorepo-proposal-scope","summary":"Saved current monorepo and independent PR release requirements; discovered existing two-stage Version PR release flow. Platform scope Q-001 remains pending. No product execution authority.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-propose-modification-plan"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"bcb63936391e93ae310d694d38b960eba854c64813da55a5c8f2cc4aa9cb0f5f","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"e684ebe529fde10655b9f9c77e118d397567981d85f9277aa986844a4c1fd3fa","previous_snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","recorded_at":"2026-10-22T03:13:27.661324+00:00","relationships":[],"revision":2,"snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"採用1","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:採用1","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-option-1"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"74b291bef1443a4a45fc7a19784c15b37b0cd9bafb0a93121f7ab54f052c5799","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"bcb63936391e93ae310d694d38b960eba854c64813da55a5c8f2cc4aa9cb0f5f","previous_snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","recorded_at":"2026-10-22T03:20:38.723424+00:00","relationships":[],"revision":2,"snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["DEC-003","DISC-002","REQ-004"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-003","DISC-002","REQ-004"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"2466103a1cb0dc1c099b40ec77a405cf9a5ce8b34b19285da23099aac41a4bb4","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"74b291bef1443a4a45fc7a19784c15b37b0cd9bafb0a93121f7ab54f052c5799","previous_snapshot_hash":"2e8938e14ee493b8c2c5554cc96fdc3a99db0f9adee83621708d5ec285a540aa","recorded_at":"2026-10-22T03:20:39.432085+00:00","relationships":[],"revision":3,"snapshot_hash":"b8be5ed9cc61c4931a60cccf3ff53c7bf372727f34f55edccd17d3753353e89f","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"採用1: doc-coauthoring Codex and Claude; synthesize complete monorepo independent Version PR proposal, no implementation grant","kind":"entry-update","source_ref":"user:採用1","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-option-1"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"0bf47639b381434f20b7f657dbb4029c8aab7627f221cd146f03bc523aec452c","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"2466103a1cb0dc1c099b40ec77a405cf9a5ce8b34b19285da23099aac41a4bb4","previous_snapshot_hash":"b8be5ed9cc61c4931a60cccf3ff53c7bf372727f34f55edccd17d3753353e89f","recorded_at":"2026-10-22T03:21:56.944856+00:00","relationships":[],"revision":3,"snapshot_hash":"b8be5ed9cc61c4931a60cccf3ff53c7bf372727f34f55edccd17d3753353e89f","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"d0bbcdba0a588488f7511a91228e5f820d1b9d2c2bca9402102627d30136ff7c","event_type":"reconcile","event_version":1,"open_decisions":["None. 技術細節已整理為待整體確認的提案；需使用者確認完整範圍後才能 materialize，開始執行授權另行判定。"],"previous_event_hash":"0bf47639b381434f20b7f657dbb4029c8aab7627f221cd146f03bc523aec452c","previous_snapshot_hash":"b8be5ed9cc61c4931a60cccf3ff53c7bf372727f34f55edccd17d3753353e89f","recorded_at":"2026-10-22T03:24:55.645258+00:00","relationships":[],"revision":4,"snapshot_hash":"9c6adc23f3e793344b617e111b396212666373ddc8b1ed81f7da95f869a78a3b","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"892c5594159e6b5ddcf573626454cc4b05680e67b419cf1f1aa871d02101abce","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"d0bbcdba0a588488f7511a91228e5f820d1b9d2c2bca9402102627d30136ff7c","previous_snapshot_hash":"9c6adc23f3e793344b617e111b396212666373ddc8b1ed81f7da95f869a78a3b","recorded_at":"2026-10-22T03:26:32.554423+00:00","relationships":[],"revision":5,"snapshot_hash":"d93e2c3872c464613937badd93c0f9aa5f2996c0f97a31ae864f3623eadb7077","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"019b06e83fd4d9488288d53a37e5697daaf54c8eef4656a8d384530efe8b47d9","event_type":"reconcile","event_version":1,"open_decisions":["Q-002@6"],"previous_event_hash":"892c5594159e6b5ddcf573626454cc4b05680e67b419cf1f1aa871d02101abce","previous_snapshot_hash":"d93e2c3872c464613937badd93c0f9aa5f2996c0f97a31ae864f3623eadb7077","recorded_at":"2026-10-22T03:27:15.338504+00:00","relationships":[],"revision":6,"snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":6,"snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[{"id":"PROPOSAL-MONOREPO","impact":"Source relocation, release orchestration, two-platform packaging and compatibility validation.","reason":"Preserve one clone and existing reviewed Version PR process while isolating package release identities.","source_ref":"assistant:complete-monorepo-proposal","status":"candidate"}],"completeness_review":null,"identified_items":{"ADOPT-DUAL-PLATFORM":{"id":"ADOPT-DUAL-PLATFORM","kind":"accepted","source_ref":"user:採用1","text":"Adopt Q-001 option 1: doc-coauthoring supports Codex and Claude while preserving the original three-stage workflow."},"PROPOSAL-MONOREPO":{"id":"PROPOSAL-MONOREPO","kind":"candidate","source_ref":"assistant:complete-monorepo-proposal","text":"Complete two-package source migration, independent Version PR/tag/publication contracts, backward compatibility and thirteen acceptance criteria; awaiting full proposal confirmation."},"Q-002":{"id":"Q-002","kind":"question","source_ref":"assistant:full-proposal-confirmation","text":"Confirm the complete SPEC-0064 proposal; confirmation does not grant implementation authority."}},"item_bindings":{"ADOPT-DUAL-PLATFORM":["REQ-004","DEC-003"],"PROPOSAL-MONOREPO":[],"Q-002":[]},"kind":"saved","reply_sha256":"a7c8387d1656db0a7fe05101418d078feaeb7b7e97d5ec81d7251cc9eadb232d","reply_stage":"prepared-until-host-stop","reviewed_sources":["assistant:complete-monorepo-proposal","assistant:full-proposal-confirmation","user:採用1"],"source_ref":"assistant:complete-monorepo-proposal","summary":"User adopted dual-platform option 1; reconciled REQ-004 DEC-003 and DISC-002. Completed source layout, independent Version PR/tag/publication and backward compatibility proposal, 13 acceptance criteria and evidence mappings. Full proposal confirmation Q-002 remains pending; no implementation authority.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-option-1"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"f6eb7cbd11d5909cd40ce0cd30815b1632957c5334f7a2745f6f2188628ae484","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"019b06e83fd4d9488288d53a37e5697daaf54c8eef4656a8d384530efe8b47d9","previous_snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","recorded_at":"2026-10-22T03:27:57.806477+00:00","relationships":[],"revision":6,"snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"採用方案，開始執行","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:adopt-plan-start","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-plan-start"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"604e440c9547f2f13fa626973ab65590f0df098d274e78e85a574ace36568eed","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"f6eb7cbd11d5909cd40ce0cd30815b1632957c5334f7a2745f6f2188628ae484","previous_snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","recorded_at":"2026-10-22T03:37:01.340927+00:00","relationships":[],"revision":6,"snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["DEC-004","DISC-003"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-004","DISC-003"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"5eb91260446fd90aa715c843f1c4e67d822f780303d68d5f6fdb82081c53deb7","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"604e440c9547f2f13fa626973ab65590f0df098d274e78e85a574ace36568eed","previous_snapshot_hash":"93f9e69808efb86a73fa284a099ea8c054d5bcbc3bdf8d5996ca780b84e0182d","recorded_at":"2026-10-22T03:37:01.918017+00:00","relationships":[],"revision":7,"snapshot_hash":"47e00cc0abd560ac29e1eb63d5b732d85cca9d57ae19d9af6cbdf0fa155581db","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":7,"snapshot_hash":"47e00cc0abd560ac29e1eb63d5b732d85cca9d57ae19d9af6cbdf0fa155581db","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[],"completeness_review":{"acceptance":{"evidence":"Thirteen ACs define expected results, reproducible validation methods and explicit selectors, with all execution evidence still NOT RUN.","source_ref":"user:adopt-plan-start"},"behavior":{"evidence":"Feature PR -> per-package Version PR -> reviewed merge -> immutable tag and isolated publication.","source_ref":"user:adopt-plan-start"},"exceptions":{"evidence":"Keep prior usable publication on failure, reject same version different content and stale leases; never infer unsupported platform test success.","source_ref":"user:adopt-plan-start"},"goal":{"evidence":"Single skills repository, sibling engineering and doc packages, independent releases.","source_ref":"user:adopt-plan-start"},"scope":{"evidence":"Complete previously presented revision 6 including preserved legacy engineering identities and dual-platform doc support.","source_ref":"user:adopt-plan-start"}},"identified_items":{"ADOPT-COMPLETE-PLAN":{"id":"ADOPT-COMPLETE-PLAN","kind":"accepted","source_ref":"user:adopt-plan-start","text":"採用方案，開始執行: confirms the complete SPEC-0064 revision 6 scope and explicitly authorizes its execution. Transcript reference identifies this visible message; the host exposes no native user-message UUID."}},"item_bindings":{"ADOPT-COMPLETE-PLAN":["DEC-004"]},"kind":"saved","reply_sha256":"cb06abefffbf3d7b58aca88315441e3942bd7bfc07774be966b7c25dbc039bc7","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:adopt-plan-start"],"source_ref":"assistant:confirmed-execution-entry","summary":"User explicitly adopted the complete proposal and authorized execution with 採用方案，開始執行. No semantic scope delta; transcript source reference is caller-attested, native user-message UUID unavailable.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-plan-start"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"150b233ad4ddb177a31db20cd201016c694e625148980a75136722b3e4a05293","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"5eb91260446fd90aa715c843f1c4e67d822f780303d68d5f6fdb82081c53deb7","previous_snapshot_hash":"47e00cc0abd560ac29e1eb63d5b732d85cca9d57ae19d9af6cbdf0fa155581db","recorded_at":"2026-10-22T03:38:47.907984+00:00","relationships":[],"revision":7,"snapshot_hash":"47e00cc0abd560ac29e1eb63d5b732d85cca9d57ae19d9af6cbdf0fa155581db","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"23ffff461befcafea0a35a7f5b69be84173e751ba90aba54b43426f16f954cd4","event_type":"reconcile","event_version":1,"open_decisions":["Q-003@8"],"previous_event_hash":"150b233ad4ddb177a31db20cd201016c694e625148980a75136722b3e4a05293","previous_snapshot_hash":"47e00cc0abd560ac29e1eb63d5b732d85cca9d57ae19d9af6cbdf0fa155581db","recorded_at":"2026-10-22T03:42:39.177181+00:00","relationships":[],"revision":8,"snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":8,"snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[],"completeness_review":null,"identified_items":{"ADOPT-COMPLETE-PLAN":{"id":"ADOPT-COMPLETE-PLAN","kind":"accepted","source_ref":"user:adopt-plan-start","text":"採用方案，開始執行: confirms the complete SPEC-0064 revision 6 scope and explicitly authorizes its execution. Transcript reference identifies this visible message; the host exposes no native user-message UUID."},"FACT-NATIVE-LIMIT":{"id":"FACT-NATIVE-LIMIT","kind":"fact","source_ref":"assistant:managed-capability-audit","text":"Materialization is blocked by missing validation rule mappings; prepare-validation requires confirmed SPEC; the loaded writer prohibits rename/delete/control targets. Prepared additive verification patch and 485 tracked-source relocations with SHA-256; no runtime product edits applied."},"Q-003":{"id":"Q-003","kind":"question","source_ref":"assistant:native-tool-exception","text":"是否允許本次 SPEC-0064 使用原生 Git／檔案工具，補齊驗證設定並執行已核准的搬移與修改，同時保留來源雜湊檢查、範圍限制及原訂驗收？"}},"item_bindings":{"ADOPT-COMPLETE-PLAN":["DEC-004"],"FACT-NATIVE-LIMIT":[],"Q-003":[]},"kind":"saved","reply_sha256":"ad0f68ff839ba5733690c6e9a3ac82db3af906f7774d3cb2c8e1fa392744497f","reply_stage":"prepared-until-host-stop","reviewed_sources":["assistant:managed-capability-audit","assistant:native-tool-exception","user:adopt-plan-start"],"source_ref":"assistant:native-tool-exception","summary":"Preserved actual full-plan execution authorization. Found confirmed-spec/preparation circular dependency and unsupported rename/control operations. Prepared additive verification patch plus 485 hashed tracked-source relocations. No product changes applied. Q-003 requests task-scoped native-tool exception preserving hash/scope/acceptance constraints.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-adopt-plan-start"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"d0d29d4dbf1984cb0383fc84ad8d23034fd28f834b29956f9fc8033296acee71","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"23ffff461befcafea0a35a7f5b69be84173e751ba90aba54b43426f16f954cd4","previous_snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","recorded_at":"2026-10-22T03:43:06.663517+00:00","relationships":[],"revision":8,"snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"允許","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:allow-native-tools","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-allow-native-tools"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"15af3b2a3c9f9aee8b761701d42967a458a02a56ed92589a924fd6a9ac25675b","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"d0d29d4dbf1984cb0383fc84ad8d23034fd28f834b29956f9fc8033296acee71","previous_snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","recorded_at":"2026-10-22T03:56:04.251698+00:00","relationships":[],"revision":8,"snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["DEC-005","DISC-004"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-005","DISC-004"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"de9b47a24a79ce7d2dbf607513327843fe72648895b311c60831c7654b26d577","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"15af3b2a3c9f9aee8b761701d42967a458a02a56ed92589a924fd6a9ac25675b","previous_snapshot_hash":"111a84eddba51e0679449e5ef61e0a7c025ca7909f6a9f526b82399194273988","recorded_at":"2026-10-22T03:56:04.925203+00:00","relationships":[],"revision":9,"snapshot_hash":"5cb2fdd7a75e6953d6bf48824877882698676f4a339e684b18424dc5e4074863","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"e760706b4ee8235711704704c572355dde799baf05f50506bae5ac20d34eef30","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"de9b47a24a79ce7d2dbf607513327843fe72648895b311c60831c7654b26d577","previous_snapshot_hash":"5cb2fdd7a75e6953d6bf48824877882698676f4a339e684b18424dc5e4074863","recorded_at":"2026-10-22T03:56:06.535446+00:00","relationships":[],"revision":9,"snapshot_hash":"650a92fb2790359736a2cea859b6117f878c77a89992791a955250a42e110f8b","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":9,"snapshot_hash":"650a92fb2790359736a2cea859b6117f878c77a89992791a955250a42e110f8b","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[],"completeness_review":{"acceptance":{"evidence":"AC-001 through AC-013 and selector mappings remain unchanged; additive matrix rules now cover the declared evidence categories.","source_ref":"user:adopt-plan-start"},"behavior":{"evidence":"Two independent Version PR flows, immutable tags and isolated publications; shared doc workflow across two harnesses.","source_ref":"user:adopt-plan-start"},"exceptions":{"evidence":"Identity conflicts and missing capabilities reject; no lowered tests or fake PASS; hashed tracked-source inventory protects existing data.","source_ref":"user:adopt-plan-start"},"goal":{"evidence":"One skills repository, two sibling packages, independent reviewed releases.","source_ref":"user:adopt-plan-start"},"scope":{"evidence":"Complete approved SPEC-0064 proposal with only the separately authorized native-tool exception.","source_ref":"user:adopt-plan-start"}},"identified_items":{"ALLOW-NATIVE":{"id":"ALLOW-NATIVE","kind":"accepted","source_ref":"user:allow-native-tools","text":"User allowed the scoped native Git/file-tool exception in Q-003, preserving the existing execution authorization and hash/scope/acceptance constraints."}},"item_bindings":{"ALLOW-NATIVE":["DEC-005"]},"kind":"saved","reply_sha256":"f8ef130743fff66d41f9b3613093b927ce41f6e0b02a677ad2f4d310bb57fee0","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:allow-native-tools"],"source_ref":"assistant:authorized-native-entry","summary":"Reconciled explicit native-tool exception without changing the approved product scope. Applied only reviewed additive verification matrix patch after exact hash check; verified all 485 relocation hashes and no destination conflicts. Original execution authorization retained.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-allow-native-tools"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"f33acea89060b37b57d3adc981e80153572e54ba4bc191c5039868525d5f4eb0","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"e760706b4ee8235711704704c572355dde799baf05f50506bae5ac20d34eef30","previous_snapshot_hash":"650a92fb2790359736a2cea859b6117f878c77a89992791a955250a42e110f8b","recorded_at":"2026-10-22T03:56:06.733170+00:00","relationships":[],"revision":9,"snapshot_hash":"650a92fb2790359736a2cea859b6117f878c77a89992791a955250a42e110f8b","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"b042257d4af7d5b39f5cc8986321d2da97b72e3a19f8b382f5033f7ec80fd8e5","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"f33acea89060b37b57d3adc981e80153572e54ba4bc191c5039868525d5f4eb0","previous_snapshot_hash":"650a92fb2790359736a2cea859b6117f878c77a89992791a955250a42e110f8b","recorded_at":"2026-10-22T04:40:53.233230+00:00","relationships":[],"revision":10,"snapshot_hash":"3ca107a6b4085762a9a4ca3beb89b6c378d32ca5c0cec161176739a516f982c3","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"877a0e848a49a90d57381ddf6dddcb3dd24352c2554f9a95393f3681d35b5cf0","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"b042257d4af7d5b39f5cc8986321d2da97b72e3a19f8b382f5033f7ec80fd8e5","previous_snapshot_hash":"3ca107a6b4085762a9a4ca3beb89b6c378d32ca5c0cec161176739a516f982c3","recorded_at":"2026-10-22T04:40:53.689740+00:00","relationships":[],"revision":10,"snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"說明為何 GitHub main 尚未顯示兩個套件目錄，只核對 PR 與目前來源狀態，不變更方案或產品","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:directory-not-split","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-directory-not-split"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"110bc6023e547bfb198dfeba2fc0e2223a7abd2076c6acc5de721c4319b98c84","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"877a0e848a49a90d57381ddf6dddcb3dd24352c2554f9a95393f3681d35b5cf0","previous_snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","recorded_at":"2026-10-22T05:52:51.083702+00:00","relationships":[],"revision":10,"snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":10,"snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"},"candidates":[],"completeness_review":null,"identified_items":{"ALLOW-NATIVE":{"id":"ALLOW-NATIVE","kind":"accepted","source_ref":"user:allow-native-tools","text":"User allowed the scoped native Git/file-tool exception in Q-003, preserving the existing execution authorization and hash/scope/acceptance constraints."}},"item_bindings":{"ALLOW-NATIVE":["DEC-005"]},"kind":"saved","reply_sha256":"91bf4d149478e129a136a046c60ed015b45f6a702afadf07ad7cea40a3badaa2","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:allow-native-tools","user:directory-not-split"],"source_ref":"assistant:directory-diagnosis","summary":"Read-only follow-up: verified PR55 merged to main while PR56 merged to codex/skills-monorepo; main therefore lacks doc-coauthoring. No new scope or execution authority. Original native exception remains recorded by DEC-005.","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-directory-not-split"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"9a60a39fad7dad0d0a1121110a01b2d15207c14bb96630e768d3a0e15f98b7b0","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"110bc6023e547bfb198dfeba2fc0e2223a7abd2076c6acc5de721c4319b98c84","previous_snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","recorded_at":"2026-10-22T05:54:32.646465+00:00","relationships":[],"revision":10,"snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"User requests tracking only necessary files and identifies spec-governance, artifacts, tests/flows/plugin-integration/monorepo, validation as unnecessary. Clarify whether required CI source tests/configuration can be retained at another path; no product changes in this turn.","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:minimal-tracked-files","task_ref":"01a16186-7170-76d2-9ee2-dd2fcd07d43f","turn_id":"user-minimal-tracked-files"},"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"49d816edd4d0ed80073fe8efd702fdb2ac3f3d73f2c147538a557efac3fb38c1","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"9a60a39fad7dad0d0a1121110a01b2d15207c14bb96630e768d3a0e15f98b7b0","previous_snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","recorded_at":"2026-10-22T06:00:17.007805+00:00","relationships":[],"revision":10,"snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"baseline_contract_hash":"c933752f14dcba2e3bbc21683fab93f8834f88c53927f0914d7ccfd217fe654c","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"30109ac4a2a8cd313f2be150d5aac1f4b69cd05d1510c8f248c862aa8ffde982","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"49d816edd4d0ed80073fe8efd702fdb2ac3f3d73f2c147538a557efac3fb38c1","previous_snapshot_hash":"55015854dd3730daaf67d60b149b394a7cb07269a910f08159067ccf8e13ed89","recorded_at":"2026-10-22T06:00:20.068925+00:00","relationships":[],"revision":11,"snapshot_hash":"20cd85330801da2ab19ae8d21f6ebbd32244bc2f66a65f48a50c3929ecd55b0f","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"9c729b7f1c693ca37ee66e4d09b23be84dafeb87b68163af51d763831ce5047f","event_type":"reconcile","event_version":1,"open_decisions":["Q-004@12"],"previous_event_hash":"30109ac4a2a8cd313f2be150d5aac1f4b69cd05d1510c8f248c862aa8ffde982","previous_snapshot_hash":"20cd85330801da2ab19ae8d21f6ebbd32244bc2f66a65f48a50c3929ecd55b0f","recorded_at":"2026-10-22T06:06:00.613396+00:00","relationships":[],"revision":12,"snapshot_hash":"5d7de8b4d8be3e5b8e4f7b5147fb78ab9e77b17fa9523af223c71a7dda041968","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["DEC-006","DEC-007","DISC-005","DISC-006","DISC-007"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-006","DEC-007","DISC-005","DISC-006","DISC-007"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"6cbdd6d08f09eb10c7059dd0a5bbaab84fbaa2a664d736b11ed03b177008d264","event_type":"reconcile","event_version":1,"open_decisions":["Q-004@12：CI 必要來源與設定是否保留並搬移，或一併停止追蹤。","Q-004@12"],"previous_event_hash":"9c729b7f1c693ca37ee66e4d09b23be84dafeb87b68163af51d763831ce5047f","previous_snapshot_hash":"5d7de8b4d8be3e5b8e4f7b5147fb78ab9e77b17fa9523af223c71a7dda041968","recorded_at":"2026-10-22T06:07:47.814224+00:00","relationships":[],"revision":13,"snapshot_hash":"24fd022f30465d139d37d92847fb8a61c70cc571da4a4f99fbb5d819f6835df0","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":["AC-014","DEC-008","DISC-008","REQ-005"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-014","DEC-008","DISC-008","REQ-005"],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"fe55cdd8d397d36dc3850e58ded5880278e925b9eafc5f45d4e85c8ee63cd2c7","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"6cbdd6d08f09eb10c7059dd0a5bbaab84fbaa2a664d736b11ed03b177008d264","previous_snapshot_hash":"24fd022f30465d139d37d92847fb8a61c70cc571da4a4f99fbb5d819f6835df0","recorded_at":"2026-10-22T06:13:28.436475+00:00","relationships":[],"revision":14,"snapshot_hash":"04ed8c48ef548d4afaf5b8bfd90ea7bcf544748e874ca00e9c6ebd254d3fc7b2","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"8f335b50ea9925092d3625493ea6e2d03fecafd77ace0627e3f46cc85fdd6bbb","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"fe55cdd8d397d36dc3850e58ded5880278e925b9eafc5f45d4e85c8ee63cd2c7","previous_snapshot_hash":"04ed8c48ef548d4afaf5b8bfd90ea7bcf544748e874ca00e9c6ebd254d3fc7b2","recorded_at":"2026-10-22T06:20:18.038000+00:00","relationships":[],"revision":15,"snapshot_hash":"d8a065965e791d5ce5b4336de94b7df68bb03af8f01c7e0e30fe6b22bcb10722","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"d0a9fb16a0e0f1885453ef05643e3db0f61fa4163b8815a5677f76b29cef9c29","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"8f335b50ea9925092d3625493ea6e2d03fecafd77ace0627e3f46cc85fdd6bbb","previous_snapshot_hash":"d8a065965e791d5ce5b4336de94b7df68bb03af8f01c7e0e30fe6b22bcb10722","recorded_at":"2026-10-22T06:20:18.663953+00:00","relationships":[],"revision":15,"snapshot_hash":"e8c8e0ef3deb52acd35cba1dbba3c144e94b2cd50b1a6e8deb6c6d481cef953b","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"baseline_contract_hash":"5ec02f5ff637d90c0e3229295fdf62c0fb0275e1ce32c7c5e1104ec4b4c003bf","conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"d6b8ff9f7e8e945c74ef9acdd69ad45b05bf1ee701a3e7db6e07358142cebc40","event_type":"reopen","event_version":1,"open_decisions":[],"previous_event_hash":"d0a9fb16a0e0f1885453ef05643e3db0f61fa4163b8815a5677f76b29cef9c29","previous_snapshot_hash":"e8c8e0ef3deb52acd35cba1dbba3c144e94b2cd50b1a6e8deb6c6d481cef953b","recorded_at":"2026-10-22T06:26:05.047974+00:00","relationships":[],"revision":16,"snapshot_hash":"239aa389a5155f337b5921d3c22c797cf54368943190f20329ccf50105fcfc94","verdict":"BLOCKED","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"cb9851a81d99274519736fcbf74ee7877c3404530012d04f47af9eb9c87d668d","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"d6b8ff9f7e8e945c74ef9acdd69ad45b05bf1ee701a3e7db6e07358142cebc40","previous_snapshot_hash":"239aa389a5155f337b5921d3c22c797cf54368943190f20329ccf50105fcfc94","recorded_at":"2026-10-22T06:26:05.573513+00:00","relationships":[],"revision":17,"snapshot_hash":"8adf7be7aacf663525d455151855c7e56df4c2671eb3f839836bc8768d3cb549","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"d4c9b67ad3de436393f6b4e3d77c3f9d","event_hash":"7565980088e9c679177934bafa52c3ab3f3ae0fd938c6ad23ef2cf70315398a8","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"cb9851a81d99274519736fcbf74ee7877c3404530012d04f47af9eb9c87d668d","previous_snapshot_hash":"8adf7be7aacf663525d455151855c7e56df4c2671eb3f839836bc8768d3cb549","recorded_at":"2026-10-22T06:26:06.295055+00:00","relationships":[],"revision":17,"snapshot_hash":"7cbd1506df83be27bf0028bb259a94809151147a494b1cd3d501b0910a8e004c","verdict":"PASS","working_id":"WORKING-SPEC-125806aa6888-skills-monorepo-independent-releases"}
```
<!-- spec-audit:end -->
