---
spec_version: 1
spec_id: SPEC-0028
revision: 20
status: confirmed
change_set: test-validation-architecture
---
# 測試與驗證架構治理

## Problem
測試程式缺乏專用架構約束；驗證產物缺乏完整目錄與保存規則。env_sensing/specs/evidence 內存在三份驗證報告。

## Solution
建立固定三區、測試專用架構規則、每次執行獨立保存與全專案攔截。下列結構與驗收條件具體化已確認決策；不增加 Git 政策或外部專案修改範圍。

## User Stories
- 維護者希望測試與驗證產物的責任及存放位置可理解且可檢查。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 採測試專用架構規則：明確測試對象、fixture/mock 與共用工具的責任、依賴方向、狀態隔離；產品不可反向依賴測試；不要求每個測試函式建立完整 L0–L3 目錄。 |
| REQ-002 | 定義驗證產物的目錄責任、來源追溯及保存生命週期；資料夾結構必須讓各專案可以自行制定 .gitignore，不在共通規範指定 Git 追蹤或忽略策略。 |
| REQ-003 | 自動檢查目錄責任；specs/ 不得放測試程式及驗證產物，SPEC 僅引用驗證結果。 |
| REQ-004 | 採三區分離：tests/ 存放測試程式、fixture、mock 與測試工具；validation/ 存放驗證計畫、情境與驗收設定；artifacts/ 下專區存放報告、日誌、截圖與量測結果。 |
| REQ-005 | tests/ 以被測對象優先：模組測試位於 tests/modules/<module>/，跨模組流程測試位於 tests/flows/<flow>/；需要時再細分測試層級，按層級批次執行以標籤或設定選取。 |
| REQ-006 | fixture、mock 與測試工具採就近私有、按需共用：專用資產位於所屬模組或流程的 support/；跨被測對象共用的資產抽至 tests/support/ 並按用途拆分。禁止跨測試目錄引用私有 helper，共用支援層不得反向依賴測試案例。 |
| REQ-007 | 每次測試與驗證執行使用唯一 run-id 建立獨立產物目錄，完成後不覆寫；SPEC 引用固定執行的結果。保存期限與清理政策由各專案明訂，不由本規範指定統一天數或自動刪除。 |
| REQ-008 | 混放檢查涵蓋全專案治理範圍內的目錄與引用，包括本次未修改的既有檔案；違規列為失敗，診斷列出檔案、違反規則及預期位置，修正後才能通過。不得將僅異動檔案通過等同全專案合規。 |
| REQ-009 | 產品存取以公開契約為優先；必要時，模組自己的測試可使用由所屬模組管理的內部測試入口，不得任意改寫私有狀態；跨模組流程測試透過參與模組契約互動，測試控制操作及其接線不得進入正式發布。 |
| REQ-010 | 既有專案導入也必須統一 tests/、validation/、artifacts/，同步修正引用、runner、建置及驗證設定；不提供替代根目錄映射。 |
| REQ-011 | 測試可變狀態、臨時資源與 mock 紀錄按案例建立及清理；共用 fixture 預設唯讀。共享外部資源須宣告隔離或序列化，不依賴其他案例的順序及殘留狀態。 |
| REQ-012 | 驗證定義與執行證據明確分離。run manifest 記錄 ID、來源與設定雜湊、被測對象、場景、時間、工具、狀態、結果及產物路徑/雜湊；未完成、缺失、不一致或越界的證據不得通過驗收。 |
| REQ-013 | 全專案治理檢查不依賴 Git 追蹤或 .gitignore。目錄/引用檢查與語言依賴/發布隔離證據分開回報；缺少必要分析能力回報 BLOCKED，不得略過後宣稱整體 PASS。 |
| REQ-014 | 更新共通技能、規範、範本、寫入/讀取流程及本技能庫自身導入；保存遷移路徑與內容雜湊，不偽造歷史 run 證據，不改寫已實作 SPEC 的原始契約。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 採測試專用規則；大型測試框架的模組治理門檻仍待細化。 |
| DEC-002 | 本次限定測試架構、驗證產物目錄與保存規則、混放自動檢查；.gitignore 由各專案另行討論，撤回 Q-002 的忽略範圍選擇。 |
| DEC-003 | 選擇三區分離；測試資產、驗證定義與執行產物各有獨立目錄責任。 |
| DEC-004 | 採被測對象優先組織測試，與模組及流程責任對應。 |
| DEC-005 | 採就近私有、按需共用的測試支援資產邊界。 |
| DEC-006 | 選擇每次執行獨立保存，不採日常試跑覆寫同一暫存結果的模式。 |
| DEC-007 | 採全專案檢查並阻擋違規，不採僅攔截本次新增或修改檔案的導入模式。 |
| DEC-008 | 允許受控的測試專用操作，沿用模組私有狀態歸屬與正式發布隔離原則。 |
| DEC-009 | 既有專案導入時也必須統一目錄名稱，並修正所有引用與執行設定；不提供替代根目錄映射。 |

