---
spec_version: 1
status: implemented
change_set: authorization-event-routing-and-legacy-migration
spec_id: SPEC-0039
revision: 3
working_id: WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration
task_ref: 01a0d19d-43ff-7fa1-9144-3195fea4f71e
---
# 同範圍驗證準備自動修復與執行接續

## Problem
使用者要求針對「再次開始執行仍卡在舊授權」提出通用技能修改方案。SPEC-0038 已提供受控準備延續，但實際 SPEC-0068 舊 pending 紀錄沒有 preparation_validation_baseline。
本次讀碼修正先前判斷：managed_delivery.py authorize 已按 source_event_id 區分新事件與 retained 事件；新事件可擷取目前文件和驗證基準，不必先通過舊事件的準備證明。http-serialization-authorize-current.json 仍使用原事件 01a0d196-b4cc-7683-a49d-29890624d7f2，只證明該請求重試舊授權；尚未證明新的真實使用者授權事件也會被核心拒絕。

## Solution
使用者已確認方向：既有授權涵蓋同範圍 AC 準備修復，修復後自動接續執行；歷史相容性由技能內部處理。優先在既有 managed-delivery 父流程組合規劃、受控修復、SPEC owner 確認及原事件 admission 重試。保留文件雜湊作並行與完整性檢查，但不得單憑準備文件改變判定使用者改了需求。新授權分流僅為已有真實新指令時的相容分支，不作預設恢復方式。

## User Stories
使用者說一次開始執行後，技能遇到可唯一推導且不改變批准範圍的 AC 對照缺漏，應自行修復、重檢並繼續，不再要求相同授權。只有需要改變功能／門檻或無法決定的選擇才詢問；可調查的資料缺漏先由工具調查。

## Requirements
使用者已採納自動修復與接續方向；下列細部契約為本次修訂方案，尚未授權實作。
| ID | Requirement |
|---|---|
| REQ-001 | managed-delivery 父流程收到有效原授權且遇到可修復準備缺漏時，自動規劃修復、呼叫 prepare-validation / repair-acceptance、透過 owner 確認、重新 admission，通過後接續原實作目標。不得以 next_action 字串作為已接續完成的證據。 |
| REQ-002 | owner 以既定契約及明確專案規則唯一推導缺失對照；功能、驗收文字、門檻、既有選擇器與驗證義務保持不變。雜湊持續檢查檔案一致性與並行變更，授權延續則以受控差異證明判定。不得忽略整個 Acceptance Mapping 或只比較 ID。 |
| REQ-003 | 同一原授權事件贯穿準備及重試，保留原 binding／歷史並追加轉換證明。修復、owner 確認及 admission 各有持久化檢查點；中斷可重入，並行變更重讀，不覆寫。相同輸入無進展時退出並回報具體阻擋，禁止無限重試或重複詢問授權。 |
| REQ-004 | 舊遷移入口接受可核對授權時間點的原文件、驗證設定及來源證據，使用原雜湊／既有可信歷史檢查；只追加版本化遷移證明，再走 SPEC-0038 的全文差異及歷史檢查。沒有原驗證雜湊時，不得以當前檔案或未綁定備份冒充原始基準。 |
| REQ-005 | 遷移為內部相容步驟，先自動蒐集可信歷史。若已有針對目前規格的真實較新授權，使用既有新事件分支保存目前基準與取代關係，無需舊快照。沒有可核對歷史也沒有新授權時，誠實列出尚不能證明的差異；不能擅自認定同範圍，也不能再次套用已失敗的同一句指令。重載或引用不是新授權。 |
| REQ-006 | 分別回報 authorization_status、admission_status、reason_code、source_event_id、bound_revision、bound_hash、next_action；保留來源可信度限制。所有寫入在既有鎖及並行檢查下執行，中斷重試不產生重複授權或覆寫他人變更。 |

