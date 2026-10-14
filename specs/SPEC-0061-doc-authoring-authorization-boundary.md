---
spec_version: 1
spec_id: SPEC-0061
revision: 7
status: confirmed
change_set: doc-authoring-authorization-boundary
working_id: WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary
task_ref: 01a13976-3449-7752-91a2-57fce7838927
branch_ref: Branch_governed-engineering-skills@0.20.0
---
# 文件撰寫與實作授權分離修改方案

## Problem
使用者澄清「開始執行」僅限制實作，文件撰寫不需該授權。0.20.0 部分技能及寫入工具仍把文件與實作混合限制。

## User Stories
使用者希望討論與文件工作可持續完成，並保留實作的獨立授權邊界。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 文件建立、修改、保存及純文件生成不要求實作開始執行；仍保留路徑、基底與並行寫入保護，不產生實作授權。 |
| REQ-002 | 移除Plugin生命週期hooks註冊、專用adapter/啟動器與必要hook證據；保留明確呼叫的owner/router/admission與歷史紀錄。 |
| REQ-003 | 正式模組的host功能語義驗證必須規劃模組契約與SIL，不因沒有獨立模擬整合claim而排除；文件內容檢查不使用此claim。 |
| REQ-004 | SIL證據必須列正式模組、公開介面、案例、正式來源雜湊與實際執行命令/結果；缺少或過期證據不能通過驗收。 |
| REQ-005 | 保留外部Fake/Replay與內部正式實作，跨模組測整合；報告分列SIL、adapter/整合、build、Web、AST/架構及適用PIL/HIL/System。 |
| REQ-006 | 同步技能、共用契約、docs、schema、架構/分發及有意義的行為測試；基於0.22.0來源，保存minor changeset供後續版本流程使用。 |

## Decisions

| ID | Decision | Source |
| --- | --- | --- |
| DEC-001 | 移除 Plugin 生命週期 hooks；保留由技能流程明確呼叫的討論保存、路由、文件更新及實作授權檢查。此決定不等於已授權修改程式或安裝內容。 | user:20261014:annotation-1「這個不要了」 |
| DEC-002 | 模組化程式的測試以完整模組的正式實作與公開介面為邊界，透過輸入、公開函式/事件序列及可觀察結果驗證行為；不以零碎內部函式或簡化重寫模型替代。 | user:20261014:module-testing-annotation-1 |
| DEC-003 | 技能中的模組 SIL 以主機執行正式模組公開介面的功能案例為核心；必要外部依賴使用 Fake/Replay，不要求另有「獨立模擬整合 claim」才可認定，也不以建置或 AST 替代。須核對實際正式實作、案例與證據，不能只改測試名稱。 | user:20261014:sil-public-interface-answer |
| DEC-004 | 採用完整模組公開介面測試輸入/輸出、狀態轉移、事件順序與錯誤恢復；只模擬外部依賴，保留內部演算法/狀態機；跨模組另做整合；依需求安排Module Contract、整合、Adapter Contract、SIL/PIL/HIL與System。 | user:20261014:module-policy-adopt-annotation-1 |
| DEC-005 | 採用功能變更先列受影響模組/公開介面/案例；符合正式實作加外部模擬依賴的既有案例納入模組SIL；真正執行，缺案例或證據不能宣稱功能驗證完成；報告分列模組SIL、整合、建置、Web及AST/架構結果。 | user:20261014:module-policy-adopt-annotation-4 |
| DEC-006 | 建置後準備/燒錄已識別的測試映像，再依需求進行PIL/HIL：PIL執行目標處理器上的正式模組及受控輸入，HIL使用對應硬體/即時模擬環境及真實I/O。需具備測試輸入、harness、觀察/停止条件；建置/燒錄不等於測試PASS。本訊息未要求現在燒錄或操作別的專案。 | user:20261014:module-policy-annotation-5 |


## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 無execution receipt可安全保存文件，不能寫產品程式、技能規則或runtime設定；過期基底保留原檔。 | public managed writer behavior tests | Pending |
| AC-002 | REQ-002 | source/assembled Plugin無hooks註冊或專用adapter，手動discussion及產品授權回歸仍有效。 | distribution and owner regression tests | Pending |
| AC-003 | REQ-003 | matched rule漏sil仍選module-contract與sil；明確排除sil或缺harness不能悄悄通過host功能計畫。 | production planner CLI regression tests | Pending |
| AC-004 | REQ-004 | SIL缺runner、模組/公開接口/案例、執行結果或正確來源hash均BLOCKED；完整對應證據可PASS。 | public project acceptance behavioral fixtures | Pending |
| AC-005 | REQ-005 | 共用測試契約明確完整正式模組與各環境證據；建置/燒錄不等於PIL/HIL通過，分項結果可辨識。 | focused contract/document checks and module suites | Pending |
| AC-006 | REQ-006 | 組裝產物與來源一致，必要引用完整，focused regression/formatter/architecture檢查通過。 | assembly validation, regression, formatter and architecture gate | Pending |

## Relationships
None. SPEC-0057 作為歷史參考，沒有繼承其授權或當前驗證結論。

## Out Of Scope
不修改ESP32專案、不燒錄設備、不安裝或發布外掛、不進行Git commit/push；允許本倉庫技能/工具/測試/說明及本地驗證組裝。

## Open Decisions
None.

## Routing/Gates
使用者已先明確開始執行，再授權基於已pull的0.22.0修改；暫停後以「繼續執行」恢復同一範圍。沿用授權，不新增授權問題。以固定可用來源/工具維護此治理工具，不讓工具自身相容性掃描成為自我維修的循環前提。

## Revision History
r1：保存使用者原則、來源事實、候選方案、替代方案及預期驗收矩陣。
r2：將空的未決事項標記正規化，未更改候選方案範圍。
r3：記錄使用者移除 hooks 的 DEC-001，修訂方案入口，補上 SIL/HIL 項目、風險分類實際行為及來源說明。
r4：依使用者澄清記錄 DEC-002，改以完整模組公開介面為測試中心；移除文件測試的自動 SIL 命名，分開測試範圍、案例與執行環境；校正 SIL/PIL/HIL 全名及 HIL 與真實模擬環境的互動定義。
r5：讀取指定聊天及ESP32案例，核對正式模組主機測試與證據；記錄DEC-003，指出SIL被matrix明列不適用的實際原因，提出分類、映射與完成報告修正。
r6：保存採用與階段說明。
r7：將已採用範圍整理成REQ-001–006及AC-001–006；以0.22.0為實作基準，記錄開始執行/繼續執行授權與驗證計畫。

## Discussion Context
來源 user:20261014:authorization-intent：「開始執行」只想卡住實作部分，文件部分不需要授權。
來源 user:20261014:提出修改方案：本回合要求提出修改方案。
來源 assistant:20261014:authorization-boundary-proposal：候選方案已保存，非使用者採用或執行授權。
來源 user:20261014:annotations-sil-hil：Annotation 1 決定移除 hooks；Annotation 2 詢問 R0–R3 判定；Annotation 3 詢問 SPEC-0057 內容；Annotation 4 詢問上游是否有 SIL/HIL；Annotation 5 詢問 ask-matt 與風險路由分工；主訊息指出缺少 SIL/HIL 測試項目。

## Acceptance Mapping

```json
{
  "AC-001": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  },
  "AC-002": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  },
  "AC-003": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  },
  "AC-004": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  },
  "AC-005": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  },
  "AC-006": {
    "evidence_claims": [
      "host-semantics"
    ],
    "contract_dimensions": [
      "call-order"
    ],
    "execution_changes": [],
    "rationale": "Complete production module interfaces with external fixtures on the host; no hardware claim."
  }
}
```

## Solution

# 修改方案：文件撰寫與實作授權分離

日期：2026-10-14（Asia/Taipei）
狀態：候選方案；已保存文件，未確認本方案、未取得本方案的實作授權。
基準：已安裝 governed-engineering-skills 0.20.0 與來源分支 Branch_governed-engineering-skills@0.20.0。

## 目標與已確認原則

使用者已明確澄清：「開始執行」原本只想限制實作；文件撰寫不需要這項授權。使用者本回合要求提出修改方案。這兩項指示允許調查和撰寫本文件，不代表已採用下列候選實作。

1. 討論、文件建立、修改、保存與文件衍生產物生成，不因缺少「開始執行」而停止。
2. 文件保存、內容確認、實作授權保持不同意義。文件保存不能自動接受 ADR 或替使用者作尚未決定的設計選擇。
3. 程式、測試程式及會改變產品執行行為的設定修改，仍使用目前範圍有效的「開始執行」。
4. 文件與程式混合任務先完成文件工作；只讓實作部分等待授權。