## Discussion Context
### DISC-001: 測試治理強度與 Git 目的

- **Situation:** development 分類未對測試程式本身建立完整結構約束。
- **Question:** 測試程式要採用哪一種架構治理強度？
- **Options and tradeoffs:** 採測試專用規則（建議）：規範測試對象、fixture/mock 與共用工具的責任、依賴方向、狀態隔離，以及產品不可反向依賴測試；不要求每個測試函式套用完整 L0–L3 目錄。適合一般測試套件，維護成本較低；大型測試框架仍需另有模組治理門檻。；全面套用產品架構：所有測試程式都納入 L0–L3、Module／Type／State 目錄與依賴檢查。適合把測試平台視為長期產品的團隊；一致性較高，但簡單測試與 mock 也需額外建模，遷移及維護成本較高。
- **User answer:** 選擇1，目前主要是方便git上傳可以直接放進gitignore
- **Explicit rationale:** 目前主要是方便 Git 上傳，可以直接放進 .gitignore。
- **Resulting impact:** REQ-001, REQ-002, DEC-001, AC-001, AC-002.

### DISC-002: 排除專案 Git 策略

- **Situation:** 前一題將資料夾規範討論延伸為 Git 忽略政策，超出使用者指定範圍。
- **Question:** 你希望 .gitignore 排除到哪個範圍？
- **Options and tradeoffs:** 只排除執行產物（建議）：集中忽略日誌、截圖、暫存及原始量測；測試程式、必要 fixture、驗證設定與精簡驗收摘要進 Git。適合需要團隊重跑與追溯的專案；需維護少量摘要，大型證據另行保存。；排除全部驗證結果：所有報告、摘要及原始證據集中忽略；測試程式與驗證設定仍進 Git。提交更精簡，也能重跑測試，但歷史驗收結果需在 Git 之外保存。；連測試程式與驗證設定都排除：整個測試、驗證區域只留本機。適合刻意只分享產品程式碼的情境；clone 後無法直接重跑這些測試，CI 與協作需另行提供檔案。
- **User answer:** 先討論規範測試程式的架構規則、驗證產物的目錄與保存規則，以及防止混放的自動檢查  ，gitignore是各別專案自行討論的。只要資料夾結構定義出來，gitignore就很方案處理了
- **Explicit rationale:** 只要資料夾結構定義出來，各專案即可方便地自行處理 .gitignore。
- **Resulting impact:** REQ-002, DEC-002, AC-002, AC-003.

### DISC-003: 三區目錄責任

- **Situation:** 需要先確認測試程式、驗證定義與執行產物的存放邊界，再細化保存及檢查。
- **Question:** 共通目錄要採哪一種責任分區？
- **Options and tradeoffs:** 三區分離（建議）：tests/ 放測試程式、fixture、mock 與測試工具；validation/ 放驗證計畫、情境及驗收設定；artifacts/ 下專區放測試與驗證的報告、日誌、截圖和量測結果。適合希望輸入與產物清楚分離的專案，混放檢查直觀；成本是多一個頂層目錄，執行工具必須統一輸出位置。；兩區分離：tests/ 放測試程式與支援資產；validation/ 內再分設定區與結果區。適合希望驗證資料集中瀏覽的專案，頂層目錄較少；但人工設定與執行產物同屬 validation/，檢查與保存規則必須細分到子目錄。
- **User answer:** 1
- **Explicit rationale:** 使用者選擇三區分離；本次未補充其他理由。
- **Resulting impact:** REQ-003, REQ-004, DEC-003, AC-002, AC-003.

### DISC-004: 測試依被測對象組織

