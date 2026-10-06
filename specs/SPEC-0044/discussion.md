## Decisions
| ID | Decision |
|---|---|
| DEC-003 | 使用者提出並採用分檔引用方向；不採先前候選 A 的全部設計內嵌單一 SPEC，對應 REQ-003。 |
| DEC-004 | 採用設計文件生命週期方案 B：專案共用、持續演進，SPEC 引用確認版本；對應 REQ-004。 |
| DEC-005 | 採用候選版本管理方案 B，對應 REQ-005；檔案格式、轉換與版本檢查實作尚待確認。 |
| DEC-006 | 採用設計來源方案 A，分檔 Markdown 為來源、manifest 為產物；對應 REQ-006。 |
| DEC-007 | 採用已呈現的目錄分工，對應 REQ-007；舊檔遷移與多檔確認機制另行定義。 |
| DEC-008 | 採用整份變更一次確認、固定版本綁定，對應 REQ-008。 |
| DEC-009 | 採用討論階段寫入範圍，對應 REQ-009；保留正式修改的確認與執行授權要求。 |
| DEC-010 | 採用三階段檢查與分別處理失敗的方式，對應 REQ-010。 |
| DEC-011 | 採用設計欄位呈現方案 B，對應 REQ-011；兩種承載方式由格式規範固定，禁止同一欄位重複維護。 |
| DEC-012 | 採用多檔一致性與恢復要求，並依使用者補充確保流程可安全修復、局部繼續及明確解除阻擋，對應 REQ-012、REQ-013。 |
| DEC-013 | 依使用者更正，失敗處理以解決原因、驗證修復並完成原工作為目標；「可繼續」不能替代解決。修正 REQ-013、AC-013，保留 DEC-012 作原採用歷史。 |
| DEC-014 | 採用舊文件自動遷移、內容與來源保留、純格式授權延續、缺漏調查／衝突討論及統一新機制要求，對應 REQ-014、REQ-015。 |
| DEC-015 | 依使用者對整體方案確認問題回覆「可以有這兩個SPEC」，確認 SPEC-0043 與 SPEC-0044 各自的已呈現需求、決策、修改清單及驗收計畫；兩份保留分工。此為 SPEC 確認，不是開始執行授權。 |

## Discussion Context
REQ/DEC/AC-003 至 010 沿用 SPEC-0043 既有已採用決策與 ID；原始使用者回答及選項見 SPEC-0043 的 DISC-003 至 DISC-010。使用者對分工問題回覆「採用。OS與執行環境不需要有規範?」，授權拆分討論規格，未授權實作。
### DISC-011: Markdown 設計欄位格式
- **Situation:** 已採用分檔 Markdown 為設計來源，需定案工具讀取欄位的細部格式。
- **Question:** 分檔 Markdown 已選為設計來源；現在要決定工具讀取設計欄位的細部格式。下列三案都保留 Markdown 來源、固定文件識別／格式版本與單一欄位來源，文字說明不代替必要欄位。平台／執行／模組／資料流各依其領域格式定義欄位；缺欄位、重複 ID、錯誤型別／單位或版本引用可定位到文件與欄位，未經定義格式不自行猜讀。採哪種欄位呈現方式？
- **Options and tradeoffs:** A：固定標題與 Markdown 表格承載所有可檢查欄位，段落說明理由；可直接閱讀編輯，適合扁平資料，但複雜巢狀契約需拆成多表與 ID 引用，格式及跳脫處理較繁瑣。
  B：固定標題與表格承載扁平欄位，只有巢狀／條件式資料使用文件內指定 YAML 區塊（建議）；便於閱讀且能表達複雜設計，但需維護表格與區塊兩種解析規則。每項欄位的承載位置由格式規範固定，禁止同一欄位在兩處手填，也禁止任意混用。
  C：文件內指定 YAML 區塊承載全部可檢查欄位，其他 Markdown 只說明理由與選擇；解析及巢狀資料一致，適合大量複雜結構，但直接閱讀／修改 YAML 的負擔較高，表格或圖由工具產生且不作另一份可編輯來源。
