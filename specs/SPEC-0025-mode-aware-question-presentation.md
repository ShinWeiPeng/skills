---
spec_version: 1
spec_id: SPEC-0025
revision: 8
status: implemented
change_set: mode-aware-question-presentation
---

# Mode-aware question presentation

## Problem

Task 01a089f8-2a35-7893-b31c-311226ccb4a5 remained in Default mode but invoked request_user_input_async for Q-019 and Q-020 using plugin 0.12.0. Its host instructions prohibit textual multiple-choice questions. The plugin manifest still prefers structured choices, while the shared contract prefers numbered Default questions. finish-turn checks question persistence/presentation but not the selected mode/surface. Thus a passing completion did not establish the requested interaction behavior.

## Solution

Make the execution-mode prohibition the primary rule: Default mode must not invoke menu-producing question tools, including request_user_input_async and request_user_input when they produce choices. Apply this before tool selection, not only after presentation fails. Remove conflicting manifest/default-prompt instructions and enforce one shared mode-to-surface policy across every project and recovery path. Use numbered text when permitted, otherwise one concise open text question. Only an already-active Plan mode may select its permitted menu surface. Do not switch modes to bypass the rule. Failed-menu recovery and option-version maintenance remain supporting safeguards, not the primary fix.
## User Stories

As a user, I can discuss a decision in execution mode without an unexpected popup, and understand any host restriction before answering.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Remove the manifest's unconditional structured-choice preference and align shared contracts, direct consumers, docs and distributed artifacts around one presentation policy for all projects. |
| REQ-002 | Default/execution mode must not invoke any menu-producing question tool, including request_user_input_async or request_user_input used for choices, regardless of tool availability, structured-choice preference, missing numeric-text permission, presentation retry or request for alternatives. Use numbered text when higher-priority rules permit it; otherwise ask one concise open text question. Never switch modes or disguise choices to bypass restrictions. |
| REQ-003 | If already in Plan mode, preserve it and use a permitted available surface. Mode and host-policy evidence must come from actual current instructions, not an inference from an available tool or a visual menu. Unknown/conflicting evidence must not silently authorize a popup. |
| REQ-004 | Before selecting or invoking a question tool, a shared mode/surface preflight must return menu_allowed=false for Default or unknown mode. Inspect the result before any dependent call. Only already-active Plan with applicable host/tool permission can allow a menu. finish-turn and trace auditing must also reject a Default menu invocation even when the tool accepts it, the user can see it, or question content matches. No result grants product execution. |
| REQ-005 | Persist the actual question form and accept free-form replies without forcing an option number. Extend the current two-or-three-option question contract to support open text questions and recover them after interruption; legacy option questions remain readable and preserve identity/version. Re-presenting an old pending choice as open text must be an explicit recorded presentation transition, not a silently changed question. Preserve decisions, no response deadline, same-turn continuation and fresh execution authorization after every SPEC revision. |

| REQ-006 | Distinguish prepared reply, tool request accepted, observed emitted reply and user-reported presentation failure. accepted=true or an assistant-authored presentation file alone must not prove visible delivery. Default final text must contain the actual answerable question in the permitted form, not merely options-sent status. Before finalization validate the prepared reply against saved question state; after emission, trace evidence verifies the actual reply separately. Never claim the preflight proves the user saw it. |
| REQ-007 | On user reports such as options disappeared or cannot see, record presentation failure for the current question and surface in existing working state. Preserve the unanswered decision; immediately use a permitted durable text question in the same turn and do not automatically resend the failed popup. Clear failure only on explicit evidence of recovery or user-requested retry, subject to mode policy. Recovery feedback never counts as an answer. |
| REQ-008 | A request for other alternatives or any question/option content change goes through question revision before presentation. Keep question ID, increment its version, retain prior versions in history and reject stale question-version answers. Numeric replies must refer to the options of the currently presented persisted version; recover ambiguity without silently mapping to an old list. Persist all new alternatives before showing them; presentation repair does not bypass routing/reconciliation. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Proposed fallback is a single open text question when host rules forbid numbered questions. It preserves discussion and avoids the popup without overriding host instructions. |
| DEC-002 | Keep durable question state under existing spec_governance_domain; share mode/surface policy with the router and observed delivery auditor. No second state store or host policy modification. |

| DEC-003 | Treat execution-mode menu invocation itself as the defect. Prevention at tool selection is primary; disappearance recovery is secondary and cannot make a Default menu compliant. |

## Discussion Context

### DISC-001: Unexpected popup in execution mode