## 現況與證據

- 安裝版 ask-matt/SKILL.md 約第 213–215 行，把 CONTEXT.md、ADR、架構產物及生成檔與產品程式一起限制。
- 安裝版 spec-governance/SKILL.md 約第 153–156 行也把上述文件列入實作授權要求。
- implement/scripts/managed_delivery.py 的 _apply 在解析目標前呼叫 _admit，普通文件若走產品寫入入口，就依賴實作 receipt。
- implement/scripts/discussion_hook.py 的恢復例外主要涵蓋讀取與特定 DISCUSSION-REQUEST 寫入；尚不能直接代表所有一般文件入口都被允許。
- 已存在 SPEC-0057-discussion-document-lifecycle.md，記錄相同原則及候選／確認流程。它的舊驗證報告有範圍限制，不能代表目前分支、完整回歸或安裝版通過。
- 目前分支缺少 SPEC-0057 引用的 document-governance.md 與 document-ownership.md；因此先核對來源與提交，再決定整合既有成果或補足缺口，不按歷史文字假定程式已完成。

## 建議規則

> 「開始執行」僅授權指定範圍的實作。討論與文件工作可在沒有實作授權時持續進行，包括 SPEC、方案、需求、CONTEXT、ADR 草稿、架構設計來源、圖表、索引、導讀、研究與驗證計畫，以及純文件衍生產物。文件保存或內容確認不得建立實作 receipt。需要使用者決定的內容仍保留為候選；正式決策依原有確認規則處理。

分類以本次操作效果、來源與使用方式為依據，不僅看副檔名。架構 manifest 作為設計文件的編寫屬文件工作；被產品載入的 runtime config、可執行生成碼、測試程式及建置／部署設定的行為修改屬實作。把程式碼放進 Markdown 並執行或抽取成產品碼，仍按實作處理。

文件中的 skill 規則草稿可撰寫；將候選規則套用到啟用中的技能、工具或 hook 而改變外掛操作行為，屬本外掛的實作修改。這項分類不能拿來阻擋一般文件作者工作。

文件格式化與文件圖表生成可直接進行；程式格式化與可執行產物生成維持實作授權。發布、Git、安裝、硬體操作依既有個別授權規則處理，不從文件寫作推定授權，也不新增文件「開始執行」門檻。

## 修改範圍與影響

| 修改群組 | 具體變更 | 收益與代價 |
|---|---|---|
| 共用授權契約 | 在既有 owner/managed-delivery 契約集中定義文件與實作操作，區分內容確認與實作 receipt | 消除各技能解讀差異；需要核對所有入口 |
| 技能及說明同步 | 更新 ask-matt、spec-governance、grilling、grill-with-docs、domain-modeling、架構及方案入口，以及相應 docs | 使用者能在討論中取得完整文件；不能只改一段提示文字 |
| 文件與實作寫入 | 沿用文件 owner 的寫入路徑，文件不呼叫產品實作 admission；產品路徑維持既有 receipt 檢查。由技能流程明確呼叫共用分類，不使用生命週期 hooks | 工具行為符合文件承諾；需處理混合操作與分類不明的情況 |
| 移除 hooks | 移除 Plugin hooks 註冊、hook 事件設定、專用啟動器與 adapter，以及打包產生流程和 hook-only 驗證依賴。保留 owner/router/admission 與歷史證據 | 減少宿主事件、信任、載入及自動阻擋的耦合；失去事件自動觸發保障，不能宣稱攔截所有工具 |
| 狀態與報告 | 文件可在 working 狀態更新；內容確認不建立 receipt。纯文字與歷史更新不撤銷既有實作授權；實作需求/驗收語義改變時只暫停相關實作 | 減少重複授權；必須保留 contract/hash 驗證與可靠語義對照 |
| 封裝一致性 | 驗證共用參照存在、來源→組裝產物→實際安裝檔一致；部署/安裝另依授權完成 | 避免來源已修但 0.20.0 安裝仍舊；增加分發檢查 |

文件更新仍保留最新基底、並行寫入保護、衝突保留、來源歷史與格式/連結檢查。缺少實作授權不能被回報成文件寫入失敗原因；真正的文件 I/O、衝突與必要內容確認問題仍如實回報。

## 架構、演算法及效率影響

- 沿用既有 discussion owner、文件更新引擎與 managed delivery，不建立新技能、第二份 SPEC 或第二套文件生命週期。
- 實作時在既有工作流模組中增加/整理共用操作分類，文件與產品寫入入口均消費同一契約；需更新受影響 manifest、來源對應與生成視圖。
- 操作分類及授權判斷會改變可觀察结果，屬規則演算法變更；在實作前記錄輸入、分類優先序、混合操作、未知操作與錯誤結果，再以行為矩陣驗證。
- 主要收益是文件討論不中斷及流程一致性，不宣稱執行效能提升。沒有新增產品排程、裝置或即時性需求。

## 替代方案

| 方案 | 優點 | 缺點 | 判斷 |
|---|---|---|---|
| 只改 SKILL.md 文字 | 成本低 | 工具仍可能阻擋文件 | 不足以滿足需求 |
| 對所有 .md/.yaml 寫入豁免 | 規則簡單 | 副檔名不能區分設計文件、產品設定及可執行生成碼 | 不建議 |
| 共用操作分類＋入口同步＋分發檢查 | 可驗證文件不中斷，並保留實作邊界 | 需做跨入口回歸與封裝核對 | 建議 |

## 實作順序

1. 核對 SPEC-0057 及相關提交/來源；先恢復正確依賴關係，保留現有未提交工作。
2. 確定共用文件/實作分類契約，更新技能文字與對應說明。
3. 調整文件 owner、managed delivery 與 router 的操作判定；移除 hooks 註冊、專用執行 adapter、生成來源及 hook-only 驗證義務，保留產品 admission。
4. 執行行為及跨入口回歸，檢查並行保存與歷史授權相容性。
5. 依已授權範圍組裝與核對產物；正式版本、安裝及發布另遵守現有流程。

## 驗收條件與預期證據

以下為候選驗收計畫，尚未執行本方案測試。

| 編號 | 場景與方法 | 通過條件／證據 |
|---|---|---|
| AC-001 | 無實作 receipt，從各文件入口建立/更新 SPEC、CONTEXT、ADR 草稿、架構文件及說明文件 | 文件成功保存；未要求「開始執行」；receipt 前後一致 |
| AC-002 | 確認相關文件內容並套用文件來源/圖表/索引 | 只驗證必要內容確認、來源基底與文件契約；不要求產品 receipt |
| AC-003 | 同一組文件／程式混合請求，無實作授權 | 文件可完成；程式、測試與產品設定保持未寫入 |
| AC-004 | 純文件修改及實作需求語義修改，前後比對授權 | 純文字/歷史修改保持同範圍授權；語義改變只使相關實作等待有效授權 |
| AC-005 | 文件寫入、確認、格式化、圖表生成後嘗試產品写入 | 未產生新 receipt；未授權產品寫入仍被拒絕 |
| AC-006 | .md 內可執行生成碼、runtime YAML、混合 patch 及未知分類案例 | 不能靠副檔名進入文件豁免；不明實作仍拒絕，獨立文件可繼續 |
| AC-007 | 並行文件改動、基底過期、文件 I/O 故障 | 保留雙方內容/歷史；不冒充成功、不要求實作授權解鎖文件 |
| AC-008 | 掃描受影響技能/docs 並重放 router/owner/managed-delivery 入口 | 無殘留文件「開始執行」限制；無 hooks 註冊及專用載入依賴；分類結果與上述矩陣一致 |
| AC-009 | 分發驗證、共用參照檢查、組裝與安裝檔比對 | 所有必要參照存在；宣告版本與實際生效檔案相符 |

測試沿用 tests/flows/plugin-integration/plugin 中的 discussion-entry、managed-delivery、spec-contract、document-lifecycle/collection 回歸，先核對其在目標分支的依賴與可執行性。候選命令：

```powershell
py -3.13 -m unittest discover -s tests/flows/plugin-integration/plugin -p test_discussion_entry.py
py -3.13 -m unittest discover -s tests/flows/plugin-integration/plugin -p test_managed_delivery.py
py -3.13 -m unittest discover -s tests/flows/plugin-integration/plugin -p test_document_lifecycle.py
py -3.13 scripts/validate_distribution.py
```

保存實際命令、exit code、必要輸出、fixture 的前後檔案雜湊與 receipt 狀態。遇到舊 adapter 或來源缺失，報告受影響場景並修復依賴，不能改低驗收條件或引用舊 run 當成此次 PASS。涉及模組邊界、型別或狀態變更時再加對應 architecture gate；本外掛此次變更沒有實體控制器與模擬環境的在迴路需求。測試首先按完整模組契約設計；路由/驗證計畫產生器的行為測試若適用，測的是該模組本身，不是執行 HIL，也不因在電腦上運行就自動命名為 SIL。

