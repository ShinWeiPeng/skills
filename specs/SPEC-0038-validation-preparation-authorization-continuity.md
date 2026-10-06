---
spec_version: 1
status: implemented
change_set: validation-preparation-authorization-continuity
spec_id: SPEC-0038
revision: 3
working_id: WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity
task_ref: 01a0d19d-43ff-7fa1-9144-3195fea4f71e
---
# 驗證計畫完整性與準備階段授權延續

## Problem
SPEC-0068 已保留 revision 2 的執行授權；確認前才發現 AC-003 缺少 scenario_layers。補齊對照經 reconcile 產生 revision 3 後，原授權被 preparation_binding_matches 拒絕。該檢查的準備雜湊涵蓋除狀態及稽核區外的文件，且歷史尾段只接受 discussion/materialize，因此即使沒有需求或驗收條件 ID 的變更，也無法延續。

「新討論」不會自動產生完整的機器可讀驗證計畫。先前已寫出實機驗證的文字要求，卻未同步補齊情境選擇欄位；完整性檢查直到 materialize 才揭露缺漏。確認入口有攔截，但前置方案準備未完成。不能把「沒有 changed_ids」等同所有語意皆未改變。

本任務上一份方案亦只出現在對話，未保存 canonical SPEC。這是討論持久化的執行遺漏；本次依使用者要求建立正式 SPEC，不把該遺漏誤稱授權機制的根因。

## Solution
先在方案合成時同步完成 AC 文字與 Acceptance Mapping，確認前集中檢查缺項；另延伸既有 prepare-validation / repair-acceptance，由 SPEC owner 保存受控的增補轉換證明，允許仍有效的原授權跨越經證明等價的準備變更。完整 admission 仍控制產品操作。

## User Stories
使用者希望新方案在呈現時已有可檢閱 SPEC 與完整驗證計畫；同範圍驗證補齊不應要求重複授權，真正的契約改變仍須重新確認和授權。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | 方案合成同步產生 AC 的驗證方法、evidence_claims、rationale 與適用情境選擇；呈現決策完整方案前執行 acceptance-plan completeness，確認入口再次檢查。缺項列為具體欄位缺漏，草稿仍可保存，不將規劃通過宣稱為驗收通過。 |
| REQ-002 | 由既有準備入口及 SPEC owner 協作補齊缺少的驗證定義和既有 AC 情境對照。僅允許可從既有契約和專案規則唯一推導的增補；不得替使用者新增產品範圍或驗收決策。 |
| REQ-003 | 每次轉換保存原授權事件、project/task/SPEC/working identity、前後文件與驗證輸入雜湊、完整差異及規則版本。原授權、舊收據及 journal 不覆寫。 |
| REQ-004 | 僅白名單新增的缺失對照和定義及其必要生命週期欄位變化可延續。逐項檢查全文差異；既有需求、決策、驗收文字、門檻、選擇器、驗證義務及既有值不可變更。未知欄位差異拒絕，不以 ID 清單或 actual_contract_delta 單獨作為證明。 |
| REQ-005 | 保留完整文件雜湊及歷史連續性檢查；preparation_binding_matches 僅接受可驗證的受控轉換鏈。一般 reconcile、reopen、撤銷、跨身份、損壞歷史仍拒絕。準備不授予產品或裝置操作權限；確認後重新執行完整 admission。 |
| REQ-006 | 在專案鎖內重讀基準並核對雜湊後保存。重複請求具冪等性；中斷或並行變更不可形成部分授權，恢復時核對所有輸入及轉換狀態；不得覆寫他人變更。 |
| REQ-007 | 舊 pending 授權僅在能重建原綁定文件、驗證原雜湊、連續歷史及全部受控差異時，新增恢復證明並重試原事件。證據不足回報缺少項目，不偽造來源、不把目前版本直接視為已授權。 |
| REQ-008 | 結果分開回報授權有效性、準備完整性、正式 admission 與驗收證據。拒絕提供具體欄位、差異或歷史原因，避免一律稱 stale。同步更新技能規則、管理流程文件及使用者文件中的受控例外。 |

## Decisions
| ID | Decision | Source |
|---|---|---|
| DEC-001 | 將前述修改方案建立為正式 SPEC，並解釋缺口成因；本次只進行規格工作。 | 本任務使用者 annotation 1「建立正式spec」及 annotation 2「為什麼會產生缺口?」。 |
| DEC-002 | 使用受控差異證明延伸既有準備入口；不全面放寬 reconcile，也不排除整個 Acceptance Mapping 的雜湊。 | 本任務前一則修改方案，依 DEC-001 轉為本次規格內容。 |