## Decisions
DEC-001：使用者以本次 annotation 2「對」採納「優先讓既有授權涵蓋同範圍 AC 準備修復，修復後自動接續，歷史相容性由技能內部處理」。本次詢問如何修改，非實作授權。禁止全面略過 stale 檢查或直接覆寫舊收據。

## Acceptance Criteria
| ID | Requirements | Criterion | Validation method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | 一次授權下，父流程自動完成缺失情境對照修復、owner 確認及完整 admission，抵達隔離 fixture 的原實作接續入口；原事件 ID 不變且沒有第二次授權請求。 | Host caller-to-managed end-to-end integration | PASS: [host acceptance evidence](../artifacts/validation/f0fa40ba5cfe46c9ac9459e838d59bad/manifest.json); 426 plugin integration tests including 16 continuation tests, architecture/distribution/format checks, Standards and Spec review PASS. Historical baseline absence remains explicitly reported; no device claim. |
| AC-002 | REQ-003, REQ-006 | 中斷重入不重複套用；並行修改不覆寫；相同輸入無進展時有限退出；其他 SPEC 授權隔離。 | Host state transition and fault injection | PASS: [host acceptance evidence](../artifacts/validation/f0fa40ba5cfe46c9ac9459e838d59bad/manifest.json); 426 plugin integration tests including 16 continuation tests, architecture/distribution/format checks, Standards and Spec review PASS. Historical baseline absence remains explicitly reported; no device claim. |
| AC-003 | REQ-004, REQ-005 | 可驗證歷史可遷移；缺失、錯誤雜湊、改門檻、跨身份、撤銷和未知差異拒絕；原紀錄不變。 | Host migration positive/negative fixtures | PASS: [host acceptance evidence](../artifacts/validation/f0fa40ba5cfe46c9ac9459e838d59bad/manifest.json); 426 plugin integration tests including 16 continuation tests, architecture/distribution/format checks, Standards and Spec review PASS. Historical baseline absence remains explicitly reported; no device claim. |
| AC-004 | REQ-006 | 新授權有效但其他 gate 未通過時仍禁止產品操作，輸出能分辨授權與准入原因。 | Host managed admission integration | PASS: [host acceptance evidence](../artifacts/validation/f0fa40ba5cfe46c9ac9459e838d59bad/manifest.json); 426 plugin integration tests including 16 continuation tests, architecture/distribution/format checks, Standards and Spec review PASS. Historical baseline absence remains explicitly reported; no device claim. |
| AC-005 | REQ-001, REQ-004, REQ-005 | SPEC-0068 歷史隔離 fixture 覆蓋可信歷史恢復、資料不足明確回報、已有較新真實授權不依赖舊快照三條路；引用或重載不建立授權；不修改實際韌體專案。 | Isolated historical-case regression | PASS: [host acceptance evidence](../artifacts/validation/f0fa40ba5cfe46c9ac9459e838d59bad/manifest.json); 426 plugin integration tests including 16 continuation tests, architecture/distribution/format checks, Standards and Spec review PASS. Historical baseline absence remains explicitly reported; no device claim. |

## Acceptance Mapping
```json
{
  "AC-001": {"evidence_claims":["host-semantics"],"rationale":"Caller routing and event identity are host contracts."},
  "AC-002": {"evidence_claims":["host-semantics"],"rationale":"Atomic state transitions and recovery run on the host."},
  "AC-003": {"evidence_claims":["host-semantics"],"rationale":"Migration verifies historical host records."},
  "AC-004": {"evidence_claims":["host-semantics"],"rationale":"Authorization and admission are independent host decisions."},
  "AC-005": {"evidence_claims":["host-semantics"],"rationale":"Historical data is replayed in an isolated host fixture, with no device claim."}
}
```

## Relationships
refines: SPEC-0038.

## Architecture impact
維持 spec-governance 的規格／歷史所有權和 managed-delivery 的授權／准入所有權。預計涉及 ask-matt、managed-delivery 規則、managed_delivery.py、execution_state.py、spec_contract.py、整合測試及對應 docs/architecture manifest 與衍生說明。正式 API 欄位需在實作前依 owner contract 定稿。