## 確認與執行狀態

文件不需實作授權這項使用者原則已明確。以上具體修改、分類實作、測試與分發範圍仍是候選方案，尚未採用；未取得本方案的「開始執行」。

## 來源

- 使用者本聊天對授權原始意圖的澄清與「提出修改方案」。
- [安裝版 ask-matt](C:/Users/hugo_peng/.codex/plugins/cache/governed-engineering/governed-engineering-skills/0.20.0/skills/ask-matt/SKILL.md:213)
- [安裝版 spec-governance](C:/Users/hugo_peng/.codex/plugins/cache/governed-engineering/governed-engineering-skills/0.20.0/skills/spec-governance/SKILL.md:153)
- [安裝版 managed delivery](C:/Users/hugo_peng/.codex/plugins/cache/governed-engineering/governed-engineering-skills/0.20.0/skills/implement/scripts/managed_delivery.py:285)
- [既有 SPEC-0057](C:/Users/hugo_peng/skill/skills/specs/SPEC-0057-discussion-document-lifecycle.md:20)
- [SPEC-0057 舊驗證報告](C:/Users/hugo_peng/skill/skills/artifacts/validation/spec0057-document-lifecycle-20261014-01/report.md)

## 本次補充：hooks、風險路由與驗證層

### 已採用的 hooks 移除決定

hooks 原本在宿主啟動/恢復聊天、接收使用者訊息、準備工具操作、準備結束回覆時，自動呼叫一段程式檢查討論與 SPEC 同步；PreToolUse/Stop 有可能拒絕操作或要求繼續保存。它是自動事件入口，不是 SIL、HIL 或實作授權本身。

依 DEC-001，本方案移除生命週期 hooks，而不是改名或以另一種宿主事件入口替代。保留一般技能流程中的 owner/router/admission 呼叫，保存歷史 hook 證據但不要求新任務提供 hook firing 證據。回歸需證明 Plugin manifest 不含 hooks 登錄、分發不重新產生 hooks、無 hook-only 驗收規則阻擋非 hook 工作。普通 Adapter Contract Test 仍保留。

### R0–R3 的 0.20.0 實際判定

classify_risk.py 將 prompt casefold 後按 routing-rules.json 做子字串搜尋。實際順序為 R3、R2、R0，未命中才採預設 R1；R1 沒有獨立詞表。若命中僅學習筆記等排除詞、沒有工程詞，則 out_of_scope。這不是根據影響量化打分，也不理解否定或完整詞界。

- R0：導讀、解釋程式、資料流、呼叫流程、read-only 等，要求 explain-code-flow。
- R1：未命中其他類別的預設一般變更，要求 tdd/code-review。
- R2：module、port、event、architecture、refactor、schema、型別、狀態、依賴、演算法等，要求方案與架構治理。
- R3：hardware、firmware、transport、timing、deadline、thread、boot、ISR/DMA、韌體、硬體、中斷、時序等，要求方案、架構及 validate-on-device。

本回合只讀呼叫 production classifier 已重現：導讀資料流→R0；修正加總結果→R1；refactor module→R2；修改韌體中斷時序→R3。「不修改硬體，只整理文件」仍→R3；write report 因含 port→R2。這些是目前限制，未在本回合修正分類器。

ask-matt 定義自動入口與流程規則；engineering-risk-routing 擁有分類器及 guided_workflow_router.py。前者呼叫後者，後者整合意圖、ProjectState、SPEC、風險與能力後提供最終 selected_skill。風險 classify 的 next_skill 只是建議，不能當成整體路由結果。

### SPEC-0057 的確切範圍與限制

已記錄五階段文件流程、可保存不完整草稿、既有正式文件先保存候選、內容確認後可套用正式文件、不需要實作「開始執行」、相關文件集合與生成 manifest/圖表/索引一致套用、保留並行基底与恢復檢查、修正技能指令/文件工具/說明及測試。文件確認不產生實作 receipt。當時包含路由/hook 相關權限入口的調整，並非移除 hooks。

SPEC-0057 r5 宣稱當時工作區維修完成，且明示安裝套件未更新、owner CLI/完整 release 並未通過。它不是目前分支已整合的證明。舊報告記錄核心37 tests全過、討論入口56/57、文件/架構集合33/40，8項既有 adapter 缺口不能算PASS。目前引用的部分共用文件缺失，需重新核對其來源與提交。

### 測試修正：完整模組契約、測試案例與執行環境

來源 user:20261014:module-testing-annotation-1 明確指出目的：程式已模組化，應用整個模組的函式進行測試，而不是只補 SIL/HIL 名称。Annotation 2 詢問文件為何需要SIL；Annotation 3 詢問驗證層選擇及SIL是否軟體測試階段；Annotation 4 要求SIL/PIL/HIL全名。這些內容在本修訂全部保留與回答。

先前把文件保存、確認或流程回歸直接命名為SIL不精確。文件內容本身應做格式、schema、引用、完整性、一致性與生成視圖比對；若測試的是寫文件的軟體，應按其模組的公開契約執行一般模組/整合測試。只有具備正式受測軟體及模擬外部環境的在迴路組成，才採用SIL標記。不因普通unit/integration test在host上執行，就自動改標為SIL。

模組契約定義測什麼；案例定義輸入、操作序列及預期結果；SIL/PIL/HIL定義受測對象與執行環境。它們可以排成逐步驗證階段，但不是產品功能項目，也不是必須每個模組全部跑一遍的固定清單。

| 名稱 | 全名與中文 | 正確含義 |
| --- | --- | --- |
| MIL | Model-in-the-Loop；模型在迴路 | 用模型及模擬環境驗證演算法；無模型的專案不強制引入 |
| SIL | Software-in-the-Loop；軟體在迴路 | 正式功能程式在host/虛擬環境運行，外部硬體/plant等以模型、Fake或Replay表示，驗證軟體行為 |
| PIL | Processor-in-the-Loop；處理器在迴路 | 目標編譯的正式程式在目標處理器執行，由測試環境提供輸入並取得輸出，檢查目標行為/數值一致性及適用成本 |
| HIL | Hardware-in-the-Loop；硬體在迴路 | 實際控制器/硬體與即時模擬環境透過真實I/O互動，驗證硬體/軟體整合和時序。普通實機測試不必然等於HIL |

來源：https://www.mathworks.com/discovery/hardware-in-the-loop-hil.html 、https://www.mathworks.com/help/ecoder/software-in-the-loop-sil-simulation.html 、https://www.mathworks.com/help/ecoder/processor-in-the-loop.html 。文件與軟體工作流的測試分類為本方案修正，不是這些來源宣称本外掛需要SIL。

### 建議的模組測試契約

對每個受影響模組：

1. 列出全部受影響公開commands、queries、events及其合法呼叫/生命週期順序，使用該模組正式實作，不以內部helper當主要測試邊界。
2. 以需求、獨立已知向量或已驗證参考模型作為預期結果；不照抄受測演算法計算expected。
3. 測正常輸入/輸出、單位/範圍、邊界輸入、狀態轉移、事件順序、錯誤/timeout/overflow、reset與恢復；只有契約涉及時才加入backlog、throughput、latency及其他資源門檻。
4. 替換模組外部的依賴Port，捕捉正式模組的結果與輸出事件；不mock掉受測模組內部演算法、狀態機或處理步驟。私有helper測試不能替代完整模組行為測試。
5. 跨模組Flow另做整合測試，驗證父層協調、資料/事件順序、拒絕及錯誤傳遞；單一模組通過不能代替整體流程證據。
6. 同一組可重用輸入、操作序列與預期結果盡可能跨環境重用；SIL/PIL/HIL的執行adapter、證據及時間門檻依平台補充，不重寫一套受測邏輯。
7. 每項案例連到Module ID、public interface、REQ/AC、fixture、執行方法、預期/實際結果與證據。完整模組表示正式實作整體運行，不表示每個案例都要调用所有公開函式。

### 修訂後驗證矩陣

