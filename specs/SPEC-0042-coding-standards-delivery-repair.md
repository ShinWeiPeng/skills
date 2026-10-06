---
spec_version: 1
spec_id: SPEC-0042
revision: 2
status: implemented
change_set: coding-standards-delivery-repair
working_id: WORKING-SPEC-2b8b2ac19264-coding-standards-delivery-repair
task_ref: 01a0eb0c-4931-7112-8cdf-8862d42e984b
---
# 規則整理的治理入口修復

## Problem
SPEC-0040/0041 執行時，owner 接受四欄 AC 而規劃器要求五欄；補 Evidence 造成授權失效。受管 writer 無 mkdir/move/delete 能力。使用者本輪明確允許原兩份 SPEC 使用一般檔案工具，並指示開始修正這三項治理問題。

## Solution
統一 AC 解析契約；保留精確原始文件、驗證設定與審計鏈的受控準備證明，擴充可唯一決定的空 Evidence 欄位準備，不把任意文字更改當同範圍。受管檔案操作新增有界目錄建立、精確雜湊的檔案移動及刪除，保留准入與路徑限制。沒有需要重問的產品決策。

## User Stories
一次授權可完成既定規格準備與檔案整理；真正的需求變更、越界路徑和並行改動仍被拒絕。

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | owner 與 planner 使用同一 AC 解析契約；四欄 Evidence 缺省為未驗證，五欄保留實際證據，重複/缺欄/未知欄拒絕，不把缺證據當 PASS。 |
| REQ-002 | 可唯一導出的 Evidence 空欄準備由 owner 產生，延續原事件須驗證原 bytes/hash、全文限定差異、連續 journal 及未放寬驗證定義；任意 criterion、門檻、scope、既有 evidence、其他章節改動均不續權。 |
| REQ-003 | 受管 mkdir、move、delete 皆核對當前授權，拒絕治理目錄、路徑逃逸、連結/接合點；move 不覆蓋目的檔，delete 僅單一有已核對 hash 的普通檔，無遞迴刪除。 |
| REQ-004 | 原有未提交改動保留，文件/測試同步；原 SPEC-0040/0041 的一般工具例外僅限本次，不改成全域忽略准入。 |

## Decisions
| ID | Decision |
|---|---|
| DEC-001 | 使用者對一般工具提問回答「允許」，並對統一格式、同範圍續權、目錄搬移功能回答「開始進行」。沿用本次明確授權，不把工具修復變成第二次授權要求。 |

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | 四/五欄解析結果一致且非法表被 owner 與 planner 同時拒絕 | Host parser positive/negative fixtures | PASS: artifacts/validation/5d264280cc9e499f9854a4a31dec5623/AC-001-review.json |
| AC-002 | REQ-002 | 空 Evidence 準備保留原事件，修改 criterion/evidence/其他章節及不連續歷史拒絕 | Host preparation and tampering tests | PASS: artifacts/validation/5d264280cc9e499f9854a4a31dec5623/AC-002-review.json |
| AC-003 | REQ-003 | 建立/搬移/刪除成功與越界、stale hash、覆蓋、連結、無授權均有正反案 | Host temporary filesystem integration | PASS: artifacts/validation/5d264280cc9e499f9854a4a31dec5623/AC-003-review.json |
| AC-004 | REQ-004 | 原行為回歸與 source/package 一致，未覆寫不相關工作 | Integration suite and diff review | PASS: artifacts/validation/5d264280cc9e499f9854a4a31dec5623/AC-004-review.json |

## Acceptance Mapping
```json
{
 "AC-001":{"evidence_claims":["host-semantics"],"rationale":"Shared host parser contract."},
 "AC-002":{"evidence_claims":["host-semantics"],"rationale":"Host receipt and owner transition with negative tampering cases."},
 "AC-003":{"evidence_claims":["host-semantics"],"rationale":"Bounded host filesystem operations in isolated temporary projects."},
 "AC-004":{"evidence_claims":["host-semantics"],"rationale":"Host integration, packaging and preservation checks."}
}
```

## Relationships
本次為 SPEC-0040/0041 的執行阻擋修復；不取代其驗收。

## Out of Scope
任意語意等價推理續權、降低驗收門檻、遞迴刪除、外部部署、安裝或 commit。

## Open Decisions
None.

## Routing/Gates
Spec review: PASS
使用者明確啟動修復；保留規格、回歸與審查，原兩份 SPEC 的一般工具例外不成為產品預設。

## Discussion Context
來源為本聊天當前使用者兩則註解：對一般工具「允許」，對治理修復「開始進行」。

## Revision History
- 1: 記錄當前明確授權的修復範圍。
| 2 | 2026-10-02 | Recorded implementation PASS evidence. |

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
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"198d3ab10ee145aca1d571058507b08f","event_hash":"f00580e43ba33e34da948fd793cc7c0e411adf9887d973a2f93e2af7e74f7f6c","event_type":"start","event_version":1,"open_decisions":[],"previous_event_hash":null,"previous_snapshot_hash":null,"recorded_at":"2026-10-02T02:21:43.952317+00:00","relationships":[],"revision":1,"snapshot_hash":"4a17ca3e36c3df2f05283a9aa7d7590542617d18d885e986c91d8ed1b0979594","verdict":"PASS","working_id":"WORKING-SPEC-2b8b2ac19264-coding-standards-delivery-repair"}
{"affected_ids":[],"conflicts":[],"continuity":"continuous","delta":{"added_ids":[],"changed_ids":[],"removed_ids":[]},"epoch":"198d3ab10ee145aca1d571058507b08f","event_hash":"53a7334cff35d243f61f9ccaf0525c20fcce3548e326afb2a5d0ab9e45159468","event_type":"materialize","event_version":1,"open_decisions":[],"previous_event_hash":"f00580e43ba33e34da948fd793cc7c0e411adf9887d973a2f93e2af7e74f7f6c","previous_snapshot_hash":"4a17ca3e36c3df2f05283a9aa7d7590542617d18d885e986c91d8ed1b0979594","recorded_at":"2026-10-02T02:56:02.248410+00:00","relationships":[],"revision":1,"snapshot_hash":"21d3ce5c73e100a9f7f75161641c22a2c0d30c22b8afdfa6618a19ffd26aba06","verdict":"PASS","working_id":"WORKING-SPEC-2b8b2ac19264-coding-standards-delivery-repair"}
```
<!-- spec-audit:end -->