- **Situation:** 三區責任已確認，需要讓 tests/ 內部結構反映測試的責任範圍。
- **Question:** tests/ 內部要優先依什麼分類？
- **Options and tradeoffs:** 被測對象優先（建議）：模組測試放 tests/modules/<module>/，跨模組流程測試放 tests/flows/<flow>/，需要時再細分測試層級。適合按功能維護與審查，責任清楚；批次執行某個測試層級需靠測試標籤或設定。；測試層級優先：先分單元、整合、系統等目錄，再按模組或流程細分。適合按測試層級安排執行流程，選取直觀；同一功能的測試會散在不同目錄，修改功能時需跨目錄追蹤。
- **User answer:** 1
- **Explicit rationale:** 使用者選擇被測對象優先；未補充額外理由。
- **Resulting impact:** REQ-005, DEC-004, AC-001.

### DISC-005: 測試支援資產共用邊界

- **Situation:** 被測對象優先的目錄結構需要限制私有支援資產跨目錄借用，並為共用資產建立明確入口。
- **Question:** fixture、mock 與測試工具要採哪種共用規則？
- **Options and tradeoffs:** 就近私有，按需共用（建議）：專用資產放在所屬模組或流程的 support/；確有跨對象用途才抽至 tests/support/，並按用途拆分。禁止跨測試目錄借用私有 helper，共用層不得反向依賴測試案例。適合按被測對象維護，可限制變更影響；代價是抽取共用資產時需整理介面與引用。；支援資產全部集中：fixture、mock 與工具統一放 tests/support/，按模組或用途分類；測試案例只依賴集中支援層。適合已有統一測試平台的專案，搜尋方便；但專用資產也需集中管理，共用介面與跨模組耦合較容易膨脹。
- **User answer:** 1
- **Explicit rationale:** 使用者在閱讀範例後選擇就近私有、按需共用；未補充額外理由。
- **Resulting impact:** REQ-006, DEC-005, AC-001, AC-003.

### DISC-006: 每次執行獨立保存

- **Situation:** 現有工具混用指定目錄下固定檔名寫入與部分拒絕覆寫，run-id 尚未等同於完整的歷次保存機制。
- **Question:** 測試與驗證產物要採哪種保存方式？
- **Options and tradeoffs:** 每次執行獨立保存（建議）：以唯一 run-id 建立目錄，完成後不覆寫；SPEC 引用固定的一次執行。適合追溯失敗、比較前後結果，規則一致；會累積較多資料，保存期限與清理政策由各專案明訂。；區分暫存與正式證據：日常試跑放可覆寫的暫存區，正式驗收另存不可覆寫的 run-id 目錄；SPEC 只能引用正式區。適合試跑頻繁、產物較大的專案；占用較少，但需明確區分兩種執行模式，暫存結果可能無法追溯。
- **User answer:** 1
- **Explicit rationale:** 使用者核對現況後選擇每次執行獨立保存；未補充額外理由。
- **Resulting impact:** REQ-007, DEC-006, AC-002.

### DISC-007: 全專案混放檢查

- **Situation:** 若只檢查異動檔案，未修改的既有 specs/evidence 混放可能持續存在。
- **Question:** 混放自動檢查要採哪種攔截範圍？
- **Options and tradeoffs:** 全專案檢查並阻擋違規（建議）：檢查專案治理範圍內的目錄與引用，既有混放也列為失敗；列出檔案、違反規則與預期位置，修正後才能通過。適合建立一致的共通規範，可抓到未修改的 specs/evidence；初次導入需整理既有資料。；只阻擋本次新增或修改的違規：舊有混放另列清單，本次涉及的檔案必須修正。適合需要分階段導入的既有專案，初期整理成本較低；需維護基準與後續清理計畫，通過檢查不代表全專案已合規。
- **User answer:** 1
- **Explicit rationale:** 使用者選擇全專案檢查並阻擋違規；未補充額外理由。
- **Resulting impact:** REQ-008, DEC-007, AC-003.

### DISC-008: 受控的內部測試入口