- **User answer:** B
- **Explicit rationale:** 使用者未另提供理由；來源為本聊天對 Q-DOC-FIELD-FORMAT-001@2 的回覆。
- **Resulting impact:** 採用 REQ-011、DEC-011、AC-011，補充 REQ-006 的格式契約；未授權實作。
### DISC-012: 多檔恢復與持續推進
- **Situation:** 多檔更新需保證一致性，使用者要求恢復要求不可造成無法繼續執行。
- **Question:** 是否採用多檔更新的一致性與恢復要求：本次文件集合先在候選／暫存區完成欄位、依賴版本、來源與生成產物檢查；取得本次正式更新授權後，套用前再核對基準，基準改變則保留候選並處理差異，不覆寫他人修改。只有完整集合驗證成功後才能標記正式生效。更新或中斷失敗時保存候選、更新進度、失敗原因及必要恢復資料，上一套完整確認版本保持可追溯；若已有部分檔案寫入，標記更新未完成，正式讀取只能使用可驗證的完整版本，不能將新舊混合檔案當成有效版本或繼續相依程式修改。恢復時核對檔案仍符合原基準或本次已寫入內容，可安全地重試／恢復，遇到新修改須保留並處理差異。不得用 Git 提交或強制回退代替此機制。沿用既有範圍與授權規則，同範圍修復不重複要求授權，契約改變重新討論；失敗只阻擋相依工作。具體暫存／日誌及版本切換方法列於實作方案並以寫入／生成失敗、中斷及基準競爭測試驗證，不宣称多檔檔案系統寫入天然同時完成。
- **Options and tradeoffs:** 開放問題：全套成功才生效，失敗保存可恢復狀態與完整舊版；局部暫停相依操作，沿用同範圍修復授權。
- **User answer:** 採用。但不要卡住變成無法繼續執行。
- **Explicit rationale:** 使用者明確要求不要因規範卡住而無法繼續執行；來源為本聊天對 Q-DOC-UPDATE-RECOVERY-002@4 的回覆。
- **Resulting impact:** 採用 REQ-012、REQ-013、DEC-012、AC-012、AC-013，明定恢復入口可用、避免循環閘門及局部繼續；未授權實作。
### DISC-013: 更正失敗處理目標為解決問題
- **Situation:** 使用者指出助理「失敗後仍可繼續推進」的表述未符合意圖；僅保留進度或局部繼續不足以完成工作。
- **Question:** 本聊天中對「失敗後仍可繼續推進」表述的使用者更正；此為直接需求澄清，沒有另行提出新問題。
- **Options and tradeoffs:** 使用者直接更正：要把東西解決，不是停下，也不是僅在失敗後繼續推進。
- **User answer:** 要把東西解決，不是停下。也不是失敗後仍可以繼續推進。
- **Explicit rationale:** 來源為本聊天最新使用者註解 1，選取先前回覆「失敗後仍可繼續推進」並明確要求解決問題。
- **Resulting impact:** 修正 REQ-013、AC-013，新增 DEC-013；要求查因、必要修復、驗證成功及完成原工作，不以局部繼續代替。原 DISC-012 保留為歷史；未授權實作。
### DISC-014: 舊格式自動遷移
- **Situation:** 文件格式與恢復要求已採用，需定義舊 SPEC／設計遷移範圍及內容／授權／歷史保留方式。
- **Question:** 沿用使用者先前遇到舊 SPEC 自動轉成新版、缺漏或衝突繼續討論的方向，是否採用以下舊格式遷移要求：當要以舊文件作本次工程工作的執行依據時，自動準備本次 SPEC 及必要設計依賴的新格式工作／目前版本，無關歷史不作整批改寫。依已採用分檔與 Markdown 表格／指定 YAML 格式拆分，保留需求、決策、驗收 ID、內容語意、原始回答、實際驗證狀態及來源／版本關係，建立原檔到新檔與欄位對照；設計來源從舊 manifest 轉移至 Markdown 後，manifest 依新來源生成。純格式轉換有可核對的完整語意與來源證明時，依既有授權延續機制保存轉換證明、核對新文件集合後接續，不重複要求相同授權，也不虛構缺失的歷史或新授權。新必填欄位缺漏先從可信專案文件、已保存討論、平台資料及程式調查補足並記錄依據；無法確定或契約衝突才提出具體待決事項，在新格式工作版繼續討論，不自行假設設計或已驗證。新增規則導致需求、設計或驗收實質改變，先提出差異並依既有規則確認。原確認版本／來源快照作不可修改歷史，與新工作版明確關聯，不能把重新編排當成當時已確認新版。舊格式讀取僅用於轉換與追溯，當前執行與檢查採新機制，不混用新舊判斷。遷移失敗依 REQ-012／REQ-013 查因、修復、驗證並完成原工作；不能以留下待遷移標記替代解決。具體遷移與恢復步驟由流程文件定義，驗收涵蓋內容保留、引用完整、授權延續、缺資料／衝突及中斷續作。
- **Options and tradeoffs:** 開放問題：自動轉換本次工作及必要依賴，純格式可證明時延續授權，缺漏先查資料、衝突於新工作版討論，保留歷史並統一當前新機制。
- **User answer:** 採用
- **Explicit rationale:** 使用者未另提供理由；來源為本聊天對 Q-DOC-LEGACY-MIGRATION-003@7 的回覆。
- **Resulting impact:** 採用 REQ-014、REQ-015、DEC-014、AC-014、AC-015；未授權實作。
### DISC-015: 兩份整體修改方案確認
- **Situation:** 兩份完整修改方案與驗收計畫已呈現，需求／驗收與選擇映射檢查通過，等待使用者整體確認。
- **Question:** 是否確認以下兩份已呈現完整修改方案與驗收計畫：SPEC-0043「OS 與執行環境規劃治理」revision 46，及 SPEC-0044「通用文件治理改版」revision 10（本題追加後版本）。確認內容包含各自 Requirements／Decisions／Acceptance Criteria／Implementation Plan／Acceptance Mapping；前者負責七組條件式 MUST、OS 設計欄位及專業流程／檢查，後者負責分檔來源、格式、版本、更新／恢復／遷移及受管入口接續。純規則、文件治理規範、設計／檢查／更新／遷移流程各有責任文件；失敗須查因修復、驗證並完成原工作。全套工具、來源／生成一致性、授權延續、故障恢復、舊格式遷移及隔離分發驗收均需實際通過。本題為整體 SPEC 確認，不是「開始執行」授權；正式實作仍等待對此範圍的開始執行，安裝／發布不在本次範圍。
- **Options and tradeoffs:** 開放問題：確認兩份各自分工的完整方案，不授予正式實作或安裝／發布權限。
- **User answer:** 可以有這兩個SPEC
- **Explicit rationale:** 使用者未另提供理由；來源為本聊天對 Q-SPEC-PAIR-CONFIRM-004@10 的回覆。
- **Resulting impact:** DEC-015 記錄兩份方案確認，保留本文件全部已採用 REQ／AC 與 Implementation Plan／Acceptance Mapping；移除整體確認待決並交由 owner materialize，尚無本次開始執行授權。