## Tradeoffs
重用既有受控修復與授權檢查，新增父流程的自動接續及舊歷史相容處理，比移除完整性檢查需要更多恢復測試，但能避免把工具準備缺漏轉嫁使用者。歷史完全缺失且無新授權時仍存在不能憑空證明的邊界。不涉及裝置排程或效能提升主張。

## Out of Scope
ESP32／其他產品修改、燒錄、實機操作、清除舊授權、偽造來源、略過驗收門檻、安裝或發布新版。

## Open Decisions
None.

## Routing/Gates
Spec review: PASS
本次僅建立方案草稿。後續需驗證呼叫端真實事件傳递、owner 契約、驗證計畫完整性、主機回歸、架構及組裝分發檢查；目前不宣稱測試或驗收 PASS。

## Revision History
- Initial: preserve corrected source findings and proposed dual-path repair.
- Revision 2: user adopted automatic same-scope AC repair and continuation as the primary path; fresh authorization is only a compatibility branch.
| 3 | 2026-09-24 | Recorded implementation PASS evidence. |

## Discussion Context
本次使用者 annotation 1 詢問工具名稱與修改位置；annotation 2 明確同意自動修復與接續方向。修訂方案以此為主要驗收目標；未聲稱任何資料不足的舊案例已成功遷移。
來源：目前任務使用者對「再次說開始執行仍卡在舊授權」的 annotation 與「提出修改方案」。本次讀碼發現既有新事件分支，因此撤回「完全沒有新授權入口」的絕對說法。來源檔案為 managed_delivery.py authorize 分支及外部唯讀 http-serialization-authorize-current.json；後者仍帶原始 source_event_id。正式根因尚需 caller-to-managed fixture 驗證，不假定每次重試都使用同一 ID。

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

- 01a0d1f4-3620-7160-8ff1-5fe1b93f8c75: 符合我的認知。開始執行SPEC-0039
- 01a0d1f4-3620-7160-8ff1-5fe1b93f8c75: User confirms SPEC-0039 and explicitly authorizes implementation: 符合我的認知。開始執行SPEC-0039. Same-scope automatic preparation repair and continuation; preserve existing changes.

### Source and Revision Audit