- **Situation:** 說明正常操作與由模組提供測試專用操作的差異後，確認測試對產品內部的存取限制。現有 codebase-design 與 runtime-validation 已有 own-test internal seams 與 release wiring 隔離原則。
- **Question:** 是否允許模組提供「只供測試使用」的操作，協助測試難以觸發的內部情況？
- **Options and tradeoffs:** 允許，但要受控（建議）：一般測試走正常操作；必要時，模組自己的測試可呼叫專用操作來模擬內部故障。只能由所屬模組管理，不能任意改私有變數，正式發布不得包含這些控制操作。較容易測到罕見情況，但要檢查發布隔離。；不允許：測試只能使用產品原本提供的操作，透過輸入與外部條件觸發問題。規則較簡單，也較貼近實際使用；但罕見的內部情況可能較難測到，或需要重新設計模組。
- **User answer:** 1
- **Explicit rationale:** 使用者選擇允許但受控；未補充額外理由。後續詢問現況並未撤回此選擇。
- **Resulting impact:** REQ-009, DEC-008, AC-001, AC-003.
### DISC-009: 固定目錄與既有專案導入

- **Situation:** 確認既有 tools/tests/ 等位置能否作為替代根目錄保留。
- **Question:** 既有專案導入時，是否也必須統一成指定的目錄名稱？
- **Options and tradeoffs:** 必須統一（建議）：既有 tools/tests/ 等測試位置也移入 tests/，驗證定義與產物分別歸入 validation/、artifacts/，同步修正引用和執行設定。跨專案一致、混放規則簡單；導入時需承擔搬移與工具相容調整成本。；允許明確登記的替代位置：新專案採標準目錄，既有專案可登記原有目錄對應的責任，仍禁止不同責任混放，也不得將產物留在 specs/。可減少搬移、保留工具相容性；檢查器須理解映射，跨專案的實際目錄不完全一致。
- **User answer:** 1
- **Explicit rationale:** 使用者選擇必須統一；未補充額外理由。
- **Resulting impact:** REQ-010, REQ-014, DEC-009, AC-004, AC-007.

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-005, REQ-006, REQ-009, REQ-011 | 模組/流程分類正確；跨範圍私有 helper、共用層反向依賴案例、產品依賴測試及測試控制進入 release 均不可通過；案例不依賴先前案例的狀態。 | 正反依賴樣本、重排/重跑/並行狀態測試及適用 analyzer/release 組成檢查。 | Pending execution. |
| AC-002 | REQ-002, REQ-004, REQ-007, REQ-012 | 設定及結果分区；連續/並行執行使用獨立 run-id；已完成結果拒絕覆寫；中斷資料不能成為验收證據。 | 獨占建立、故障注入、重跑、固定引用與 hash 反例測試。 | Pending execution. |
| AC-003 | REQ-003, REQ-006, REQ-008, REQ-013 | 未修改的 specs/evidence、設定區報告、舊測試根及非法引用也被攔截；診斷包括路徑、規則及預期位置。 | 含 tracked/untracked/ignored 治理檔案的正反 fixture 與結束碼檢查。 | Pending execution. |
| AC-004 | REQ-010, REQ-014 | 本技能庫及舊專案測試樣本統一目錄，runner/文件/來源清單/組裝引用無失效路徑。 | 完整 layout gate、路徑檢查、乾淨副本核心測試及 plugin distribution 驗證。 | Pending execution. |
| AC-005 | REQ-012, REQ-013 | 未知分類/owner、缺 analyzer、未解動態依賴、越界路徑或 hash 不符均不得整體 PASS。 | 逐項反例驗證 FAIL/BLOCKED，合法完整案例必須通過。 | Pending execution. |
| AC-006 | REQ-002, REQ-007, REQ-014 | 不修改 Git 政策、不自動清理、不將舊證據冒充新執行；遷移内容與原始路徑可追溯。 | 差異審查、遷移前後 hash 與對照、拒絕歷史證據重新綁定測試。 | Pending execution. |
| AC-007 | REQ-013, REQ-014 | router、architecture gate、verification-ladder、validate-on-device 與 delivery 對新目錄及證據採一致規則；缺能力不降級通過。 | Host 整合回歸、架構 gate/render、技能組裝及發行內容檢查，不聲稱裝置通過。 | Pending execution. |