## Implementation Plan
### 文件責任與修改位置
以下新檔名稱為本次方案的預定位置；現階段只保存規格，不修改正式 Skill、工具或來源設計。

| 責任 | 修改位置 | 內容 |
|---|---|---|
| 共用文件治理規範 | skills/engineering/spec-governance/references/document-governance.md（新增） | 來源唯一、ID／版本／引用、完整生效、授權保留、歷史追溯及失敗解決責任；不寫操作步驟。 |
| 共用格式契約 | references/document-format.md（新增）、spec-contract.schema.json | SPEC 主檔／附檔與設計共同識別、格式版本、固定表格／指定區塊、數值／引用／適用性表示及錯誤定位。 |
| 更新／恢復流程 | references/document-update-workflow.md（新增） | 候選準備、完整檢查、核對基準、套用、生效、失敗查因修復及安全續作；恢復不被驗收前置循環阻擋。 |
| 遷移流程 | references/document-migration-workflow.md（新增） | 舊單檔／manifest 讀取、來源對照、純格式證明、欄位補足、歷史保存與驗證；當前執行只採新機制。 |
| SPEC owner 與讀取 | scripts/spec_contract.py、execution_state.py、discussion_state.py；新增 document_bundle.py 作完整集合的讀取與格式投影責任模組 | 既有公開 owner 入口統一處理分檔；canonical 完整集合有確定性投影與來源位置，所有 callers 使用同一內容，不能各自猜讀主檔。 |
| 更新與遷移責任模組 | scripts/document_updates.py、legacy_document_migration.py（新增） | 持久化更新進度、基準比對、完整生效、恢復與來源轉換證明；不讓 managed_delivery 自行接管 SPEC 狀態。 |
| 領域來源與生成 | govern-modular-event-architecture 的格式文件、manifest-schema.md 及 check／render／schema／CLI 工具 | 模組、介面、資料流與平台／執行格式採同一共同契約；設計源資料全數有明確文件擁有者，manifest 為產物。 |
| 授權與父流程接續 | implement/scripts/managed_delivery.py 及相關契約；ask-matt、grilling、spec-governance、implement 的入口／說明 | 在既有來源事件與同範圍修復契約上加入完整集合綁定及轉換證明；查因修復後驗證並實際接續，不只輸出 next_action。 |
| 文件／打包 | 對應 docs、README／Skill 路由與既有分發腳本必要同步 | 不維護第二份 Skill 源樹，驗證所有新增引用、資源及工具均進入隔離組裝包。 |

