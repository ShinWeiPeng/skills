---
spec_version: 1
spec_id: SPEC-0023
revision: 4
status: implemented
change_set: mode-preserving-decision-options
---

# Mode-preserving decision options

## Problem

The shared decision contract prefers structured choice tools even in execution mode. The user wants numbered replies in execution mode without switching to Plan mode.

## Solution

Make decision presentation depend on the existing collaboration mode across all projects. Preserve pending questions and explicit-answer requirements without a deadline.

## User Stories

As a user, I can finish reading options and reply with a number while remaining in my current mode.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | In Default/execution mode, present user decisions as numbered text options 1, 2, 3 as applicable, accepting numeric or clear free-form replies; do not switch to Plan mode to ask them. |
| REQ-002 | If already in Plan mode, remain there and use its available decision surface; do not force a switch to execution mode. |
| REQ-003 | Required decisions have no response deadline. Empty results, preselection, elapsed time and mode changes never resolve a question or authorize dependent execution. Persist questions before display and reconcile answers before the next decision. |
| REQ-004 | Apply this presentation rule to the shared plugin workflow for every project. Option selection remains distinct from exact execution authorization. |

| REQ-005 | Every SPEC revision, including editorial, evidence-only and no-semantic-delta reconfirmation, invalidates earlier execution authorization. Wait for a new explicit 開始執行 covering the revised SPEC before subsequent product operations. Read-only verification and SPEC persistence remain allowed. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Default mode uses numbered replies as the intended surface, not merely a fallback when structured tools are absent. |

## Discussion Context

### DISC-001: Existing-mode presentation

- **Situation:** The user reports unwanted transitions into Plan mode and losing time to read decision options.
- **Question:** How should decisions be presented in execution mode?
- **Options and tradeoffs:** Numbered text preserves execution-mode interaction; existing Plan-mode interaction remains available when already in that mode. This changes shared skill guidance, not host mode controls.
- **User answer:** 還有如果在執行模式需要使用者決定的選項使用1, 2, 3 回復，不必切到計畫模式。除非原本就在計畫模式。
- **Explicit rationale:** Avoid switching modes solely to display decision options.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, DEC-001.

### DISC-002: Every revision revokes prior authorization

- **Situation:** Earlier guidance retained authorization on reconfirmation without semantic delta.
- **Question:** Does every SPEC revision require a new execution instruction?
- **Options and tradeoffs:** Always requiring fresh authorization avoids ambiguity over revision meaning; even editorial revisions stop subsequent product operations.
- **User answer:** 就是只要SPEC有revise就必須要等待使用者下達開始執行；開始執行
- **Explicit rationale:** Any SPEC revision must wait for the user to authorize execution.
- **Resulting impact:** REQ-005, AC-004.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-004 | Shared workflow presents numbered options in Default mode without requesting a Plan-mode switch, accepting numeric and free-form replies. | Review shared contract, consumers and a controlled interaction trace. | PASS: shared contract and consumer review; controlled model Default scenario in SPEC-0023-interaction-review.md; 234 assembled tests. Not App UI playback. |
| AC-002 | REQ-002 | A decision originating in Plan mode preserves that mode. | Mode-specific scenario review. | PASS: controlled model existing-Plan scenario preserves surface/mode through timeout and numeric answer; SPEC-0023-interaction-review.md. |
| AC-003 | REQ-003, REQ-004 | Unanswered decisions stay pending without a deadline; answers reconcile into SPEC and do not independently grant product execution. | Pending-question recovery and authorization regression checks. | PASS: full 234-test suite includes pending-question recovery, numeric answers and non-authorizing choices; independent Spec and Standards reviews PASS. |

| AC-004 | REQ-005 | Reopen and reconfirm without semantic changes, editorial changes and evidence-only revisions reject the prior receipt and old event; fresh authorization permits delivery. Materialization never reports retained authority. | Integration tests through materialization and managed writes, plus contract review. | PASS: new lifecycle regression failed old code in all three variants, then full suite passed; old receipt/event blocked, targets unchanged, fresh authorization permits apply; no-delta materialization returns false retention. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | refines | SPEC-0020 |
| REQ-004 | refines | SPEC-0022 |
| REQ-005 | refines | SPEC-0022 |
| AC-004 | depends_on | REQ-005 |
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-002 |
| AC-003 | depends_on | REQ-003 |

## Out of Scope

Host UI timer or collaboration-mode implementation. Changing prior implemented specifications. Installation, commit and push are not part of this implementation request.

## Open Decisions

None.

## Routing/Gates

Spec review: PASS

User explicitly authorized this clarified change set with 開始執行 in the same message as REQ-005. Persist that clarification before executing. Any later revision invalidates this authorization, including recording final evidence; perform no subsequent product operations after such a revision without a new instruction. Intended implementation touches the shared decision contract, affected skill/document copies and focused validation. Higher-priority host tool constraints remain applicable; the plugin must not claim it controls host modes or UI timers.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-10 | Record user-selected all-project, mode-preserving decision presentation. |
| 2 | 2026-09-10 | Reopened before clarification: User requires fresh execution authorization after every SPEC revision and authorizes the clarified implementation in the same message. |
| 4 | 2026-09-10 | Recorded implementation PASS evidence. |