## Relationships
| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-002 |
| REQ-004 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-004 |
| REQ-006 | depends_on | DEC-005 |
| REQ-007 | depends_on | DEC-006 |
| REQ-008 | depends_on | DEC-007 |
| REQ-009 | depends_on | DEC-008 |
| REQ-010 | depends_on | DEC-009 |
| AC-001 | depends_on | REQ-001 |
| AC-001 | depends_on | REQ-005 |
| AC-001 | depends_on | REQ-006 |
| AC-001 | depends_on | REQ-009 |
| AC-001 | depends_on | REQ-011 |
| AC-002 | depends_on | REQ-002 |
| AC-002 | depends_on | REQ-004 |
| AC-002 | depends_on | REQ-007 |
| AC-002 | depends_on | REQ-012 |
| AC-003 | depends_on | REQ-003 |
| AC-003 | depends_on | REQ-006 |
| AC-003 | depends_on | REQ-008 |
| AC-003 | depends_on | REQ-013 |
| AC-004 | depends_on | REQ-010 |
| AC-004 | depends_on | REQ-014 |
| AC-005 | depends_on | REQ-012 |
| AC-005 | depends_on | REQ-013 |
| AC-006 | depends_on | REQ-002 |
| AC-006 | depends_on | REQ-007 |
| AC-006 | depends_on | REQ-014 |
| AC-007 | depends_on | REQ-013 |
| AC-007 | depends_on | REQ-014 |

## Out of Scope
.gitignore、Git 追蹤/取消追蹤、提交、推送與發布政策由各專案另定，本變更不代為執行。
env_sensing 僅作為問題案例；本變更不直接搬移該專案或其他外部專案、不改產品功能、不部署裝置。
不新建通用大型測試框架，不強制每個測試函式加入產品 L0–L3/Type/State catalog。測試支援適用專用規則；獨立交付的測試平台沿用既有產品治理。
不指定統一保存天數、不自動刪除證據。

## Open Decisions
None.

## Routing/Gates
ask-matt → spec-governance/grilling → confirmed SPEC → scoped execution authorization → formatter/architecture design → implementation and host verification → Standards/Spec review.
執行前完成 Boundary/Type/State ownership、source sets 及語言分析配置；architecture_cli.py 為唯一公開架構 gate，並驗證生成視圖一致性。採顯式版本化 validation/layout.yaml 初版 schema_version: 1，與既有 architecture 2.2.0 分開釘選；缺少新政策回報需要導入，不默默重解讀舊專案。
本專案為 host-side 規範/工具驗證，不主張裝置、效能或即時性 PASS。依既有梯級建立本 SPEC 的 AC mapping。目前選用的 Python 缺少 PyYAML，已由 project_validation.py 的 ModuleNotFoundError 證實；實作驗證前需使用具備依賴的 runtime，不把本次規格驗證當作 project validation 通過。

## Question Record

```json
{
  "question_id": "Q-008",
  "history": [
    {
      "action": "revise",
      "question": {
        "id": "Q-008",
        "version": 16,
        "question": "測試對產品程式的存取，要採哪種邊界？",
        "options": [
          "公開契約優先，內部入口受控（建議）：模組測試必要時可使用由該模組維護的內部測試入口；流程測試只經過參與模組的契約互動。不得任意改寫私有狀態或讓測試控制入口進入正式發布。適合需要驗證演算法邊界與故障情境的專案；需檢查入口歸屬與發布隔離。",
          "一律只測公開契約：模組與流程測試皆不使用內部測試入口。適合能從外部完整驗證行為的模組，較不受內部重構影響；難以觸發的內部故障或邊界情境，可能需要重新設計模組或增加測試成本。"
        ]
      },
      "source_ref": "current-task:user-clarification-not-understood-Q-008",
      "user_text": "不懂這個問題"
    }
  ],
  "failed_surfaces": {}
}
```

## Concrete directory contract

```text
tests/
  modules/<module-id>/
    test files
    support/                    # private fixtures, mocks and helpers
  flows/<flow-id>/
    test files
    support/
  support/<capability>/         # explicitly shared test assets
validation/
  layout.yaml                  # versioned roles, ownership, output bindings
  verification-ladder.yaml
  on-device.yaml               # when applicable
  acceptance-SPEC-####.json     # authored acceptance mapping
  plans/                       # reusable authored plans when needed
artifacts/
  tests/<run-id>/
  validation/<run-id>/
    manifest.json
    plan.snapshot.json
    evidence.json
    reports/
    logs/
    captures/
specs/
  SPEC-####-<slug>.md
  history/                     # existing allowed normalized SPEC history
```