### 解析、版本與更新的實作邊界
1. 每類格式以版本化欄位清單定義鍵、位置、型別／單位、引用、適用性與是否必填；Markdown 表格與指定 YAML 區塊各司其職。指定區塊以固定章節及標記辨識，不讀取範例區塊當資料。重複欄位／ID、未知版本、格式錯誤及缺檔均保留來源定位。
2. SPEC 主檔只保留識別、狀態、摘要與入口；requirements.md、acceptance.md、discussion.md、references.yaml、candidates/ 按已採用責任維護。references.yaml 固定綁定設計 ID／版本／內容雜湊，確認集合還須綁定本次需求、驗收及候選內容。
3. 每個目前設計一份可編輯來源，歷史為不可修改確認快照。生成 manifest 包括原有全部 catalog／擴充欄位；逐欄建立來源擁有者對照，不能因轉換丟失未列入簡單表格的資料，或把這些資料留為另一份手改 manifest。
4. 更新計畫有固定操作 ID、已核對基準、準備資料及持久化步驟紀錄。套用與恢復均核對現有內容屬於原基準或本次預期結果；新修改保留處理。同一操作續作不重複副作用。完整集合狀態供 readers 與 gate 核對，部分寫入不假裝完整生效。
5. 授權由既有 managed-delivery／execution owner 管理，轉換證明提供原內容與新內容的完整語意／來源關係；雜湊仍檢查完整性與並行變更，不單以格式雜湊改變視為需求改變。不得假造原快照、來源事件或信任紀錄。
6. 暫存／恢復資料限於本次集合與受管位置，候選與新修改保留；清理由已完成狀態及實際持有關係決定，不以反覆嘗試造成無界資料累積。恢復入口對未完成集合可用，完成後仍須全套驗證。

### 驗收映射與完成條件
本次採主機上的暫存專案、真實 owner／managed-delivery 呼叫鏈與隔離組裝包，保留每條 AC 的結果與來源版本；尚未執行的驗收不標 PASS。