| 測試範圍 | 測試項目 | 執行與適用性 |
| --- | --- | --- |
| 單一模組契約 | 正常/邊界I/O、完整生命週期、可觀察狀態與事件、錯誤/reset/recovery | 用完整正式模組和公開介面執行；所有受影響模組均按契約規劃 |
| 模組整合/Flow | 父層協調、Port資料傳遞、事件順序、錯誤傳播 | 組合正式模組，只有系統外部依賴模擬 |
| Adapter Contract | Fake/Replay與真實adapter遵守相同Port語義 | 重用相同契約案例，adapter專用案例只能補充 |
| SIL | 模組/流程在模擬外部環境下的功能行為 | 軟體在迴路適用時採用，不能僅因host執行而選用 |
| PIL | 正式目標程式行為、數值一致性及適用資源成本 | 需要目標處理器證據時採用，不替代整合環境的deadline證據 |
| HIL | 真實控制器I/O、即時模擬環境互動、干擾/故障/時序 | 硬體在迴路適用時採用，設定專案確認的target/plant/profile/threshold |
| System/Soak | 端到端行為、負載、長時間穩定性與恢復 | 按產品需求規劃；不强制每个模組跑所有階段 |
| 文件檢查 | 格式、schema、引用、內容一致性、來源/生成視圖比對 | 文件檢查；不是SIL、PIL或HIL |

在本外掛方案中，文件owner、router、delivery等程式可用模組契約與軟體整合案例驗證；檢查hooks是否移除屬manifest/分發與工作流回歸。它們不再以「文件SIL」為測項名稱。verification-ladder.py若本身需測，應測其公開plan/validate/assess等功能的完整行為；這不是產品的SIL階段。0.20.0既有matrix與實作仍未修改，本文件仅记录候選修正。

修訂候選驗收：AC-010受影響模組均有公開介面與正式實作的完整行為案例；AC-011每案記錄模組、REQ/AC、輸入、呼叫序列、預期、環境與證據；AC-012不以零碎helper、mock內部邏輯或簡化重寫模型替代正式模組測試；AC-013文件檢查與軟體行為測試不自動標為SIL；AC-014按專案適用性安排模組、整合、Adapter Contract、SIL/PIL/HIL與System/Soak；AC-015保留已決定的hooks移除及文件/實作授權分離。本回合只修正方案文件，未新增測試程式、未執行SIL/PIL/HIL、未修改安裝版。

## ESP32 實際案例：測試已執行但 SIL 被排除

來源使用者：「程式修改後只有主機回歸、ESP32建置、Web與完整AST/架構檢查均通過，沒有進行SIL」。使用者提供 codex://threads/01a13947-9b6b-7301-a80e-66688bcba1b9（整理規格章節格式），並澄清SIL可以藉由正式模組公開介面進行測試。該聊天指向 codex://threads/01a138a5-c950-7033-bdc4-537ad590bdc5（排查模型匯入逾時）及專案 C:/Users/hugo_peng/firmware/periphery/env_sensing。本回合僅讀取該專案，未修改或執行其測試/韌體/裝置。

### 已查明的事實

1. validation/verification-ladder.yaml 的 spec0092-host 規則只選 module-contract；layers 沒有sil定義，not_applicable 明列sil，理由為「No separate simulated integration claim; production-seam host tests cover this feature.」。因此驗證計畫不會列SIL，完成檢查也不會要求本次SIL證據。
2. tests/modules/model_storage/run_spec0092_host.py 以g++編譯正式model_catalog、firmware_system/runtime、modules、application及model_json程式，並實際執行model-catalog和model-runtime的九種模式；不是僅跑建置或重寫一份簡化演算法。
3. model_catalog_test.cpp 透過ModelCatalog公開介面測匯入、串流、同名拒絕、確認/取消、I/O故障與恢復；MemoryIo實作外部ModelArtifactIoPort，正式內部邏輯仍執行。
4. model_runtime_test.cpp 使用正式FirmwareSystemRuntime公開入口，Fake Physical/Transport及受控時鐘/condition-variable gates，驗證匯入生命週期、取消/timeout/reset式恢復、configuration保留及長操作下progress查詢。
5. 保存的 artifacts/tests/0930b57f495c4965983385f193d7474c/manifest.json outcome=PASS；10-import-progress.txt 實際記錄PASS progress query under blocked validation, commit and IMU restore; completed/new job coherence。兩個測試cpp和model_catalog.cpp、firmware_system_runtime.cpp目前SHA256皆與该run記錄一致。
6. spec-governance/spec0092-delivery-summary.md 已明示整體驗收未完成，尚未實機操作，情境映射及歷史layout仍有缺口。因此沒有證據顯示該聊天把整體SPEC/HIL標為完成。

依DEC-003，本案例的部分主機測試符合使用者要求的模組SIL執行方式。不能再說完全沒有跑正式模組功能測試。實際缺口是測試分類/適用性、AC→模組→案例的明確覆蓋報告，以及報告只寫「主機回歸」；不能據此推定每個受影響模組與所有契約均已充分覆蓋。

### 0.20.0 工具機制的已重現限制

對正式verification_ladder.plan函式提供記憶體fixture，layers.sil存在且module-contract.next_layers含sil，但從matched rules.layers移除sil後，planner仍PASS且required_layers只有module-contract。host-semantics單項authority也只要求module-contract。next_layers是描述資料，不會自動執行下一層；planner/assessor不會代替專案runner執行測試。此探測不是執行產品SIL，也不是認定planner違反現有契約。

### 候選修改與驗收

- 移除「沒有獨立模擬整合claim所以SIL不適用」的分類理由；依實際正式模組/harness組成認定模組SIL。保留普通文件檢查、純建置、AST與web打包的獨立類別。
- 功能/狀態/流程變更先盤點受影響Module和public interface，再映射AC到正式模組案例及host/SIL runner命令。缺harness、案例或介面映射是待補的測試缺口，不當作任意不適用理由。
- 儘可能重用已確認正式實作与外部Fake的現有主機案例，不要求另寫重复測試。新計畫/新run明確登錄SIL組成與對應AC；歷史run/manifest保留原樣，不直接改標為新SIL PASS或假稱重跑。
- 實作流程需真正執行對應runner，記錄Module、公開操作、fixture、production-source hash、command/exit、預期/實際輸出、覆蓋及證據。完成檢查必須核對已選Module/SIL案例，缺证据时不宣稱功能驗證完成；既有建置/AST通過仍如實保留。
- 最終報告分列完整模組/SIL功能、整合/adapter、ESP32建置、Web、AST/架構及適用的PIL/HIL/System，不能只寫一個主機回歸PASS讓使用者無法辨識。
- 候選反例測試：matched rule漏sil、存在未使用的next_layers、功能模組漏案例、只有build/AST、過期production source hash、單純將host標籤改SIL但無實際模組組成、缺少指定runner結果。應被計畫/完成检查按各自責任拒絕，不能用降低其他硬體驗收門檻解決。

### 案例來源

- [專案matrix](C:/Users/hugo_peng/firmware/periphery/env_sensing/validation/verification-ladder.yaml:160)
- [SIL不適用理由](C:/Users/hugo_peng/firmware/periphery/env_sensing/validation/verification-ladder.yaml:212)
- [正式來源host runner](C:/Users/hugo_peng/firmware/periphery/env_sensing/tests/modules/model_storage/run_spec0092_host.py:32)
- [模組契約案例](C:/Users/hugo_peng/firmware/periphery/env_sensing/tests/modules/model_storage/model_catalog_test.cpp:139)
- [正式runtime案例](C:/Users/hugo_peng/firmware/periphery/env_sensing/tests/modules/model_storage/model_runtime_test.cpp:263)
- [保存的執行證據](C:/Users/hugo_peng/firmware/periphery/env_sensing/artifacts/tests/0930b57f495c4965983385f193d7474c/manifest.json)
- [執行報告及驗收限制](C:/Users/hugo_peng/firmware/periphery/env_sensing/spec-governance/spec0092-delivery-summary.md)

## 本回合採用與說明

Annotation 1和4已明確「採用」，分別記錄為DEC-004與DEC-005。這些測試原則與報告行為不再是未採用選項，不重新詢問；剩餘具體工具改動、測試接線與分發範圍仍需依目前working方案整理。文件保存、採用及實作「開始執行」授權保持獨立。

### 主機回歸的意義

主機（host）是開發電腦，相對於目標ESP32。回歸是修改後重跑既有案例，確認原有功能未被改壞。因此「主機回歸」描述在哪裡/為何重跑，不指定是哪種測試。它可以包含模組契約、符合已採用定義的模組SIL、跨模組整合、adapter或Web測試。主機回歸名稱本身不能證明SIL組成或所有模組已覆蓋。報告應列出實際模組/公開介面/測試項目及結果，避免以一個籠統PASS遮蔽。

### 兩個程式元件

