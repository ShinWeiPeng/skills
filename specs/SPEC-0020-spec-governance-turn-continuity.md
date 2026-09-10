---
spec_version: 1
spec_id: SPEC-0020
revision: 5
status: implemented
change_set: spec-governance-turn-continuity
---

# Cross-turn specification governance continuity

## Problem

In task 01a0857c-7484-7863-a889-966e8e9a0783, decisions to preserve local files and exclude them from Git tracking led directly to writes without visible specification reconciliation. Existing specifications retained conflicting test-tracking requirements. Current routing depends on caller-supplied unresolved-decision context and does not by itself intercept arbitrary tool writes.

## Solution

Repair plugin-level task/change-set continuity, reconcile-before-resume routing, mutation preflight for governed delivery, and multi-turn regression coverage. Preserve required choices without a plugin response deadline. Keep the exact user instruction 開始執行 as the final human execution authorization after the decision-complete specification is available for review. Host-wide arbitrary-write interception investigation is excluded.

## User Stories

- As a user, I want settled answers and new change decisions to reach the specification without repeatedly naming a skill.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Preserve task/change-set identity and pending decision references across turns; short answers must not silently clear pending state. |
| REQ-002 | Reconcile change decisions before further governed questions or delivery; materialize and verify the applicable specification before implementation. |
| REQ-003 | Keep factual read-only questions read-only and detect conflicts with existing specification requirements. |
| REQ-004 | Report the actual enforcement boundary; plugin routing success must not be presented as proof that arbitrary tool writes are intercepted. |
| REQ-005 | Governed decision presentation must not request switching to Plan mode merely to show options. Select an available question surface in the current mode; provide durable Markdown options when necessary. |
| REQ-006 | Required choices have no plugin-imposed response deadline. Timeout, empty tool results, a preselected option, mode changes, interruptions and unrelated follow-up messages must not count as an answer or authorization. Required decisions remain pending until explicitly answered or withdrawn by the user; dependent modification remains blocked while independent read-only work may continue. |
| REQ-007 | Persist each pending question identity, option text and version in the working specification. After interruption or UI disappearance, recover the same question without silently choosing, clearing state, duplicating prompts or accepting an answer against changed options. |
| REQ-008 | Keep 開始執行 as the final explicit human execution gate for the reviewed change set. Adopting a proposal, selecting an option, quoting the phrase, silence, or returning to Default mode does not grant execution. Canonical specification completion and verification are independently required before governed delivery. Existing no-contract-delta authorization retention remains compatible. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Required user choices have no plugin-imposed response deadline or timeout-based default. If a host tool times out, preserve the pending decision and durable options; do not continuously poll or hold a blocking tool call indefinitely. Host UI timer cancellation is capability-dependent and must not be claimed without verification. |
| DEC-002 | Adopt the plugin-only complete workflow repair. Do not include host-level arbitrary-tool-write interception investigation in this change set. |
| DEC-003 | Preserve the existing 開始執行 gate as the final human confirmation; proposal adoption confirms scope but does not authorize implementation. |

## Discussion Context

### DISC-001: Requested proposal

- **Situation:** The inspected conversation lost specification continuity when explanations became modification decisions.
- **Question:** What work is requested?
- **Options and tradeoffs:** Repair only plugin-owned continuity, or extend scope to investigate host-level enforcement.
- **User answer:** 提出修改方案
- **Explicit rationale:** not stated
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004; scope remains open.

### DISC-002: Unanswered options disappear during mode changes

- **Situation:** The user reports occasionally entering planning mode for options, then returning to execution mode after elapsed time before reading or choosing finishes. The host-level trigger is not yet established. The proposal skill includes an unconditional instruction to tell the user to switch to Default mode, although the shared question contract says missing structured UI does not require Plan mode.
- **Question:** What additional failure should this change address?
- **Options and tradeoffs:** Preserve unanswered decisions independently of tool and mode lifecycle; independent read-only work may continue, but dependent changes wait for explicit input.
- **User answer:** 還有發現在偶爾會切到規劃模式跳出選項，然後時間到右切回執行模式，導致沒選到，也還沒看完選項
- **Explicit rationale:** The options disappear before the user finishes reading or selecting.
- **Resulting impact:** REQ-005, REQ-006, REQ-007, AC-004, AC-005. This report does not answer OD-001.

### DISC-003: Remove the decision deadline

- **Situation:** The user cannot finish reading or selecting before the reported question timeout.
- **Question:** Is removing the timeout acceptable?
- **Options and tradeoffs:** Remove the plugin-level response deadline and preserve pending choices; host-owned UI timers may require durable text fallback instead of cancellation.
- **User answer:** 不然取消逾時也可以。
- **Explicit rationale:** not stated
- **Resulting impact:** DEC-001, REQ-006, AC-004. User accepts no timeout for the required choice; OD-001 remains unanswered.

### DISC-004: Adopt plugin scope and preserve final human confirmation