| AC | 本次需證明的結果 |
|---|---|
| AC-003、007 | 入口可解析全部附檔與設計引用，缺檔／錯誤引用可定位，角色與來源沒有平行維護。 |
| AC-004、005 | 跨 SPEC 同一設計、候選隔離、固定確認版本、基準競爭與歷史不可變。 |
| AC-006、011 | 表格／YAML 解析、完整 manifest 欄位保留、確定性生成、產物漂移、重複欄位／ID／未知格式反案。 |
| AC-008、009 | 整套內容與原來源事件綁定；無關變更及純格式修復不重複授權，實質變更重新確認；討論與正式寫入範圍正確。 |
| AC-010 | 尚無程式的草案可完成設計檢查，必要可行性不能省略，實作與驗收結果分開判定。 |
| AC-012、013 | 各寫入步驟／生成失敗／中斷／基準競爭注入後，查因修復、驗證及原工作實際完成；單有進度或重試入口不合格。 |
| AC-014、015 | 舊 SPEC／manifest 自動遷移與完整來源對照、純格式授權延續、缺資料調查、衝突待決、歷史保留、無證據不得偽造。 |

擴充 test_spec_governance.py、test_managed_delivery.py、test_discussion_entry.py、架構來源／生成測試及 test_shared_skill_distribution.py；必要時新增同目錄的文件集合／更新／遷移測試模組。以實際公開入口與效果驗證，不只測私有函式或鏡像實作。完成相關回歸、兩份 SPEC／Standards 審查及隔離分發驗證才標已實作；安裝／發布另依其授權。

## Open Decisions
None.

## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-10-02 | 依使用者採用分工承接既有文件治理決策。 |
| 12 | 2026-10-02 | Recorded implementation PASS evidence. |

## Decision History

See Decisions, Discussion Context and the sourced Discussion History below.

## Pending Discussion

None.

## Completeness Gaps

None.

<!-- spec-audit:start -->
## Discussion History