- ModelCatalog：位於src/modules/model_storage的模型儲存/匯入元件。公開Begin、Append、Finish、Cancel、Recover、Progress等函式；管理staging、名稱衝突、提交/取消/恢復。儲存與JSON檢查經外部Ports注入，測試可以Fake這些依賴而保持正式邏輯。
- FirmwareSystemRuntime：位於src/bootstrap/firmware_system_runtime.cpp的正式韌體執行組裝與協調實作，實作FirmwareSystemRuntimePort及ModelManagementFlowPort，內含ModelCatalog並整合configuration、sensor、transport及operation協調。對外由CreateFirmwareSystemRuntime建立並提供Models、Configurations、SystemFlows等介面；模型匯入串起停止/排空傳輸、存模型、恢復及進度查詢。它不是單純測試程式，也不是所有功能的一個平面模組，測它可涵蓋多個模組協調。

來源：[ModelCatalog公開介面](C:/Users/hugo_peng/firmware/periphery/env_sensing/src/modules/model_storage/model_catalog.h:80)、[FirmwareSystemRuntime實作](C:/Users/hugo_peng/firmware/periphery/env_sensing/src/bootstrap/firmware_system_runtime.cpp:310)、[Runtime公開Port](C:/Users/hugo_peng/firmware/periphery/env_sensing/src/bootstrap/firmware_system_runtime.h:151)。

### 階段與必要結果

主機模組/SIL與整合驗證 → 建置對應目標映像 → 在適用授權下燒錄/啟動並核對image → 執行已定義的PIL/HIL案例 → 依需求System/Soak。PIL/HIL可在建置和燒錄後執行，但不能只因裝置已開機就算執行或PASS。需從專案契約取得測試輸入、可觀察輸出、門檻、harness/外部模擬、設備條件、timeout與停止條件；通過條件及結果分別記錄。未預先假定ESP32的時序/負載門檻，也未將本訊息當作立即燒錄許可。

補充驗收要求：最終報告將建置、燒錄、PIL、HIL分列，標明已執行/未執行/不適用與來源理由；成功建置/成功燒錄只代表準備步驟，不替代模組功能、目標成本或硬體整合證據。對無目標處理器或硬體在迴路需求的專案，不新增無根據的PIL/HIL。

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