- **Situation:** The latest task used 0.12.0 and stayed in Default but displayed structured choices; manifest and completion checks were incomplete.
- **Question:** What repair addresses presentation mismatch within actual host constraints?
- **Options and tradeoffs:** Numbered text remains preferred where allowed. A concise open question avoids the popup under restrictive hosts but requires a textual answer. Forcing numbered choices would violate host instructions; retaining the popup would violate the user's requested interaction. The open question is the proposed compatible fallback.
- **User answer:** 為什麼在執行模式，最後仍跳出規劃模式的選單；提出修改方案
- **Explicit rationale:** No further rationale stated; existing preference is numbered execution-mode replies without switching modes.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, DEC-001, DEC-002.

### DISC-002: Popup-dependent apparent discussion stop

- **Situation:** Latest source rollout 2026-09-10T20-37-51 for task 01a089f8-2a35-7893-b31c-311226ccb4a5 recorded Q-023 at line 278, request_user_input_async at 283, accepted=true at 286, finish-turn PASS/await-answer at 291, and final reply at 294 saying options were sent without a standalone question. This differs from the earlier missing-reconciliation failure. Tool acceptance does not establish ongoing UI visibility.
- **Question:** Why does discussion appear stopped again despite the completion check?
- **Options and tradeoffs:** Popup-dependent waiting leaves the user without an actionable final question if the menu is unavailable. The proposed single-question Default fallback keeps the decision answerable in the conversation, while preserving the exact pending decision and avoiding invented answers.
- **User answer:** 最後又停止討論了
- **Explicit rationale:** No additional rationale stated.
- **Resulting impact:** REQ-002, REQ-004, REQ-005, AC-002, AC-003.

### DISC-003: Invisible popup and unsaved alternative

- **Situation:** In the latest task rollout, the user reported 選項不見了 (line 301), the assistant resent request_user_input_async (303) and said to check the card (309). After 沒看到 (316), it asked a text question (321). After the user requested other alternatives (328), it displayed three choices (333) without tools. Read-only verification found the saved Q-023 still at version 46 with two options. The third option therefore had no persisted answer mapping.
- **Question:** How should invisible presentation and new alternatives be repaired?
- **Options and tradeoffs:** Repeated popup requests do not establish usability. Recording failed presentation and returning to permitted text preserves an answerable conversation. Versioned question revision adds journal and compatibility work but prevents selecting from an unseen or obsolete option list.
- **User answer:** Selected the explanation of accepted=true being mistaken for effective presentation and requested 提出修改方案.
- **Explicit rationale:** No additional rationale stated.
- **Resulting impact:** REQ-006, REQ-007, REQ-008, AC-006, AC-007, AC-008.

### DISC-004: Correct the primary defect

- **Situation:** Previous proposal emphasized recovering a disappeared menu, although the user wanted execution mode to avoid menus in the first place.
- **Question:** What must be the primary correction?
- **Options and tradeoffs:** Shared pre-call denial plus consistent entry guidance directly addresses the wrong tool selection. Recovery-only changes would still permit the prohibited popup. Plain open questions preserve discussion under host restrictions but may require more typing than numeric choices.
- **User answer:** 我認為錯誤地方是為什麼還是使用選單；提出修改方案
- **Explicit rationale:** The error is still using a menu in execution mode.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, DEC-003, AC-002, AC-003.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Source manifest, assembled artifact and all direct question consumers contain no conflicting unconditional preference for structured choices. | Distribution-wide policy consistency tests and source/manifest review. | PASS: source/distributed prompts, shared/direct contracts and docs synchronized; distribution/review. |
| AC-002 | REQ-002, REQ-003 | Default with numbered permission uses text; restrictive Default uses one open question and no popup; existing Plan retains a permitted surface; unknown mode never silently selects popup. | Policy matrix tests and controlled model traces using actual host constraints. | PASS: mode/host matrix and controlled new/existing Default model cases; no human UI claim. |
| AC-003 | REQ-004 | Default with either available choice tool must deny menu invocation before the call, including retries and alternative requests. A bypassed call fails trace/finish checks even if visible and accepted=true. Plan allows only permitted available menus; unknown mode never permits one. A tool exposing a no-options variant is not an automatic Default fallback. | Mode/tool matrix, pre-call denial tests and controlled actual tool-trace review. | PASS: pre-call denial and forbidden accepted-call replay; finish/audit and Plan/unknown matrix. |
| AC-004 | REQ-005 | Open text questions persist, recover and reconcile explicit answers; old choice records remain readable. Surface transition is recorded and stale presentation evidence fails. Timeout keeps the question pending; selection never authorizes product work. | Migration/recovery lifecycle and authorization regressions. | PASS: open/legacy recovery, versioned transition, explicit free-form answer and authorization regressions. |
| AC-005 | REQ-001, REQ-004, REQ-005 | New and existing project scenarios pass shared workflow checks and assembled distribution validations, without claiming host-wide tool interception. | Plugin tests, architecture gate, independent Spec/Standards review and model-trace evidence audit. | PASS: 262 tests; architecture release, distribution, artifact and version checks; Spec/Standards reviews and controlled traces. |