- 01a0fba7-3b92-7020-8ccb-7264156dac99: 開始執行 SPEC-0043 與 SPEC-0044 已確認範圍
- 01a0fba7-3b92-7020-8ccb-7264156dac99: 使用者對已確認的 SPEC-0043 與 SPEC-0044 授予開始執行；本次沒有新增需求或設計決策。
- 01a0fba7-3b92-7020-8ccb-7264156dac99: 接續兩份已確認 SPEC 的執行授權；驗收映射準備後同步目前 owner 版本，沒有改變需求。

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"4dcbb1cd33b6b74ee5780e8b335fcf80fbf3103af9ef558e046c964f604fcff2","event_type":"start","event_version":1,"open_decisions":["更新失敗恢復、Markdown 固定欄位與解析契約、舊格式遷移、完整驗收映射待確認。"],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-10-02T05:40:51.335828+00:00","relationships":[],"revision":1,"snapshot_hash":"0b385758363e578c92d115527529eea1e9322116b99b8c69dcb15b16eacb241c","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"567bfb944ab94bec6aec902624c76b2da1f56b1cd61c8885c6675848b845792f","event_type":"reconcile","event_version":1,"open_decisions":["更新失敗恢復、Markdown 固定欄位與解析契約、舊格式遷移、完整驗收映射待確認。","Q-DOC-FIELD-FORMAT-001@2"],"previous_event_hash":"4dcbb1cd33b6b74ee5780e8b335fcf80fbf3103af9ef558e046c964f604fcff2","previous_snapshot_hash":"0b385758363e578c92d115527529eea1e9322116b99b8c69dcb15b16eacb241c","recorded_at":"2026-10-02T06:36:47.286187+00:00","relationships":[],"revision":2,"snapshot_hash":"6d5e9fab26f688f889337ec717019372aed235f7affeac3043227dd0d5b37421","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":["AC-011","DEC-011","DISC-011","REQ-011"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-011","DEC-011","DISC-011","REQ-011"],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"0b007d6d318da60fe1fff2dd4240b951a5becae9ba692c32be7c2c3eb6fa3d51","event_type":"reconcile","event_version":1,"open_decisions":["Markdown 欄位承載方案 B 已採用；領域格式的具體解析契約與欄位映射、更新失敗恢復、舊格式遷移、完整驗收及修改清單仍待定案。"],"previous_event_hash":"567bfb944ab94bec6aec902624c76b2da1f56b1cd61c8885c6675848b845792f","previous_snapshot_hash":"6d5e9fab26f688f889337ec717019372aed235f7affeac3043227dd0d5b37421","recorded_at":"2026-10-02T06:39:52.616610+00:00","relationships":[],"revision":3,"snapshot_hash":"8e8bf4cebff8ff639ebf7610ab94004a01bf157f9a37a51169599d3d95fd5905","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"92c197cdabcfc6d4ec8bf9fb4d1e3bbaee37279bdd6adf91e4ba5a719772437e","event_type":"reconcile","event_version":1,"open_decisions":["Markdown 欄位承載方案 B 已採用；領域格式的具體解析契約與欄位映射、更新失敗恢復、舊格式遷移、完整驗收及修改清單仍待定案。","Q-DOC-UPDATE-RECOVERY-002@4"],"previous_event_hash":"0b007d6d318da60fe1fff2dd4240b951a5becae9ba692c32be7c2c3eb6fa3d51","previous_snapshot_hash":"8e8bf4cebff8ff639ebf7610ab94004a01bf157f9a37a51169599d3d95fd5905","recorded_at":"2026-10-02T06:40:37.495714+00:00","relationships":[],"revision":4,"snapshot_hash":"f55829207e59dc67c2631e17d1b2484285658c4da4edf3ef26ac4cbcbe055214","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":["AC-012","AC-013","DEC-012","DISC-012","REQ-012","REQ-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-012","AC-013","DEC-012","DISC-012","REQ-012","REQ-013"],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"c4968e90a5920cf370eb573482d713b2d397efc40a4cd08d83ae562c3b8cb360","event_type":"reconcile","event_version":1,"open_decisions":["Markdown 欄位承載與多檔一致性／可持續恢復要求已採用；舊格式遷移策略仍待定案。具體領域格式、解析／恢復實作與檢查工具、完整驗收映射及最終修改清單需在整體方案呈現。"],"previous_event_hash":"92c197cdabcfc6d4ec8bf9fb4d1e3bbaee37279bdd6adf91e4ba5a719772437e","previous_snapshot_hash":"f55829207e59dc67c2631e17d1b2484285658c4da4edf3ef26ac4cbcbe055214","recorded_at":"2026-10-02T06:44:28.558854+00:00","relationships":[],"revision":5,"snapshot_hash":"820902f603849fe616738b874595d9cdc053deee9c191c0b9caa56f3f3d44d11","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":["AC-013","DEC-013","DISC-013","REQ-013"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":["AC-013"],"added_ids":["DEC-013","DISC-013"],"changed_ids":["AC-013","REQ-013"],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"12f038f7288a989290762e83e921f9dee3b038b13fbefdfc5bba82a00064c486","event_type":"reconcile","event_version":1,"open_decisions":["Markdown 欄位承載、多檔一致性及失敗後查因／修復／驗證／完成原工作要求已採用；舊格式遷移策略仍待定案。具體領域格式、解析／恢復實作與檢查工具、完整驗收映射及最終修改清單需在整體方案呈現。"],"previous_event_hash":"c4968e90a5920cf370eb573482d713b2d397efc40a4cd08d83ae562c3b8cb360","previous_snapshot_hash":"820902f603849fe616738b874595d9cdc053deee9c191c0b9caa56f3f3d44d11","recorded_at":"2026-10-02T06:46:03.777733+00:00","relationships":[],"revision":6,"snapshot_hash":"f5995ae8e9e18fcd4d5b1f8bdf2532c089a004644ee00ed2ad8d1704fc7459da","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"6d0641a2bc82fe166ef680c60bdb571a6efda4efc10bfa17f99a1b97529c44d4","event_type":"reconcile","event_version":1,"open_decisions":["Markdown 欄位承載、多檔一致性及失敗後查因／修復／驗證／完成原工作要求已採用；舊格式遷移策略仍待定案。具體領域格式、解析／恢復實作與檢查工具、完整驗收映射及最終修改清單需在整體方案呈現。","Q-DOC-LEGACY-MIGRATION-003@7"],"previous_event_hash":"12f038f7288a989290762e83e921f9dee3b038b13fbefdfc5bba82a00064c486","previous_snapshot_hash":"f5995ae8e9e18fcd4d5b1f8bdf2532c089a004644ee00ed2ad8d1704fc7459da","recorded_at":"2026-10-02T06:52:03.542285+00:00","relationships":[],"revision":7,"snapshot_hash":"76ea7f3b01ad8280a370d557531fbee71bc5a463298716e123b2daa1d67209ee","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":["AC-014","AC-015","DEC-014","DISC-014","REQ-014","REQ-015"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["AC-014","AC-015","DEC-014","DISC-014","REQ-014","REQ-015"],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"472fe9af1b8831758b4a377cb3b5f3b2b0957f3e1aee0f041b99936795c689ec","event_type":"reconcile","event_version":1,"open_decisions":["主要方向已採用；具體領域格式、解析／恢復實作與檢查工具、完整驗收映射及最終修改清單需整理後整體確認。"],"previous_event_hash":"6d0641a2bc82fe166ef680c60bdb571a6efda4efc10bfa17f99a1b97529c44d4","previous_snapshot_hash":"76ea7f3b01ad8280a370d557531fbee71bc5a463298716e123b2daa1d67209ee","recorded_at":"2026-10-02T06:54:27.683885+00:00","relationships":[],"revision":8,"snapshot_hash":"d47020618eec7fa6417d335d83119c95b787a660e45ac71bc46ad775dad0d727","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"ca88a4e206c06c9c84fbef516cb4b2397a08bf266ff3c2bee8b07cf22f2ea42a","event_type":"reconcile","event_version":1,"open_decisions":["完整修改方案與驗收計畫待使用者整體確認；已採用的規則、格式、恢復及遷移方向不重新開啟。"],"previous_event_hash":"472fe9af1b8831758b4a377cb3b5f3b2b0957f3e1aee0f041b99936795c689ec","previous_snapshot_hash":"d47020618eec7fa6417d335d83119c95b787a660e45ac71bc46ad775dad0d727","recorded_at":"2026-10-02T07:01:41.303729+00:00","relationships":[],"revision":9,"snapshot_hash":"ba03974f5831f423cd59e33f4524dfc93e988132b132154d636b8d7342b2e474","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"6dd41e8305d2dea3c33efa507b96358208a93b9db8db280a558fd8ee9a3ebf4e","event_type":"reconcile","event_version":1,"open_decisions":["完整修改方案與驗收計畫待使用者整體確認；已採用的規則、格式、恢復及遷移方向不重新開啟。","Q-SPEC-PAIR-CONFIRM-004@10"],"previous_event_hash":"ca88a4e206c06c9c84fbef516cb4b2397a08bf266ff3c2bee8b07cf22f2ea42a","previous_snapshot_hash":"ba03974f5831f423cd59e33f4524dfc93e988132b132154d636b8d7342b2e474","recorded_at":"2026-10-02T07:04:24.978736+00:00","relationships":[],"revision":10,"snapshot_hash":"c4af01438ed25b7a74d5e4d28c6af5d193655f7f9b2ec8da65067d5905ef65c8","verdict":"BLOCKED","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":["DEC-015","DISC-015"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":["DEC-015","DISC-015"],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"fac19ef54a7989aa806ab2fcbbad0fdd193ddc9a29ebc38599c5f5c718450107","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"6dd41e8305d2dea3c33efa507b96358208a93b9db8db280a558fd8ee9a3ebf4e","previous_snapshot_hash":"c4af01438ed25b7a74d5e4d28c6af5d193655f7f9b2ec8da65067d5905ef65c8","recorded_at":"2026-10-02T07:09:44.686750+00:00","relationships":[],"revision":11,"snapshot_hash":"981b6aa11b27ab5b0f266b81bcdb2c39bd844e968762c53f87a1ba825f52279d","verdict":"PASS","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"46a5d19f2de3e977b7c850679aa3a4110dd447b5102464935e2e8e387cf343cb","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"fac19ef54a7989aa806ab2fcbbad0fdd193ddc9a29ebc38599c5f5c718450107","previous_snapshot_hash":"981b6aa11b27ab5b0f266b81bcdb2c39bd844e968762c53f87a1ba825f52279d","recorded_at":"2026-10-02T07:09:45.783689+00:00","relationships":[],"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","verdict":"PASS","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"開始執行 SPEC-0043 與 SPEC-0044 已確認範圍","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0fba7-3b92-7020-8ccb-7264156dac99","task_ref":"01a0eb0c-4931-7112-8cdf-8862d42e984b","turn_id":"01a0fba7-3afd-76b0-b8aa-2e41a9c7b6e7"},"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"ad26863f64c27f7d127b0319e07314f31521a149b8d56e900d43b952d7469645","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"46a5d19f2de3e977b7c850679aa3a4110dd447b5102464935e2e8e387cf343cb","previous_snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","recorded_at":"2026-10-02T08:09:19.304930+00:00","relationships":[],"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","verdict":"PASS","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"a9ce7f4e0490681c2e2089cf536e4c723d4db9dce6e6e9f1cc2b2fa0af20e72f","reply_stage":"prepared-until-host-stop","reviewed_sources":["01a0fba7-3b92-7020-8ccb-7264156dac99"],"source_ref":"01a0fba7-3b92-7020-8ccb-7264156dac99","summary":"使用者對已確認的 SPEC-0043 與 SPEC-0044 授予開始執行；本次沒有新增需求或設計決策。","task_ref":"01a0eb0c-4931-7112-8cdf-8862d42e984b","turn_id":"01a0fba7-3afd-76b0-b8aa-2e41a9c7b6e7"},"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"3949808eaeac38bfc2d01487d1ed2e74419dfd5adc4122344c874a2971178e76","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"ad26863f64c27f7d127b0319e07314f31521a149b8d56e900d43b952d7469645","previous_snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","recorded_at":"2026-10-02T08:14:11.257843+00:00","relationships":[],"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","verdict":"PASS","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"289c43a371aca1a6e3788ed672ff2d342331bd0258939f29ac115ce550147deb","reply_stage":"prepared-until-host-stop","reviewed_sources":["01a0fba7-3b92-7020-8ccb-7264156dac99"],"source_ref":"01a0fba7-3b92-7020-8ccb-7264156dac99","summary":"接續兩份已確認 SPEC 的執行授權；驗收映射準備後同步目前 owner 版本，沒有改變需求。","task_ref":"01a0eb0c-4931-7112-8cdf-8862d42e984b","turn_id":"01a0fba7-3afd-76b0-b8aa-2e41a9c7b6e7"},"removed_ids":[]},"epoch":"ac2e22ae50b44a88a4eed351bdb83603","event_hash":"206b420786768bd23e94621920aec9b7bd182a6e26ead3137e49bee763509bdd","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"3949808eaeac38bfc2d01487d1ed2e74419dfd5adc4122344c874a2971178e76","previous_snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","recorded_at":"2026-10-02T08:16:42.281372+00:00","relationships":[],"revision":11,"snapshot_hash":"74fc2415047e91fd97427271b7eb56bb4282ba99c2b0e65f51a2befd89020e24","verdict":"PASS","working_id":"WORKING-SPEC-a95230978287-shared-document-governance"}
```
<!-- spec-audit:end -->
