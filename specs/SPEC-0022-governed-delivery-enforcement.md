---
spec_version: 1
spec_id: SPEC-0022
revision: 4
status: implemented
change_set: governed-delivery-enforcement
---

# Governed delivery enforcement proposal

## Problem

User confirms 0.11.0. Task 01a08922-5806-7ba2-a090-2eff34ebe2da ignored false execution authorization, composed router and unconditional apply_patch, omitted admission, and later stopped SPEC maintenance after a stop-product instruction.

## Solution

Propose plugin-only repair: distinguish discussion persistence from execution; bind authorization to task and contract; separate routing success from write permission; managed patch admission; sequential gate inspection; real assistant trace validation. Apply the shared discussion lifecycle across all projects using the plugin, independent of repository, language, framework, domain or example terminology. No per-project rule installation or user reminder is required. Existing project specifications remain isolated. No host-interception guarantee.

## User Stories

As a user, I need accepted discussion persisted before separately authorizing product edits.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Continue SPEC reconciliation during product suspension unless user explicitly stops SPEC or all work. |
| REQ-002 | Suspend prior authorization on contract change or user stop; require fresh exact execution evidence bound to the current task and contract. |
| REQ-003 | Managed edits must check admission before mutation; route PASS is not write permission; inspect gate results before dependent operations. |
| REQ-004 | Validate actual assistant tool traces, preserve no-timeout questions, and report direct bypass as failure rather than claiming host enforcement. |

| REQ-005 | Apply the shared workflow to every engineering project, including new and existing projects and later discussion after implementation; never key behavior to Uptime, a firmware project or particular task. Pure factual questions remain read-only; requirement and decision changes persist in the current project SPEC before dependent implementation. |
| REQ-006 | Keep specification identity and execution authorization isolated by project, task and change set; no authorization may leak across projects. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Carry forward the previously adopted plugin-only scope; implementation adopted by the current explicit execution instruction. |

| DEC-002 | Define a universal plugin discussion lifecycle; use the reported Uptime exchange only as one regression example. |

## Discussion Context

### DISC-001: Version and proposal

- **Situation:** Known governance rules were bypassed.
- **Question:** What repair addresses this failure?
- **Options and tradeoffs:** Managed workflow improves consistency; arbitrary tool interception requires host capability outside the accepted scope.
- **User answer:** 確定版本是0.11.0；提出修改方案。
- **Explicit rationale:** No additional rationale stated.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, DEC-001.

### DISC-002: All-project scope

- **Situation:** A proposal acceptance example named Uptime from the reported firmware project.
- **Question:** Is the workflow specific to that project?
- **Options and tradeoffs:** Shared plugin behavior applies consistently across projects; project-specific fixes would leave the same failure elsewhere.
- **User answer:** 這不是針對某個專案，而是要符合全部專案的討論流程
- **Explicit rationale:** The discussion workflow must apply to all projects.
- **Resulting impact:** REQ-001, REQ-005, REQ-006, DEC-002, AC-001, AC-004.

### DISC-003: Execution authorization

- **Situation:** All-project scope clarified.
- **Question:** Proceed with the shared workflow repair?
- **Options and tradeoffs:** Adopt plugin-only repair with documented host boundary.
- **User answer:** 開始執行
- **Explicit rationale:** No additional rationale stated.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, AC-001, AC-002, AC-003, AC-004.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-004 | During discussion without execution authorization, accepting or changing a requirement updates SPEC and leaves product files unchanged; the same holds after a stop-product instruction, without a response deadline. | Real conversation replay, journal and target hashes. | PASS: controlled four-project model replay, no-deadline recovery and pause/adoption journal/product hash evidence; SPEC-0022-review/extended-spec-review.md. |
| AC-002 | REQ-002, REQ-003 | Missing/stale/suspended authorization or route to grilling cannot execute a managed patch. | Negative lifecycle integration and tool-order assertions. | PASS: absent, stale, suspended, repeated-event and route-only permission cases; 232-test suite and 15 final focused tests. |
| AC-003 | REQ-003, REQ-004 | Current authorization permits managed patch; direct bypass is reported as a workflow failure. | Managed patch positive/negative tests and fresh-task trace audit. | PASS: controlled managed writes and observed isolated direct-write audit FAIL; protected target/hash invariants; Standards follow-up PASS. |

| AC-004 | REQ-005, REQ-006 | Run the same discussion, adoption, pause, contract-change and fresh-authorization scenarios in new and existing projects across firmware, Web and Python fixtures; swapping project/task references must never permit writes. No project-specific reminder or Uptime keyword is needed. | Parameterized lifecycle fixtures and fresh-task tool-trace replays with per-project file hashes and journals. | PASS: new/no-source, C++, JavaScript and Python controlled model lifecycle matrix plus automated project/task isolation; synthetic test authorization only. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-002 |
| AC-003 | depends_on | REQ-003 |
| REQ-002 | refines | SPEC-0020 |
| AC-004 | depends_on | REQ-005 |
| AC-004 | depends_on | REQ-006 |

## Out of Scope

Product implementation, firmware modification, Git writes, installation and publication during proposal preparation. Arbitrary host interception.

## Open Decisions

None.

## Routing/Gates

- Spec review: PASS

Execution authorized by user 開始執行. Design: local receipt bound to resolved project root, task, canonical hash and working journal fingerprint; suspension revokes product execution while SPEC discussion continues. Single-file JSON patch with expected prior SHA-256, bounded content and atomic replacement, rejecting symlinks and governance-control paths. Source event IDs are caller-supplied and cannot authenticate human input; replay is rejected within retained local history. A trace auditor detects observed bypass without claiming host enforcement. Existing spec module owns state; delivery module would own managed patch admission; router would expose unambiguous permission fields. Architecture and tests are included in the authorized implementation.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-10 | Record version correction, evidence and proposed repair. |
| 2 | 2026-09-10 | Record all-project discussion scope and cross-project isolation acceptance. |
| 3 | 2026-09-10 | Accept execution and bounded managed-write design. |
| 4 | 2026-09-10 | Recorded implementation PASS evidence. |