## Acceptance Criteria
| ID | Requirements | Criterion | Validation method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 新方案缺少適用情境、claims 或 rationale 時，方案完整性及確認入口均列出缺項；草稿保存成功；完整計畫不被誤報驗收通過。 | Host completeness and materialization integration tests | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |
| AC-002 | REQ-002, REQ-003, REQ-004, REQ-005 | 重現 SPEC-0068 revision 2 pending → 補 AC-003 對照 → reconcile → confirmed → admission，沿用同一來源事件；準備期間產品寫入仍拒絕。 | Host managed delivery integration regression | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |
| AC-003 | REQ-004, REQ-005 | 保持 ID 不變而修改需求、驗收內容、门檻、既有對照；或一般 reopen、撤銷、跨身份、損壞歷史、未知差異時，均拒絕沿用授權且產品檔案不變。 | Host table-driven negative integration tests | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |
| AC-004 | REQ-003, REQ-006 | 並行變更、中斷與同一請求重放不覆寫變更、不重複套用、不增加權限；恢復只能使用驗證完整的轉換。 | Host concurrency and fault-injection integration tests | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |
| AC-005 | REQ-007, REQ-008 | 舊授權案例在歷史與雜湊可重建時通過；缺證據時指出具體缺項且保存原紀錄。 | Host legacy-state recovery fixtures | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |
| AC-006 | REQ-008 | 原有授權、撤銷與管理入口回歸通過；技能、流程及 docs 對允許的例外描述一致；組裝外掛與 distribution validation 通過。 | Existing regression suite, documentation review and distribution validation | PASS: [host acceptance evidence](../artifacts/validation/cd97ffaf2ef548a6a0bebf5e90ebba6e/manifest.json); 180 host tests, architecture and distribution checks; independent Standards/Spec review PASS. |

## Acceptance Mapping
```json
{
  "AC-001": {"evidence_claims":["host-semantics"],"contract_dimensions":["call-order"],"execution_changes":[],"rationale":"Completeness and confirmation decisions are host CLI contracts."},
  "AC-002": {"evidence_claims":["host-semantics"],"contract_dimensions":["call-order"],"execution_changes":[],"rationale":"Replay the firmware incident as isolated host state fixtures; no device claim."},
  "AC-003": {"evidence_claims":["host-semantics"],"contract_dimensions":["call-order"],"execution_changes":[],"rationale":"Negative authorization boundaries are host state-machine behavior."},
  "AC-004": {"evidence_claims":["host-semantics"],"contract_dimensions":["call-order"],"execution_changes":[],"rationale":"Host locking, interrupted saves and idempotency require deterministic fault injection."},
  "AC-005": {"evidence_claims":["host-semantics"],"contract_dimensions":["call-order"],"execution_changes":[],"rationale":"Legacy recovery verifies document hashes and journal continuity on the host."},
  "AC-006": {"evidence_claims":["host-semantics"],"contract_dimensions":["input-output-units"],"execution_changes":[],"rationale":"Regression and assembled distribution checks do not claim desktop hook firing or physical validation."}
}
```

## Relationships
- refines: SPEC-0033, SPEC-0034, SPEC-0035, SPEC-0037
- External incident: C:/Users/hugo_peng/firmware/periphery/env_sensing/specs/SPEC-0068-http-response-serialization.md
- External evidence: C:/Users/hugo_peng/firmware/periphery/env_sensing/spec-governance/http-serialization-admission-transition.md

## Out of Scope
本次建立規格不修改產品程式；後續外掛實作不包含韌體修改、燒錄、實機操作或發佈。原韌體任務的授權不作為本次外掛實作授權。不得降低验收門檻、清除授權歷史或繞過 admission。

## Architecture impact
保留既有 spec-governance owner 與 implement managed-delivery 邊界。owner 驗證並保存規格轉換，delivery 驗證授權延續和正式 admission。修改 execution_state.py、spec_contract.py、managed_delivery.py 及既有整合測試；若新增公開符號或持久化欄位，更新對應 manifest/Flow 說明及版本相容測試，不建立新服務或並行任務。

## Algorithm impact
使用确定性白名單差異分類、雜湊與歷史鏈驗證。未知差異 fail closed；不使用模型語意評分判定等價，無可調閾值、即時排程或效能提升主張。

## Tradeoffs
相比全面放寬 reconcile，增加轉換紀錄與舊狀態恢復成本，但可追溯每次例外並限制權限。相比要求每次重新授權，可修復既有流程且不把工具欄位缺漏轉嫁使用者。前置完整性檢查負責減少新缺口，恢復機制處理舊狀態及規則變動；兩者缺一不可。

## Open Decisions
None.

## Authorization
使用者要求建立正式 SPEC。尚未授權修改外掛程式；規格確認不代表實作、發佈或韌體操作授權。

## Discussion Context
Source task: 01a0d19d-43ff-7fa1-9144-3195fea4f71e。先前方案未保存 SPEC；本次補正。成因已核對 preparation_contract_hash、preparation_binding_matches 及 SPEC-0068 稽核；尚未執行任何本規格測試，不主張整體驗收 PASS。