```jsonl
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"feda30eefde94ab0899118e88646f8cd","event_hash":"0eebf0e9dd770f12d785c5662be92eff868f0a9e3285902a1fd2d0ef709dd1f6","event_type":"start","event_version":1,"open_decisions":["候選方案待使用者審閱，尚未採納及授權實作。"],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-09-24T05:55:49.027731+00:00","relationships":[],"revision":1,"snapshot_hash":"2a2a404df87344354895e82c2557a91f9fdb92ab6798593251675302891daebc","verdict":"BLOCKED","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"}
{"affected_ids":["AC-001","AC-002","AC-005","REQ-001","REQ-002","REQ-003","REQ-005"],"conflicts":[],"continuity":"continuous","delta":{"acceptance_changes":["AC-001","AC-002","AC-005"],"added_ids":[],"changed_ids":["AC-001","AC-002","AC-005","REQ-001","REQ-002","REQ-003","REQ-005"],"removed_ids":[]},"epoch":"feda30eefde94ab0899118e88646f8cd","event_hash":"3bd40c14cb27852f6222c4155065c1ba6eefcc32e53417b83769975bcc8c00c2","event_type":"reconcile","event_version":1,"open_decisions":[],"previous_event_hash":"0eebf0e9dd770f12d785c5662be92eff868f0a9e3285902a1fd2d0ef709dd1f6","previous_snapshot_hash":"2a2a404df87344354895e82c2557a91f9fdb92ab6798593251675302891daebc","recorded_at":"2026-09-24T06:05:11.500544+00:00","relationships":[],"revision":2,"snapshot_hash":"e50e3f5eefa53e7a4a09f2981f74ee92ccb253cf3abb5d201c4174f9ab7ed80b","verdict":"PASS","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"goal":"符合我的認知。開始執行SPEC-0039","historical_entry_evidence":"not-inferred","kind":"entry","source_ref":"01a0d1f4-3620-7160-8ff1-5fe1b93f8c75","task_ref":"01a0d19d-43ff-7fa1-9144-3195fea4f71e","turn_id":"01a0d1f4-3620-7160-8ff1-5fe1b93f8c75"},"removed_ids":[]},"epoch":"feda30eefde94ab0899118e88646f8cd","event_hash":"162f4a31ea074407795a493e1eb66d9f6b3afb1d724813dc30e660800c676c5a","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"3bd40c14cb27852f6222c4155065c1ba6eefcc32e53417b83769975bcc8c00c2","previous_snapshot_hash":"e50e3f5eefa53e7a4a09f2981f74ee92ccb253cf3abb5d201c4174f9ab7ed80b","recorded_at":"2026-09-24T06:12:00.874264+00:00","relationships":[],"revision":2,"snapshot_hash":"e50e3f5eefa53e7a4a09f2981f74ee92ccb253cf3abb5d201c4174f9ab7ed80b","verdict":"PASS","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"feda30eefde94ab0899118e88646f8cd","event_hash":"7a461e9bab89fe58102bc50e7dd3fd39757dad179fcc5c7eaf090eb48500f91f","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"162f4a31ea074407795a493e1eb66d9f6b3afb1d724813dc30e660800c676c5a","previous_snapshot_hash":"e50e3f5eefa53e7a4a09f2981f74ee92ccb253cf3abb5d201c4174f9ab7ed80b","recorded_at":"2026-09-24T06:13:36.814303+00:00","relationships":[],"revision":2,"snapshot_hash":"82dc90812a7d4a04e3d01bfcb9de7429fd7043c4e1e589b13d5d5fbe906b33e0","verdict":"PASS","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"discussion":{"binding":{"revision":2,"snapshot_hash":"82dc90812a7d4a04e3d01bfcb9de7429fd7043c4e1e589b13d5d5fbe906b33e0","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"},"candidates":[],"completeness_review":null,"identified_items":{},"item_bindings":{},"kind":"saved","reply_sha256":"30a252a2f655aa3918e160c178cded15e6fb0f3c188136258673cdf11bc32040","reply_stage":"prepared-until-host-stop","reviewed_sources":["01a0d1ab-859b-7ba0-8629-140d96c8736d","01a0d1f4-3620-7160-8ff1-5fe1b93f8c75"],"source_ref":"01a0d1f4-3620-7160-8ff1-5fe1b93f8c75","summary":"User confirms SPEC-0039 and explicitly authorizes implementation: 符合我的認知。開始執行SPEC-0039. Same-scope automatic preparation repair and continuation; preserve existing changes.","task_ref":"01a0d19d-43ff-7fa1-9144-3195fea4f71e","turn_id":"01a0d1f4-3620-7160-8ff1-5fe1b93f8c75"},"removed_ids":[]},"epoch":"feda30eefde94ab0899118e88646f8cd","event_hash":"c3a2b99ad4323cf8bfd786f110b9ea180da470c8f75868d72a661babd7389cb7","event_type":"discussion","event_version":1,"open_decisions":[],"previous_event_hash":"7a461e9bab89fe58102bc50e7dd3fd39757dad179fcc5c7eaf090eb48500f91f","previous_snapshot_hash":"82dc90812a7d4a04e3d01bfcb9de7429fd7043c4e1e589b13d5d5fbe906b33e0","recorded_at":"2026-09-24T06:14:46.157203+00:00","relationships":[],"revision":2,"snapshot_hash":"82dc90812a7d4a04e3d01bfcb9de7429fd7043c4e1e589b13d5d5fbe906b33e0","verdict":"PASS","working_id":"WORKING-SPEC-e9f1181cd3fd-authorization-event-routing-and-legacy-migration"}
```
<!-- spec-audit:end -->