Directories are created only when needed; tests/ runs use the same run-manifest contract. Module/Flow ownership resolves from the architecture manifest rather than guessed path names. Do not offer alternate test-root mappings. General build/development tooling remains in its declared role; not every tools/ script is test code. Device test-runner source belongs in tests/, declarative scenario input in validation/.

Fixtures/templates are declared inputs even when their extensions resemble reports. Promoting captured data to a fixture creates a curated input with provenance and does not mutate the original run. spec-governance/ retains specification discussion state; generated execution plan snapshots and logs move to artifacts/. Canonical architecture/generated/ views retain their existing documented location; per-run gate reports are artifacts. Third-party and build-output roots retain their provenance-controlled roles.

## Run lifecycle and reference contract

Allocate a unique run-id and exclusively create the run directory. An existing guided session's run identity is retained, not replaced. Duplicate destination is rejected. While running, collect files; publish a terminal manifest atomically after hashes and outcome are available. Completed runs can have PASS, FAIL or BLOCKED outcomes and are immutable thereafter. A crash leaves an incomplete run; no acceptance may cite it as complete. Reruns create new IDs. No overwrite, append, relabel or silent hash refresh of a finalized run.

Manifest metadata includes schema version, run-id, UTC start/end, test/validation kind, Module/Flow/scenario, SPEC/AC when applicable, command/tool version, source revision and dirty-source digest when relevant, config/profile/plan hashes, execution status/verdict, relative artifact paths and SHA-256. Do not collect secrets or unnecessary environment values. Ordinary module tests need not invent a SPEC.

Keep raw evidence, reports and generated plan snapshots with their run. Authored acceptance mappings remain in validation/. Generated validation/evidence-SPEC-####.json and spec-governance/validation-SPEC-####.json are replaced by the selected run's evidence.json and plan.snapshot.json; all consumers receive an explicit run/manifest reference. An acceptance decision may cite multiple fixed runs. Never select newest files or use a mutable latest link as the evidence identity.

Paths remain within allowed project roots; reject traversal and symlink/junction escapes. Check missing files, provenance, metadata and hashes; hashes establish integrity, not authentic observations. Project-owned retention must not silently leave active acceptance references claiming valid deleted evidence.

## Whole-project checker

validation/layout.yaml supplies explicit roles, ownership, intentional fixtures, output bindings and required analyzers. Combine these declarations with architecture source sets and filesystem discovery. Do not decide semantic role from extension alone or exempt development wholesale. Scan project-owned governance scope including unchanged/ignored/untracked governed files. Gitignore cannot suppress it. Third-party/build exclusions require explicit provenance and cannot hide project-owned tests/reports.

Each governed entry has exactly one valid role. Unknown/ambiguous role, unknown owner or missing required capability is BLOCKED; proven misplaced data or illegal dependency is FAIL. Both block completion. Stable diagnostics show rule ID, path, expected role/location and reason. Checker never auto-moves or deletes.

Check specs/ evidence, tests/ execution output, validation/ generated reports, old test roots, undefined owners, private-support cross-use, support back-edges, production-to-test dependencies, output escapes, invalid run references and release test-control leakage. Reuse a single policy implementation through existing architecture/validation/delivery gates. Writers validate output admission; whole-project checking catches out-of-band files.

Existing Python and C/C++ analyzers provide the initial dependency integration. All languages receive role/path/reference checks; further dependency or release-isolation claims require a capable language/build/runtime evidence adapter. Report per-rule coverage and leave required unknown claims BLOCKED. Do not promise arbitrary file semantic recognition or prove runtime state isolation with path checking alone.

## Architecture impact

Use architecture_governance_cli (L0) and governance_workflow_domain for layout assessment, verification_ladder_domain for plan/evidence binding, spec_governance_domain for fixed evidence references, and delivery_workflow_domain/project_validation_composition for admission. validate-on-device's runner/adapters own output I/O and run transitions. Domain modules own policy; adapters own filesystem effects. Complete detailed boundary, type and state tables before source changes.

Development tests stay outside production Type/State catalogs and gain dedicated ownership/dependency checks. Each test owns setup/reset/cleanup; shared input is read-only by default, and shared external resources declare isolation. Private test seams follow REQ-009. File length alone does not trigger a new full product hierarchy; independently shipped platform code follows existing production rules.