- user:20261014:提出修改方案: 提出文件撰寫不需開始執行、實作才需開始執行的修改方案；本回合只調查與撰寫候選方案。
- assistant:20261014:authorization-boundary-proposal: User principle: only implementation needs 開始執行. Candidate proposal, source evidence, alternatives and expected validation saved in SPEC-0061 r1. Historical SPEC-0057 does not supply current authority or current PASS. No active skill, program, hook, test, config, install or publication modified.
- assistant:20261014:authorization-boundary-proposal: User principle and candidate proposal saved in SPEC-0061 r2. The empty open-decision marker was normalized without changing adopted scope. No implementation or installation is performed. Expected validation only; no runtime PASS is claimed.
- user:20261014:annotations-sil-hil: Annotations: remove lifecycle hooks; confirm R0-R3 determination, SPEC-0057 scope, upstream SIL/HIL, and ask-matt/risk-routing roles. Main request: SIL/HIL test items were missing.
- assistant:20261014:annotations-sil-hil-response: 上一版漏列 SIL/HIL，現已補入 SPEC-0061 r3 working 草稿。hooks 移除已記錄 DEC-001，尚未變更安裝版。R0-R3 是 keyword substring classifier，已重現否定與 report/port 誤判。SPEC-0057、上游測試與 router 分工均已核對。沒有執行 SIL/HIL 或取得實作授權。
- user:20261014:module-testing-annotations: User clarifies that testing must exercise complete modular production functions through public interfaces; asks why documents need SIL, what verification-layer selection means, and SIL/PIL/HIL expansions.
- assistant:20261014:whole-module-testing-response: 我之前分類不準確。以完整模組正式實作與公開介面測試行為，模擬外部依賴而保留內部邏輯；文件不需SIL。SIL/PIL/HIL是軟體/處理器/硬體在迴路，可作驗證階段，不是功能測項。SPEC-0061 r4 working已保存，未取得實作授權。
- user:20261014:reported-no-sil: User reports host regression/ESP32 build/Web/AST PASS but no SIL, supplies the referenced Codex chat, and clarifies that SIL should test production modules through public interfaces.
- assistant:20261014:verified-esp32-module-sil: 已核對你的ESP32案例：正式模組公開介面主機測試確實執行，matrix卻把sil列不適用，報告只寫host regression。依你的技能定義可認定部分模組SIL；不能宣稱所有模組已覆蓋。SPEC-0061 r5 working保存了來源、DEC-003及分類/映射/報告修正候選；沒有改ESP32或歷史證據，未取得實作授權。
- user:20261014:module-test-policy-adoptions: Annotations 1 and 4 adopt the whole-module testing policy and mapping/execution/report requirements. Annotation 2 asks host regression meaning, 3 asks ModelCatalog/FirmwareSystemRuntime roles, and 5 states PIL/HIL follow build and flashing.
- assistant:20261014:adopted-module-test-policy: 兩項採用已保存為DEC-004/005，建置燒錄後PIL/HIL序列為DEC-006。主機回歸是開發電腦上變更後重跑已有測試，可能包括模組SIL。ModelCatalog管理模型匯入儲存；FirmwareSystemRuntime組裝協調正式韌體服務。SPEC-0061 r6 working，未取得實作授權，僅文件保存。
- user:20261014:discussion-readiness-review: 還有需要討論的地方?
- assistant:20261014:discussion-readiness-review: 目前沒有需要你再決定的核心問題。文件不需實作授權、移除hooks、完整模組公開介面測試、模組SIL與實際案例/證據及分項報告、建置燒錄後依需求PIL/HIL都已有決定。剩下是整理具體修改範圍與驗收清單；R0-R3誤判修正未被採用，不擴張本次範圍。SPEC-0061 r6 working，尚未取得實作授權。
- user:20261014:reload-installed-0220: 重新讀取0.22.0技能；本回合僅重新讀取與檢查，先前修改暫停仍有效。

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"69909a2168d0a515842007bdb8574727bc5ed8ce1d9f6c0709c58ed0b78b1d5a","event_type":"start","event_version":1,"open_decisions":["None. 候選方案待使用者審閱；不藉保存文件推定採用。"],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-10-14T08:27:11.493858+00:00","relationships":[],"revision":1,"snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","verdict":"BLOCKED","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"提出文件撰寫不需開始執行、實作才需開始執行的修改方案；本回合只調查與撰寫候選方案。","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:提出修改方案","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"authorization-boundary-proposal-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"8bd3693ed397d25c53f19bdf5dd8ed9e7b68015364ad4967f49a94b6f60c6e40","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"69909a2168d0a515842007bdb8574727bc5ed8ce1d9f6c0709c58ed0b78b1d5a","previous_snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","recorded_at":"2026-10-14T08:30:46.692551+00:00","relationships":[],"revision":1,"snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":1,"snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"2986c855ec6ec2f794936de2f884ce22784c6fd339fc6aec710f0900ed0292fc","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:提出修改方案"],"source_ref":"assistant:20261014:authorization-boundary-proposal","summary":"User principle: only implementation needs 開始執行. Candidate proposal, source evidence, alternatives and expected validation saved in SPEC-0061 r1. Historical SPEC-0057 does not supply current authority or current PASS. No active skill, program, hook, test, config, install or publication modified.","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"authorization-boundary-proposal-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"66222504ff0020a0c295535be53d4814ea3b2b680bc5d471c27ebc42155e985b","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"8bd3693ed397d25c53f19bdf5dd8ed9e7b68015364ad4967f49a94b6f60c6e40","previous_snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","recorded_at":"2026-10-14T08:31:18.216306+00:00","relationships":[],"revision":1,"snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"d4fa82ec5148a77f6287b3ff3a109c5d72303e2d6214933df1517497e5c733e9","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"66222504ff0020a0c295535be53d4814ea3b2b680bc5d471c27ebc42155e985b","previous_snapshot_hash":"471b33b8e2074258ad87604fddcd59354d5df5088a6568386678e9f1ed79cd73","recorded_at":"2026-10-14T08:33:18.615839+00:00","relationships":[],"revision":2,"snapshot_hash":"b3050589331344551b31a60edb24ed399c13f63df1595d8018b4791008744e83","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":2,"snapshot_hash":"b3050589331344551b31a60edb24ed399c13f63df1595d8018b4791008744e83","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"8918a6cc6bc984556fbacd8ed5c2f101b0b8b2382df350603ff88efc0ed36a46","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:提出修改方案"],"source_ref":"assistant:20261014:authorization-boundary-proposal","summary":"User principle and candidate proposal saved in SPEC-0061 r2. The empty open-decision marker was normalized without changing adopted scope. No implementation or installation is performed. Expected validation only; no runtime PASS is claimed.","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"authorization-boundary-proposal-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"4802bc946b11d7c50e789424ea6eb0ac7f25b89a8b2e38a7e4806db055b9f4db","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"d4fa82ec5148a77f6287b3ff3a109c5d72303e2d6214933df1517497e5c733e9","previous_snapshot_hash":"b3050589331344551b31a60edb24ed399c13f63df1595d8018b4791008744e83","recorded_at":"2026-10-14T08:33:43.761814+00:00","relationships":[],"revision":2,"snapshot_hash":"b3050589331344551b31a60edb24ed399c13f63df1595d8018b4791008744e83","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":["DEC-001"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-001"],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"a5ad3e39f3ed841ffe692d2c5f1af5d8b3bb34e7fe0e342ec6784273b14f1b61","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"4802bc946b11d7c50e789424ea6eb0ac7f25b89a8b2e38a7e4806db055b9f4db","previous_snapshot_hash":"b3050589331344551b31a60edb24ed399c13f63df1595d8018b4791008744e83","recorded_at":"2026-10-14T08:39:55.630094+00:00","relationships":[],"revision":3,"snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"Annotations: remove lifecycle hooks; confirm R0-R3 determination, SPEC-0057 scope, upstream SIL/HIL, and ask-matt/risk-routing roles. Main request: SIL/HIL test items were missing.","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:annotations-sil-hil","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"annotations-sil-hil-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"8b836d9450bb812d30b8baf5f8c65ad9ede00d159b4fe649c4dafaac217013be","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"a5ad3e39f3ed841ffe692d2c5f1af5d8b3bb34e7fe0e342ec6784273b14f1b61","previous_snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","recorded_at":"2026-10-14T08:41:51.580576+00:00","relationships":[],"revision":3,"snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":3,"snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{"hook-removal":{"id":"hook-removal","kind":"accepted","source_ref":"user:20261014:annotation-1","text":"移除生命週期 hooks；不以此推定程式或安裝實作授權。"},"risk-question":{"id":"risk-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 R0–R3 判定；已核對 production keyword classifier，記錄否定和子字串誤判。"},"router-roles":{"id":"router-roles","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"ask-matt 定義入口/流程；risk-routing 擁有 classifier 與 guided router，risk next_skill 不是最終 selected_skill。"},"sil-hil-plan":{"id":"sil-hil-plan","kind":"candidate","source_ref":"user:20261014:annotations-sil-hil","text":"補充正式實作 SIL 分流/生命週期/無hook/驗證層規劃測試、真實宿主整合及硬體 HIL 項目與適用性。"},"spec57-question":{"id":"spec57-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 SPEC-0057 修改範圍；已引用其 r5 與範圍限制，未繼承歷史授權或驗證。"},"upstream-layers":{"id":"upstream-layers","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"已核對 pinned upstream tdd/implement 無明確 SIL/HIL 層級；專案現有 matrix 有 SIL，HIL 明列不適用。"}},"item_bindings":{"hook-removal":["DEC-001"],"risk-question":[],"router-roles":[],"sil-hil-plan":[],"spec57-question":[],"upstream-layers":[]},"kind":"saved","reply_sha256":"e7aec39fae633607ca876361178d2c777be95aaeb891f386d5e59caaf9bc3cb2","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:annotation-1","user:20261014:annotations-sil-hil","user:20261014:提出修改方案"],"source_ref":"assistant:20261014:annotations-sil-hil-response","summary":"上一版漏列 SIL/HIL，現已補入 SPEC-0061 r3 working 草稿。hooks 移除已記錄 DEC-001，尚未變更安裝版。R0-R3 是 keyword substring classifier，已重現否定與 report/port 誤判。SPEC-0057、上游測試與 router 分工均已核對。沒有執行 SIL/HIL 或取得實作授權。","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"annotations-sil-hil-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"0fe642b80ad03a2107707462b28830937b9b5c08f2ce2d5d9601d24350b232b6","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"8b836d9450bb812d30b8baf5f8c65ad9ede00d159b4fe649c4dafaac217013be","previous_snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","recorded_at":"2026-10-14T08:41:52.741832+00:00","relationships":[],"revision":3,"snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":["DEC-002"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-002"],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"f4e35d81e3e94bbb2a1dcaf9453c51548d423b5e5a2c23eddc0c6c4eeaa0bf0b","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"0fe642b80ad03a2107707462b28830937b9b5c08f2ce2d5d9601d24350b232b6","previous_snapshot_hash":"69594bebc8ce6f886001c501b3fc110c19a746e3654cd4bf14feca3c35958b80","recorded_at":"2026-10-14T08:57:21.895280+00:00","relationships":[],"revision":4,"snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"User clarifies that testing must exercise complete modular production functions through public interfaces; asks why documents need SIL, what verification-layer selection means, and SIL/PIL/HIL expansions.","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:module-testing-annotations","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"whole-module-testing-annotations-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"092cab5132637f55c829c773efd4ba0217329d3d77f03d5fd5f31d9626276df1","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"f4e35d81e3e94bbb2a1dcaf9453c51548d423b5e5a2c23eddc0c6c4eeaa0bf0b","previous_snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","recorded_at":"2026-10-14T08:58:19.102190+00:00","relationships":[],"revision":4,"snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":4,"snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{"acronyms":{"id":"acronyms","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"已查MathWorks官方文件確認Software/Processor/Hardware-in-the-Loop及HIL實體控制器與即時模擬環境互動定義。"},"document-sil-correction":{"id":"document-sil-correction","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"文件本身做格式/引用/內容一致性檢查，不需SIL；寫文件的軟體按模組行为測試，不自動標SIL。"},"hook-removal":{"id":"hook-removal","kind":"accepted","source_ref":"user:20261014:annotation-1","text":"移除生命週期 hooks；不以此推定程式或安裝實作授權。"},"layer-meaning":{"id":"layer-meaning","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"SIL/PIL/HIL可排為階段，定義執行環境和受測對象；模組契約定義測什麼，案例定義輸入/操作/expected。"},"risk-question":{"id":"risk-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 R0–R3 判定；已核對 production keyword classifier，記錄否定和子字串誤判。"},"router-roles":{"id":"router-roles","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"ask-matt 定義入口/流程；risk-routing 擁有 classifier 與 guided router，risk next_skill 不是最終 selected_skill。"},"sil-hil-plan":{"id":"sil-hil-plan","kind":"candidate","source_ref":"user:20261014:annotations-sil-hil","text":"補充正式實作 SIL 分流/生命週期/無hook/驗證層規劃測試、真實宿主整合及硬體 HIL 項目與適用性。"},"spec57-question":{"id":"spec57-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 SPEC-0057 修改範圍；已引用其 r5 與範圍限制，未繼承歷史授權或驗證。"},"upstream-layers":{"id":"upstream-layers","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"已核對 pinned upstream tdd/implement 無明確 SIL/HIL 層級；專案現有 matrix 有 SIL，HIL 明列不適用。"},"whole-module-principle":{"id":"whole-module-principle","kind":"accepted","source_ref":"user:20261014:module-testing-annotation-1","text":"測試以完整模組正式實作的公開函式/事件為邊界，而非只補SIL/HIL標籤或零碎helper。"}},"item_bindings":{"acronyms":[],"document-sil-correction":[],"hook-removal":["DEC-001"],"layer-meaning":[],"risk-question":[],"router-roles":[],"sil-hil-plan":[],"spec57-question":[],"upstream-layers":[],"whole-module-principle":["DEC-002"]},"kind":"saved","reply_sha256":"aab241b347b4c5df903f528201ff904d0efcf71f5fb06bab1ee12b3909a55584","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:annotations-sil-hil","user:20261014:module-testing-annotation-1","user:20261014:module-testing-annotations","user:20261014:提出修改方案"],"source_ref":"assistant:20261014:whole-module-testing-response","summary":"我之前分類不準確。以完整模組正式實作與公開介面測試行為，模擬外部依賴而保留內部邏輯；文件不需SIL。SIL/PIL/HIL是軟體/處理器/硬體在迴路，可作驗證階段，不是功能測項。SPEC-0061 r4 working已保存，未取得實作授權。","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"whole-module-testing-annotations-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"8dea1455017ab2d86aac0cb3a0487937e5558a42bea30c5e20238a870951fe13","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"092cab5132637f55c829c773efd4ba0217329d3d77f03d5fd5f31d9626276df1","previous_snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","recorded_at":"2026-10-14T08:58:59.439690+00:00","relationships":[],"revision":4,"snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":["DEC-003"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-003"],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"aa759ad1b4559b3cbc6321b2f180d61c638b8b0c5e3a0a55f1e199184895d86b","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"8dea1455017ab2d86aac0cb3a0487937e5558a42bea30c5e20238a870951fe13","previous_snapshot_hash":"28346ad00a0dd480625a9a2cb935af575844bde35cf644f87f23fe40efc990f4","recorded_at":"2026-10-14T09:06:58.109845+00:00","relationships":[],"revision":5,"snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"User reports host regression/ESP32 build/Web/AST PASS but no SIL, supplies the referenced Codex chat, and clarifies that SIL should test production modules through public interfaces.","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:reported-no-sil","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"verified-esp32-module-sil-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"ed936eec01ce700237a35eaac26e1925cc1cdf7f7d9b8f49ea64aa88f229a03a","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"aa759ad1b4559b3cbc6321b2f180d61c638b8b0c5e3a0a55f1e199184895d86b","previous_snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","recorded_at":"2026-10-14T09:08:04.024697+00:00","relationships":[],"revision":5,"snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":5,"snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{"acronyms":{"id":"acronyms","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"已查MathWorks官方文件確認Software/Processor/Hardware-in-the-Loop及HIL實體控制器與即時模擬環境互動定義。"},"actual-acceptance-incomplete":{"id":"actual-acceptance-incomplete","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"原執行報告保留實機、情境映射及歷史layout缺口，並未把SPEC標為implemented。"},"actual-matrix-excludes-sil":{"id":"actual-matrix-excludes-sil","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"SPEC-0092 host rule只選module-contract，sil被not_applicable明確排除，理由production-seam host tests已涵蓋且無separate simulated integration claim。"},"actual-production-modules-tested":{"id":"actual-production-modules-tested","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"Host runner編譯正式model_catalog與firmware_system/runtime，測試呼叫公開接口並模擬外部依賴；保存run PASS且四份相關source hash與現檔一致。不能宣稱所有模組/所有AC已充分覆蓋。"},"document-sil-correction":{"id":"document-sil-correction","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"文件本身做格式/引用/內容一致性檢查，不需SIL；寫文件的軟體按模組行为測試，不自動標SIL。"},"hook-removal":{"id":"hook-removal","kind":"accepted","source_ref":"user:20261014:annotation-1","text":"移除生命週期 hooks；不以此推定程式或安裝實作授權。"},"layer-meaning":{"id":"layer-meaning","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"SIL/PIL/HIL可排為階段，定義執行環境和受測對象；模組契約定義測什麼，案例定義輸入/操作/expected。"},"module-sil-definition":{"id":"module-sil-definition","kind":"accepted","source_ref":"user:20261014:sil-public-interface-answer","text":"透過正式模組公開介面在主機進行功能測試；外部依賴可Fake/Replay，不需要另有獨立模擬整合claim才認定。"},"risk-question":{"id":"risk-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 R0–R3 判定；已核對 production keyword classifier，記錄否定和子字串誤判。"},"router-roles":{"id":"router-roles","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"ask-matt 定義入口/流程；risk-routing 擁有 classifier 與 guided router，risk next_skill 不是最終 selected_skill。"},"sil-hil-plan":{"id":"sil-hil-plan","kind":"candidate","source_ref":"user:20261014:annotations-sil-hil","text":"補充正式實作 SIL 分流/生命週期/無hook/驗證層規劃測試、真實宿主整合及硬體 HIL 項目與適用性。"},"sil-planning-report-repair":{"id":"sil-planning-report-repair","kind":"candidate","source_ref":"user:20261014:reported-no-sil","text":"依實際正式模組組成認定/reuse host SIL案例，修正matrix和Module/AC映射，要求runner結果及明確覆蓋報告；保留歷史run原貌，不直接改標或假稱重跑。"},"spec57-question":{"id":"spec57-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 SPEC-0057 修改範圍；已引用其 r5 與範圍限制，未繼承歷史授權或驗證。"},"upstream-layers":{"id":"upstream-layers","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"已核對 pinned upstream tdd/implement 無明確 SIL/HIL 層級；專案現有 matrix 有 SIL，HIL 明列不適用。"},"whole-module-principle":{"id":"whole-module-principle","kind":"accepted","source_ref":"user:20261014:module-testing-annotation-1","text":"測試以完整模組正式實作的公開函式/事件為邊界，而非只補SIL/HIL標籤或零碎helper。"}},"item_bindings":{"acronyms":[],"actual-acceptance-incomplete":[],"actual-matrix-excludes-sil":[],"actual-production-modules-tested":[],"document-sil-correction":[],"hook-removal":["DEC-001"],"layer-meaning":[],"module-sil-definition":["DEC-003"],"risk-question":[],"router-roles":[],"sil-hil-plan":[],"sil-planning-report-repair":[],"spec57-question":[],"upstream-layers":[],"whole-module-principle":["DEC-002"]},"kind":"saved","reply_sha256":"c17ed3807172e2fb2835bb1a4d4c32520a94cb13d85be0b5adcabec96464df63","reply_stage":"prepared-until-host-stop","reviewed_sources":["source:env_sensing:verification-ladder-and-host-evidence","user:20261014:annotations-sil-hil","user:20261014:module-testing-annotations","user:20261014:reported-no-sil","user:20261014:sil-public-interface-answer","user:20261014:提出修改方案"],"source_ref":"assistant:20261014:verified-esp32-module-sil","summary":"已核對你的ESP32案例：正式模組公開介面主機測試確實執行，matrix卻把sil列不適用，報告只寫host regression。依你的技能定義可認定部分模組SIL；不能宣稱所有模組已覆蓋。SPEC-0061 r5 working保存了來源、DEC-003及分類/映射/報告修正候選；沒有改ESP32或歷史證據，未取得實作授權。","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"verified-esp32-module-sil-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"4d5a5374f938c5100b26ac7cb24d58fc7620e54b4804abd83e12a3eef77ad56b","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"ed936eec01ce700237a35eaac26e1925cc1cdf7f7d9b8f49ea64aa88f229a03a","previous_snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","recorded_at":"2026-10-14T09:08:04.832467+00:00","relationships":[],"revision":5,"snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":["DEC-004","DEC-005","DEC-006"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-004","DEC-005","DEC-006"],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"d897f5cad5f06232c1551538f40401aff708839336b1963e4bfd0f97933c3d86","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"4d5a5374f938c5100b26ac7cb24d58fc7620e54b4804abd83e12a3eef77ad56b","previous_snapshot_hash":"62a6919c2642ad71a31433ab3ca7b0d2f78dea0383ee4dfce6cbf7fddcdeb404","recorded_at":"2026-10-14T09:16:02.200860+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"Annotations 1 and 4 adopt the whole-module testing policy and mapping/execution/report requirements. Annotation 2 asks host regression meaning, 3 asks ModelCatalog/FirmwareSystemRuntime roles, and 5 states PIL/HIL follow build and flashing.","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:module-test-policy-adoptions","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"adopted-module-test-policy-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"93a584f352918b32c1b5705e34f66992baef59b4a6e32cfb26e1cb98c53a5582","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"d897f5cad5f06232c1551538f40401aff708839336b1963e4bfd0f97933c3d86","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T09:17:06.098143+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{"acronyms":{"id":"acronyms","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"已查MathWorks官方文件確認Software/Processor/Hardware-in-the-Loop及HIL實體控制器與即時模擬環境互動定義。"},"actual-acceptance-incomplete":{"id":"actual-acceptance-incomplete","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"原執行報告保留實機、情境映射及歷史layout缺口，並未把SPEC標為implemented。"},"actual-matrix-excludes-sil":{"id":"actual-matrix-excludes-sil","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"SPEC-0092 host rule只選module-contract，sil被not_applicable明確排除，理由production-seam host tests已涵蓋且無separate simulated integration claim。"},"actual-production-modules-tested":{"id":"actual-production-modules-tested","kind":"fact","source_ref":"source:env_sensing:verification-ladder-and-host-evidence","text":"Host runner編譯正式model_catalog與firmware_system/runtime，測試呼叫公開接口並模擬外部依賴；保存run PASS且四份相關source hash與現檔一致。不能宣稱所有模組/所有AC已充分覆蓋。"},"adopt-mapping-execution-report":{"id":"adopt-mapping-execution-report","kind":"accepted","source_ref":"user:20261014:module-policy-adopt-annotation-4","text":"採用模組/接口/案例盤點、實際SIL案例映射、真正執行與證據要求，以及分項完成報告。"},"adopt-whole-module-policy":{"id":"adopt-whole-module-policy","kind":"accepted","source_ref":"user:20261014:module-policy-adopt-annotation-1","text":"採用完整模組公開介面與正式實作測試、外部模擬、跨模組整合及依需求安排各測試類別。"},"document-sil-correction":{"id":"document-sil-correction","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"文件本身做格式/引用/內容一致性檢查，不需SIL；寫文件的軟體按模組行为測試，不自動標SIL。"},"hook-removal":{"id":"hook-removal","kind":"accepted","source_ref":"user:20261014:annotation-1","text":"移除生命週期 hooks；不以此推定程式或安裝實作授權。"},"host-regression-answer":{"id":"host-regression-answer","kind":"fact","source_ref":"user:20261014:module-test-policy-adoptions","text":"主機是開發電腦；回歸是變更後重跑已有案例。此名稱不單獨指定測試類別，可包含模組SIL、契約、整合、adapter或Web。"},"layer-meaning":{"id":"layer-meaning","kind":"fact","source_ref":"user:20261014:module-testing-annotations","text":"SIL/PIL/HIL可排為階段，定義執行環境和受測對象；模組契約定義測什麼，案例定義輸入/操作/expected。"},"module-sil-definition":{"id":"module-sil-definition","kind":"accepted","source_ref":"user:20261014:sil-public-interface-answer","text":"透過正式模組公開介面在主機進行功能測試；外部依賴可Fake/Replay，不需要另有獨立模擬整合claim才認定。"},"production-component-answer":{"id":"production-component-answer","kind":"fact","source_ref":"user:20261014:module-test-policy-adoptions","text":"已讀正式headers/cpp：ModelCatalog管理model storage/import；FirmwareSystemRuntime為bootstrap runtime組裝協調器，內含catalog並提供Models/Configurations/SystemFlows等公開Port。"},"risk-question":{"id":"risk-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 R0–R3 判定；已核對 production keyword classifier，記錄否定和子字串誤判。"},"router-roles":{"id":"router-roles","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"ask-matt 定義入口/流程；risk-routing 擁有 classifier 與 guided router，risk next_skill 不是最終 selected_skill。"},"sil-hil-plan":{"id":"sil-hil-plan","kind":"candidate","source_ref":"user:20261014:annotations-sil-hil","text":"補充正式實作 SIL 分流/生命週期/無hook/驗證層規劃測試、真實宿主整合及硬體 HIL 項目與適用性。"},"sil-planning-report-repair":{"id":"sil-planning-report-repair","kind":"candidate","source_ref":"user:20261014:reported-no-sil","text":"依實際正式模組組成認定/reuse host SIL案例，修正matrix和Module/AC映射，要求runner結果及明確覆蓋報告；保留歷史run原貌，不直接改標或假稱重跑。"},"spec57-question":{"id":"spec57-question","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"使用者要求確認 SPEC-0057 修改範圍；已引用其 r5 與範圍限制，未繼承歷史授權或驗證。"},"target-test-sequence":{"id":"target-test-sequence","kind":"accepted","source_ref":"user:20261014:module-policy-annotation-5","text":"建置與燒錄後具備裝置測試準備，依對應harness與條件執行PIL/HIL；本訊息未要求現在燒錄。"},"upstream-layers":{"id":"upstream-layers","kind":"fact","source_ref":"user:20261014:annotations-sil-hil","text":"已核對 pinned upstream tdd/implement 無明確 SIL/HIL 層級；專案現有 matrix 有 SIL，HIL 明列不適用。"},"whole-module-principle":{"id":"whole-module-principle","kind":"accepted","source_ref":"user:20261014:module-testing-annotation-1","text":"測試以完整模組正式實作的公開函式/事件為邊界，而非只補SIL/HIL標籤或零碎helper。"}},"item_bindings":{"acronyms":[],"actual-acceptance-incomplete":[],"actual-matrix-excludes-sil":[],"actual-production-modules-tested":[],"adopt-mapping-execution-report":["DEC-005"],"adopt-whole-module-policy":["DEC-004"],"document-sil-correction":[],"hook-removal":["DEC-001"],"host-regression-answer":[],"layer-meaning":[],"module-sil-definition":["DEC-003"],"production-component-answer":[],"risk-question":[],"router-roles":[],"sil-hil-plan":[],"sil-planning-report-repair":[],"spec57-question":[],"target-test-sequence":["DEC-006"],"upstream-layers":[],"whole-module-principle":["DEC-002"]},"kind":"saved","reply_sha256":"ca2d925445c0e00e2e1c56826a08e5d3c1a4837d221937b35a94cd99b59ddc09","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:annotations-sil-hil","user:20261014:module-policy-adopt-annotation-1","user:20261014:module-policy-adopt-annotation-4","user:20261014:module-policy-annotation-5","user:20261014:module-test-policy-adoptions","user:20261014:module-testing-annotations","user:20261014:reported-no-sil","user:20261014:提出修改方案"],"source_ref":"assistant:20261014:adopted-module-test-policy","summary":"兩項採用已保存為DEC-004/005，建置燒錄後PIL/HIL序列為DEC-006。主機回歸是開發電腦上變更後重跑已有測試，可能包括模組SIL。ModelCatalog管理模型匯入儲存；FirmwareSystemRuntime組裝協調正式韌體服務。SPEC-0061 r6 working，未取得實作授權，僅文件保存。","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"adopted-module-test-policy-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"7dbf8121f9f7a9146868a4ee185282960e36c8569b6f9100899d5ec69f99824b","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"93a584f352918b32c1b5705e34f66992baef59b4a6e32cfb26e1cb98c53a5582","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T09:17:06.897992+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"還有需要討論的地方?","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:discussion-readiness-review","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"discussion-readiness-review-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"18befa9c521ee94caf28afe138ca607b606abd6a89509579aec3df431934dc68","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"7dbf8121f9f7a9146868a4ee185282960e36c8569b6f9100899d5ec69f99824b","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T09:30:04.203885+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"4bf91e5a664d505e1c3d8c50f2306481e8022fbc45cd5022c70ce275571160a8","reply_stage":"prepared-until-host-stop","reviewed_sources":["user:20261014:discussion-readiness-review"],"source_ref":"assistant:20261014:discussion-readiness-review","summary":"目前沒有需要你再決定的核心問題。文件不需實作授權、移除hooks、完整模組公開介面測試、模組SIL與實際案例/證據及分項報告、建置燒錄後依需求PIL/HIL都已有決定。剩下是整理具體修改範圍與驗收清單；R0-R3誤判修正未被採用，不擴張本次範圍。SPEC-0061 r6 working，尚未取得實作授權。","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"discussion-readiness-review-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"71d74cb65d63c39560f99cd1fb82560527b3acf1b89a92ffe3eabcbfd9664f4d","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"18befa9c521ee94caf28afe138ca607b606abd6a89509579aec3df431934dc68","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T09:30:04.832992+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"重新讀取0.22.0技能；本回合僅重新讀取與檢查，先前修改暫停仍有效。","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"user:20261014:reload-installed-0220","task_ref":"01a13976-3449-7752-91a2-57fce7838927","turn_id":"reload-installed-0220-20261014"},"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"547e0d06af12a04c3fb364d2b604b138ac87ea0a089088deb558e480a32b294a","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"71d74cb65d63c39560f99cd1fb82560527b3acf1b89a92ffe3eabcbfd9664f4d","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T09:56:45.250297+00:00","relationships":[],"revision":6,"snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","REQ-001","REQ-002","REQ-003","REQ-004","REQ-005","REQ-006"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","REQ-001","REQ-002","REQ-003","REQ-004","REQ-005","REQ-006"],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"d500933537f0c60f8efcab97c50e06473a58163c4c6806179a1140e12a09a5cf","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"547e0d06af12a04c3fb364d2b604b138ac87ea0a089088deb558e480a32b294a","previous_snapshot_hash":"ad6892118d605d38c29cd294e089c8f307a32a7eccf79405fdae12a8f98a12f7","recorded_at":"2026-10-14T10:03:18.692484+00:00","relationships":[],"revision":7,"snapshot_hash":"d6953c9582982ee38f831e26acd1c0a900bf6c3213d99bd2d5b438866d642957","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"b4ebb9a03c07437486bcaca7c87c2d9f","event_hash":"01cfa173c0067e0a888801225edae3b62e5ba65f1fb0c10c426d6560c6ea7480","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"d500933537f0c60f8efcab97c50e06473a58163c4c6806179a1140e12a09a5cf","previous_snapshot_hash":"d6953c9582982ee38f831e26acd1c0a900bf6c3213d99bd2d5b438866d642957","recorded_at":"2026-10-14T10:03:19.036165+00:00","relationships":[],"revision":7,"snapshot_hash":"7cd1572209dd59702e00d947ed6f7c67bf54f3c90bece94aec319d5838b2061e","verdict":"PASS","working_id":"WORKING-SPEC-ad178d3c81df-doc-authoring-authorization-boundary"}
```
<!-- spec-audit:end -->