- **Situation:** OD-001 distinguished plugin workflow repair from host interception investigation.
- **Question:** Which repair scope should be adopted?
- **Options and tradeoffs:** Plugin repair is bounded to existing governance entry points; host interception would require additional platform capability research and a different acceptance boundary.
- **User answer:** Selected 「先修 plugin 完整流程（建議）」 with 「採用」; clarified 「目前有擋開始執行，這邊是人為確認的最後關卡。」
- **Explicit rationale:** The existing 開始執行 gate is the final human confirmation checkpoint.
- **Resulting impact:** DEC-002, DEC-003, REQ-004, REQ-008, AC-003, AC-006. OD-001 is resolved; no implementation authorization is supplied by this answer.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | Replay explanation, tracking decision, proposal, execution, and a later contract change; every modifying transition retains correct specification identity and reconciles before delivery. | Multi-turn route and lifecycle integration fixtures, including process restart and stale state. | PASS: 215-test regression suite; composed router, subprocess recovery and reopen lifecycle fixtures pass. |
| AC-002 | REQ-003 | Factual questions do not create decisions; a change from retaining tracked tests to excluding tests records the conflict and resulting relationship. | Read-only and contract-delta negative/positive fixtures. | PASS: factual review/diagnosis/verification routing and conflict-preserving reconciliation fixtures pass. |
| AC-003 | REQ-002, REQ-004 | Missing, stale, ambiguous or mismatched spec evidence blocks governed delivery; tests document which entry points are covered. | Delivery preflight integration tests and bypass-boundary documentation review. | PASS: canonical drift, current hash, malformed state and task identity admission fixtures pass; plugin-only boundary documented. |
| AC-004 | REQ-005, REQ-006 | In Default and Plan scenarios, displaying a question does not request a mode switch solely for the choice UI; no plugin response deadline is imposed; simulated elapsed time, timeout, empty response, preselection and mode changes preserve the pending decision and never enable dependent writes. | Question-surface and pending-decision integration fixtures with injected tool outcomes; inspect rendered fallback options. | PASS: exact Markdown/no-deadline/no-mode-change presentation assertions and clock-independent recovery; shared skill text review. Native host timer cancellation excluded. |
| AC-005 | REQ-006, REQ-007 | After process restart, unrelated input or disappearance of the question surface, the same question and options remain recoverable; an explicit answer is reconciled against the recorded version exactly once. | Restart, interruption, duplicate/stale answer and recovery fixtures plus manual rendered-choice checklist. | PASS: restart, duplicate/stale/empty answer, semantic numeric-answer and normalized-journal fixtures pass. |
| AC-006 | REQ-002, REQ-008 | Proposal adoption, option selection, quoted execution phrases, empty responses and mode changes never authorize governed delivery. The exact affirmative execution instruction can proceed only with the matching confirmed and verified contract; actual contract changes require renewed authorization under the existing lifecycle. | Authorization and spec-lifecycle integration fixtures including negative cases and unchanged-contract resumption. | PASS: explicit execution rejection/acceptance and unchanged-versus-changed reopen authorization fixtures pass. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-003 |
| AC-003 | depends_on | REQ-004 |
| AC-004 | depends_on | REQ-005 |
| AC-004 | depends_on | REQ-006 |
| AC-005 | depends_on | REQ-006 |
| AC-005 | depends_on | REQ-007 |
| REQ-006 | depends_on | DEC-001 |
| REQ-004 | depends_on | DEC-002 |
| REQ-008 | depends_on | DEC-003 |
| AC-006 | depends_on | REQ-008 |

## Out of Scope

- Host interception research, modifications to App/CLI internals, or guarantees covering arbitrary tool calls.

- Modifying the inspected firmware repository or retroactively inventing historical approval records.
- Publishing, installing, committing or changing product code during proposal preparation.

## Open Decisions

None.

## Routing/Gates

- Spec review: PASS
- Execution authorized: user exact 開始執行 in task 01a085c7-8a93-7a73-b625-2b09168538ec.

- ask-matt: implementation present; durable context present; unresolved decision false after reconciliation of DISC-004.
- grilling; immediate resume target spec-governance.
- OD-001 resolved by DEC-002; canonical specification verified before implementation. Detailed evidence: spec-governance/SPEC-0020-validation.md.
- Architecture and algorithm impact assessment required if routing/state interfaces change.
- Spec verification, formatter policy, focused integration tests and distribution validation required before implementation delivery.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-09 | Capture observed gap, candidate scope and open enforcement-boundary decision. |
| 2 | 2026-09-09 | Capture unanswered-choice persistence, mode-independent presentation, timeout semantics and recovery acceptance. |
| 3 | 2026-09-09 | Record user acceptance of no deadline for required choices, with host capability boundary and durable fallback. |
| 4 | 2026-09-09 | Resolve plugin-only scope and preserve the final human execution gate; no product execution authorization. |
| 5 | 2026-09-09 | Recorded implementation PASS evidence. |