Description Views: update source paths, gate/validation invariants and entrypoints in the manifest; regenerate applicable System/Parent views through the renderer. Update generated tool mirrors and distribution by assembly, never by hand. Prepare a proposed ADR for fixed roots/immutable run storage; do not create AI-approved exceptions or approval metadata.

## Algorithm screening and flow review

Full inventory/classification/reference validation is algorithm-bearing: observable decisions and failure behavior change. Select deterministic enumeration + explicit role/owner matching + existing analyzer edges. Filename-only heuristics are rejected because fixtures and live evidence can share extensions. Changed-files-only scanning is rejected by DEC-007. A proposed Algorithm Design Record owned by governance_workflow_domain must capture ordered classification, graph edges, diagnostic ordering, verdict aggregation, complexity and AC-003/AC-005 golden cases before implementation. All declared invalid samples must avoid false PASS.

Run allocation/finalization is algorithm-bearing: select exclusive allocation plus atomic terminal manifest publication; fixed-path overwrites are rejected by DEC-006. An external state database is unnecessary for this local artifact contract. Record transitions and crash/duplicate/parallel behavior under the validation policy owner with filesystem I/O delegated to its adapter. Validate AC-002 fault and concurrency cases.

As-is flow: caller-selected output → fixed evidence paths → acceptance. Proposed flow: declared inputs → exclusive run → collection/evaluation → finalized manifest → explicit acceptance reference. Preserve verdict authority and verification-layer semantics. Pure post-hoc scanning cannot prevent a completed run from being overwritten; writer admission plus full scan is selected. No background polling, new device protocol, target thread, queue or scheduling change.

Host work is proportional to governed files/edges and referenced bytes hashed. Avoid unnecessary binary reads; retain applicable bounded read/subprocess contracts. No measured speedup or target performance claim is made. Host regression validates correctness; no hardware benchmark is needed for directory/evidence correctness. New or unresolved load-bearing performance claims require the existing Flow-review gates rather than assumptions.

## Delivery and migration

This change updates the common skill source, associated human docs/templates, relevant checker/runner/readers and this repository's own tests/validation outputs. env_sensing and other external project migrations remain separate work. The selected uniform-directory rule governs their future adoption without authorizing their mutation now.

After scoped execution authorization:[REDACTED: credential] formatter and architecture design gates; integrate versioned layout/run contracts; update writers/readers and single-source distribution; migrate own assets and references preserving unrelated edits; regenerate views; validate AC-001 through AC-007, host Windows/Linux support, architecture development/render gates, plugin unit/integration/distribution and Standards/Spec review. Publication, Git operations and device actions are excluded.

Legacy evidence is inventoried under artifacts/ with a migration manifest preserving original path, bytes/hash and known provenance. Missing old metadata stays unknown; do not manufacture past run IDs or relabel old results as new acceptance. Immutable implemented SPEC text remains unchanged; use an explicit migration cross-reference for historic paths and update editable consumers to canonical references. No retained legacy test-root aliases substitute for migration.

## Impacts and tradeoffs

Benefits: consistent roots, visible test ownership, fixed evidence references and whole-project diagnostics. Costs: initial path/runner migration, additional host scanning, and accumulated per-run storage until project-owned cleanup. No Git policy is imposed. All behavior and delivery claims remain pending implementation evidence.

## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-18 | 開始討論使用者指定的三項治理缺口。 |
| 3 | 2026-09-18 | 確認測試專用規則；記錄以 Git 忽略管理為主要目的。 |

| 5 | 2026-09-18 | 撤回 Git 忽略政策問題，聚焦共通目錄與架構規範。 |

| 7 | 2026-09-18 | 確認 tests/、validation/、artifacts/ 三區分離及 specs/ 混放限制。 |

| 9 | 2026-09-18 | 確認 tests/ 以模組與流程等被測對象優先分類。 |

| 11 | 2026-09-18 | 確認測試支援資產就近私有、按需共用及依賴邊界。 |

| 13 | 2026-09-18 | 確認每次執行獨立 run-id、完成後不覆寫與專案自訂保存期限。 |

| 15 | 2026-09-18 | 確認全專案治理範圍混放檢查，既有違規同樣阻擋通過。 |

| 18 | 2026-09-18 | 確認模組內部測試入口受控，保持私有狀態歸屬與正式發布隔離。 |
| 20 | 2026-09-18 | 確認固定目錄導入，完成目錄/run/檢查/遷移與驗收規範。 |