## Revision History
- Initial: persist requested proposal, add prevention of late validation gaps and bounded authorization continuity/recovery.
| 3 | 2026-09-24 | Recorded implementation PASS evidence. |

## Routing/Gates
Spec review: PASS
規格完整性檢查及確認；後續實作需本範圍授權、formatter/architecture 適用檢查、主機正負向整合回歸及外掛組裝驗證。所有驗收證據目前 Pending。

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

- 01a0d1ab-859b-7ba0-8629-140d96c8736d: 開始執行SPEC-0038
- 01a0d1ab-859b-7ba0-8629-140d96c8736d: User authorized execution of confirmed SPEC-0038 with no contract change. Complete the acceptance projection, preserve existing work and implement the reviewed preparation continuity scope.

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"46ba000a627f4632a34b617630f5a7be","event_hash":"52b2d7f8d5de9d382299f3be2cf1db2c2e574ff74fe355e3b06e8be1df4981f8","event_type":"start","event_version":1,"open_decisions":[],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-24T04:24:22.167229+00:00","relationships":[],"revision":1,"snapshot_hash":"21fd6deee494cd761952044a90f55a33ab2ddfbfebc73ebd114df5dbfb06a2f5","verdict":"PASS","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":[],"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"46ba000a627f4632a34b617630f5a7be","event_hash":"4d73b5d61309242be5dd3317d09a99f995266a9d2ec124aebf5597651bc6c886","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"52b2d7f8d5de9d382299f3be2cf1db2c2e574ff74fe355e3b06e8be1df4981f8","previous_snapshot_hash":"21fd6deee494cd761952044a90f55a33ab2ddfbfebc73ebd114df5dbfb06a2f5","recorded_at":"2026-09-24T04:24:52.407366+00:00","relationships":[],"revision":2,"snapshot_hash":"911275b54a00ab27d5e758e6fbf919cb4504bd68069c1e83c2524229bc286e5e","verdict":"PASS","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"46ba000a627f4632a34b617630f5a7be","event_hash":"395c5746e59a9a7ca160f1e71ce8360af86f84bc1cba5194f065c233baa0c77f","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"4d73b5d61309242be5dd3317d09a99f995266a9d2ec124aebf5597651bc6c886","previous_snapshot_hash":"911275b54a00ab27d5e758e6fbf919cb4504bd68069c1e83c2524229bc286e5e","recorded_at":"2026-09-24T04:25:00.430955+00:00","relationships":[],"revision":2,"snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","verdict":"PASS","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"開始執行SPEC-0038","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0d1ab-859b-7ba0-8629-140d96c8736d","task_ref":"01a0d19d-43ff-7fa1-9144-3195fea4f71e","turn_id":"01a0d1ab-859b-7ba0-8629-140d96c8736d"},"removed_ids":[]},"epoch":"46ba000a627f4632a34b617630f5a7be","event_hash":"33b2c5bb458ac01fc4ec1bab737430f2efb22a9a40d8e1da892b6a7d1ef7a653","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"395c5746e59a9a7ca160f1e71ce8360af86f84bc1cba5194f065c233baa0c77f","previous_snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","recorded_at":"2026-09-24T04:29:23.784273+00:00","relationships":[],"revision":2,"snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","verdict":"PASS","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":2,"snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"9da07ee4f2a3e488b192e40f71788e54467a6d525d7a11660fc301809c76e20b","reply_stage":"prepared-until-host-stop","reviewed_sources":["01a0d1ab-859b-7ba0-8629-140d96c8736d"],"source_ref":"01a0d1ab-859b-7ba0-8629-140d96c8736d","summary":"User authorized execution of confirmed SPEC-0038 with no contract change. Complete the acceptance projection, preserve existing work and implement the reviewed preparation continuity scope.","task_ref":"01a0d19d-43ff-7fa1-9144-3195fea4f71e","turn_id":"01a0d1ab-859b-7ba0-8629-140d96c8736d"},"removed_ids":[]},"epoch":"46ba000a627f4632a34b617630f5a7be","event_hash":"08abdf03c9b85fb8be882eb3cc262d93eeec615e481fba7a4564bda0de84bde2","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"33b2c5bb458ac01fc4ec1bab737430f2efb22a9a40d8e1da892b6a7d1ef7a653","previous_snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","recorded_at":"2026-09-24T04:34:01.702760+00:00","relationships":[],"revision":2,"snapshot_hash":"f8fd8da41329523dd988c25972a599c9062f9908cfd72788b085199bd900ec31","verdict":"PASS","working_id":"WORKING-SPEC-d8af7ee439f9-validation-preparation-authorization-continuity"}
```
<!-- spec-audit:end -->