| AC-006 | REQ-006 | accepted=true plus a prepared presentation file plus a final reply containing only options-sent cannot count as delivered/answerable discussion. Preflight checks the actual prepared text, question identity/version and permitted surface; observed final content is checked separately and never described as proof of user reading. | Exact reported trace negative fixture and rendered-reply evidence tests. | PASS: prepared/emitted separation, options-sent negative case and actual emitted agent-reply audit. |
| AC-007 | REQ-007 | After cannot-see feedback, no automatic same-popup retry occurs; same unresolved decision survives and a permitted text question is asked in that turn. Restart preserves the failed-surface record; feedback is never recorded as a design answer. | Stateful feedback/recovery and restart tests, controlled model scenario. | PASS: durable failure, protected history, explicit retry policy and existing-project model recovery. |
| AC-008 | REQ-008 | Expanding two options to three first persists the new question version and third alternative. Numeric 3 resolves only against that presented version; stale old-version replies and display-without-persistence fail. | Question revision, stale-answer, journal and trace regressions using Q-023 scenario. | PASS: two-to-three history, current numeric answer, stale rejection and unpersisted third-option trace rejection. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-002 | refines | SPEC-0023 |
| REQ-004 | refines | SPEC-0024 |
| REQ-006 | refines | SPEC-0024 |
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-002 |
| AC-003 | depends_on | REQ-004 |
| AC-004 | depends_on | REQ-005 |
| AC-005 | depends_on | REQ-001 |
| AC-006 | depends_on | REQ-006 |
| AC-007 | depends_on | REQ-007 |
| AC-008 | depends_on | REQ-008 |

## Out of Scope

Changing host/developer instructions, host UI code, unrelated project source, arbitrary tool interception, installation, commit or push during proposal preparation. No guarantee of numbered multiple choice where higher-priority instructions prohibit it.

## Open Decisions

None.

## Routing/Gates

Implementation authorized by the current root user 開始執行 covering revision 7 (original rollout line 3297). Product work and checks are complete before this final lifecycle evidence update. Primary delivery order: remove conflicting manifest/entry prompts, implement shared pre-call mode policy, wire all question paths and recovery through it, then add completion/audit checks. Popup failure recovery is supporting scope. No host-wide interception is claimed; the managed preflight and independently checked observed traces must not be described as disabling arbitrary host tools. Expected files: plugin manifest/default prompts, shared question contract and skill/docs consumers, spec_contract pending question representation/validation/CLI and completion policy, router presentation context, managed trace auditor, affected tests and release metadata. Legacy records need backward compatibility; no silent pending-state rewrite. Extend the existing question/journal schema for surface failure and versioned revisions, without a second state store. Preflight and post-emission evidence are distinct: a draft can be checked for completeness but cannot attest that the user saw the UI. Final response source references/content must be correlated by the trace reviewer. No automatic retry of a failed Default popup.

Architecture impact: existing spec_governance_domain owns question representation and deterministic presentation policy, guided_workflow_router consumes it, delivery_workflow_domain audits observations. Update manifest/public interfaces and generated views for changed contracts. ALG-0003/0004 describe policy selection and question reconciliation. No new concurrency or performance claims. Validate with the single architecture_cli.py gate and independent review.

Ambiguity assessment: all-project scope, no unexpected Default popup, host precedence, no deadline and execution boundary are settled. Open-text fallback is the explicit recommended proposal under the observed host restriction; it is not represented as a previously adopted user answer. Implementation details remain within these requirements.

Spec review: PASS. Independent Spec /root/spec25_review and Standards /root/spec25_standards reviews passed after corrections. Full suite: 262 tests PASS. Distribution, clean artifact, version metadata and architecture release checks PASS. Detailed local evidence: spec-governance/SPEC-0025-validation.md. New/existing controlled model cases used actual Default host restrictions and parent-agent test replies; no human UI visibility or host-wide interception claim. Installation, commit and push were not performed. Local evidence stays excluded from commit.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-10 | Record mode/surface mismatch, host constraint and proposed repair. |
| 2 | 2026-09-10 | Reopened before clarification: Record latest observed Q-023 popup-dependent wait and missing actionable final question. |
| 4 | 2026-09-10 | Reopened before clarification: Extend proposal with reported invisible-choice recovery and unpersisted option expansion. |
| 6 | 2026-09-10 | Reopened before clarification: User corrects primary fault: execution mode must not invoke menu tools at all. |
| 8 | 2026-09-10 | Recorded implementation PASS evidence. |
