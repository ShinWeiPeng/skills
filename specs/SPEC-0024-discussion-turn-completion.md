---
spec_version: 1
spec_id: SPEC-0024
revision: 3
status: implemented
change_set: discussion-turn-completion
---

# Discussion turn completion

## Problem

In task 01a089f8-2a35-7893-b31c-311226ccb4a5, the user selected option 2, removed the unfiltered comparison and asked a technical confirmation in one message. The assistant answered only the technical question and ended the turn without reconciliation or a next question. The original rollout lines 204-210 contain zero tool calls; after the user asked to keep discussing at line 214, reconciliation and the next question resumed. Existing audit_trace catches unsaved decisions but cannot distinguish a persisted decision followed by premature finalization from a correctly presented next question.

## Solution

Add a shared discussion turn completion contract and checked continuation assessment. Preserve the active discussion through mixed-intent messages, reconcile explicit answers and requirements, inspect remaining decisions, then either present one persisted question or materialize a complete proposal. Make conversational completion distinct from product execution admission. Apply across all projects using the plugin.

## User Stories

As a user, I can answer an option, adjust scope and ask a factual question together without reminding the assistant to continue the active discussion.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | During an active governed discussion, interpret each message for all applicable components: answer, requirement change, factual question and stop/pause intent. A technical question must not erase a concurrent answer or requirement. Pure factual follow-ups preserve the active pending decision without inventing an answer. |
| REQ-002 | Answer factual questions and reconcile explicit decisions and scope changes before asking the next question. After persistence, reload the authoritative question and open-decision state. If an unresolved user decision remains, present exactly one actionable question in the same turn; if repository facts are needed first, investigate them read-only. Never end solely with a promise to discuss later. |
| REQ-003 | A turn may wait for the user only after presenting the current persisted question, after explaining a concrete blocker and required input, after an explicit user discussion pause, or after materializing a decision-complete SPEC/proposal. Factual answers during an unanswered decision must preserve and visibly reconnect that decision without repeatedly recreating it. No invented decisions or automatic option adoption. |
| REQ-004 | Preserve SPEC-0023: Default mode numbered options, existing Plan mode preserved, no response deadline, and every SPEC revision invalidates prior product execution authority. Product suspension never stops permitted discussion or SPEC persistence. |
| REQ-005 | Add structured continuation assessment and observed per-turn trace validation for premature completion. Evidence must correlate persisted question identity/version, open decisions, presentation and turn boundary; callers cannot pass merely by asserting a final reason. Report observed-audit scope honestly; no host-wide final-response interception claim. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Extend the existing shared contracts, SPEC context assessment and managed trace auditor rather than introduce a second discussion state store. |
| DEC-002 | A factual follow-up can be answered immediately, but must reconnect the existing unanswered decision; a mixed answer is reconciled first. |

## Discussion Context

### DISC-001: Shared discussion continuity proposal

- **Situation:** User reports discussion automatically stopping; original trace shows technical-only finalization after a mixed decision message.
- **Question:** How should the common workflow prevent premature discussion completion?
- **Options and tradeoffs:** Instruction-only reminders are smaller but lack a checkable completion result. Shared guidance plus state-based continuation assessment and observed trace auditing add validation cost but cover mixed messages and distinguish waiting from premature completion. Host interception remains outside the previously agreed plugin-only scope.
- **User answer:** 還有發現討論會自動停下來。這是為什麼?；提出修改方案
- **Explicit rationale:** No additional rationale stated; prior all-project scope and separate execution authorization remain in effect.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, DEC-001, DEC-002.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | Replay option 2 plus removal of an output comparison plus technical question: answer the question, reconcile both decisions, present the next saved question without a user continue reminder. | Original trace negative fixture, lifecycle tests and controlled multi-turn model replay. | PASS: mixed reply persists highpass-only/no-comparison requirement, then next question in lifecycle test; controlled model factual-answer and next-question scenario in SPEC-0024-interaction-review.md. |
| AC-002 | REQ-002, REQ-003, REQ-005 | Saving SPEC then ending with unresolved decisions and no presented question/blocker/pause is rejected; a valid persisted/presented question permits waiting. | Per-turn completion assessment and trace tests, including false caller reason and stale question identity/version. | PASS: per-turn premature completion, stale question/context, false reason, duplicate question and evidenced blocker regressions; 248 assembled tests. |
| AC-003 | REQ-001, REQ-003, REQ-004 | Pure factual follow-up preserves the same unanswered question; numeric/free-form answers reconcile once; stop-discussion preserves state; stop-product continues discussion; timeout never resolves pending input. | Parameterized lifecycle tests and controlled mode-specific model scenarios. | PASS: factual followup/no answer preserve question; explicit discussion pause differs from product pause; malformed and contradictory evidence rejected; controlled mode scenarios. |
| AC-004 | REQ-003, REQ-004 | With zero unresolved decisions, materialize and present the complete proposal, then await exact execution authorization; no invented next question or product edit. | Completion and negative authorization scenarios with unchanged product hashes. | PASS: confirmed matching proposal required; metadata-only canonical revision/status drift blocked; completion always grants no product authority; CLI/lifecycle regressions. |
| AC-005 | REQ-004, REQ-005 | New and existing project scenarios use the same contract and isolated state; existing routes, receipt rejection and release checks remain valid. | Assembled plugin regressions, architecture gate, two-axis review and evidence scope audit. | PASS: 248 assembled plugin tests, distribution validation, architecture release gate, formatter checks and independent Spec/Standards follow-ups. Model scenarios cover new/existing projects with caller-attested evidence limits. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | refines | SPEC-0022 |
| REQ-004 | depends_on | SPEC-0023 |
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-005 |
| AC-003 | depends_on | REQ-003 |
| AC-004 | depends_on | REQ-004 |
| AC-005 | depends_on | REQ-005 |

## Out of Scope

IMU application changes; automatic user decisions; timeout removal in host software; host-wide interception of final replies; installation, commit, push or product implementation during proposal preparation.

## Open Decisions

None.

## Routing/Gates

Spec review: PASS

Implementation explicitly authorized by the user 開始執行 after this proposal (root rollout line 2766). Product validation completed before this final evidence update, which invalidates prior execution authority. Implemented diff: ask-matt decision question contract and router handoff guidance; spec-governance continuation assessment using existing turn-context; clarify-improvement-proposals and grilling completion rules; managed_delivery.audit_trace per-turn events; matching docs and regression tests. Preserve existing execution_state receipt behavior.

Architecture impact: existing spec_governance_domain owns persisted context and continuation assessment; guided_workflow_router consumes its result; delivery_workflow_domain owns observed trace audit. Reuse existing snapshot/journal, avoid a second state authority. Update manifest/public interfaces and generated affected domain/System views only if an interface changes. ALG-0003 and ALG-0004 cover deterministic routing/reconciliation refinements. No new runtime concurrency or performance claims; expected work scales with current decision records and observed events, to be verified without speculative speed claims.

Validation: red regression from original trace, lifecycle and adversarial false-final-reason tests, controlled new/existing-project model interactions, assembled distribution tests, formatter checks preserving existing style, architecture_cli.py release gate and independent Spec/Standards reviews. Static tests do not establish host UI enforcement.

Ambiguity assessment: shared all-project scope, mixed-answer handling, stopping conditions, presentation and authorization are settled by existing user constraints and observed failure. Internal implementation details are bounded to existing owners and do not require another user selection.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-10 | Record observed premature completion and proposed shared discussion contract. |
| 3 | 2026-09-10 | Recorded implementation PASS evidence. |
