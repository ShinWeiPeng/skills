---
spec_version: 1
spec_id: SPEC-0008
revision: 4
status: implemented
change_set: turn-boundary-grilling-handoff
---

# Turn-boundary grilling handoff

## Problem

A read-only code-understanding conversation can correctly begin in
`explain-code-flow`, then drift into decisions about future repository behavior
without returning to the authoritative router. The downstream skill may continue
asking design questions that resemble grilling while omitting the required
`grilling` handoff and per-answer `spec-governance.reconcile` evidence.

The router already supports `has_unresolved_decision` and the CLI
`--unresolved-decision`, but the cross-skill responsibility to set that signal before
the first design question is not explicit or regression-tested.

## Solution

Define a mandatory turn-boundary rerouting contract. Reassess every user turn, and
before any active skill asks a repository-modifying design or specification
question, rerun the guided router with `has_unresolved_decision=true`. The current
skill must stop leading when the authoritative result selects `grilling`.

Keep read-only factual follow-ups in `explain-code-flow`. Let
`clarify-improvement-proposals` maintain the ambiguity ledger and synthesize the
proposal, while routing repository-modifying decisions through `grilling` and
reconciling every answer into the working specification.

## User Stories

- As a developer asking for a code explanation, I can continue factual follow-ups
  without being forced into a change-set interview.
- As a developer who begins choosing a future implementation during an explanation,
  I receive the governed grilling and specification workflow before any decision is
  treated as settled.
- As a plugin maintainer, I can detect regressions with a multi-turn fixture that
  reproduces explanation-to-design intent drift.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Pure read-only code-understanding requests and factual follow-ups MUST remain owned by `explain-code-flow`. |
| REQ-002 | Every user turn MUST be reassessed. `has_unresolved_decision` MUST be true if and only if an unresolved user decision is not discoverable from repository facts and affects the change set's implementation behavior, interface, persistent parameter, failure policy, specification scope, or acceptance threshold. It MUST become true before the first such question, remain true for short or numeric answers through reconciliation, and become false only when no open decisions remain. |
| REQ-003 | When the authoritative route selects `grilling`, the previously active skill MUST stop leading; `grilling` MUST ask one decision at a time and each answer MUST resume at `spec-governance`, pass through `spec-governance.reconcile`, and reroute only after reconciliation establishes whether another open decision remains. |
| REQ-004 | `clarify-improvement-proposals` MAY own discovery, the ambiguity ledger, comparison, and final proposal synthesis, but MUST NOT independently own repository-modifying decision questions. |
| REQ-005 | The change MUST reuse the existing `has_unresolved_decision` Python option and `--unresolved-decision` CLI flag, document its classifier and lifecycle in the guided routing schema, return a design/specification-neutral reason and `resume_target=spec-governance`, and MUST NOT add persistent conversation state or change the existing public callable or CLI spelling. |
| REQ-006 | Architecture descriptions, ALG-0003, generated views, skill contracts, integration contracts, and release changeset metadata MUST describe the same handoff behavior. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Select a mandatory turn-boundary handoff using the existing unresolved-decision signal instead of a documentation-only reminder or a new persistent conversation-state API. |
| DEC-002 | Trigger the handoff before the first repository-modifying decision question, not after the user answers it. |
| DEC-003 | Preserve repository-wide ProjectState semantics: existing repositories use `grilling`; only `implementation=absent` and `stateful_context=absent` use `grill-me`. |
| DEC-004 | Treat this as conformance with accepted ADR-0010 and an extension of ALG-0003, without creating a new ADR or Algorithm Design Record. |
| DEC-005 | Define `has_unresolved_decision` as caller-supplied lifecycle evidence for an unresolved, non-discoverable, change-set-shaping choice; use `spec-governance` as the immediate resume target because reconciliation, not execution, follows each grilling answer. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003 | A multi-turn ODR fixture starts in `explain-code-flow`, switches to `grilling` before the first design choice, keeps a numeric reply such as `1` inside the change-set interview, resumes at `spec-governance`, and clears the signal only after decisions are complete. | Focused guided-routing unit tests and skill-contract tests. | PASS — `test_read_only_odr_flow_hands_off_before_design_choice`, `test_decision_complete_clears_signal_and_restores_normal_routing`, and the real CLI unresolved-decision fixture verify the complete lifecycle and `spec-governance` resume target. |
| AC-002 | REQ-001 | A factual follow-up about the same code Flow remains read-only and does not select `grilling`. | Guided-routing regression tests. | PASS — `test_factual_odr_follow_up_remains_code_understanding` and the decision-complete fixture select `explain-code-flow`. |
| AC-003 | REQ-002, REQ-003, REQ-004, REQ-005 | `ask-matt`, `explain-code-flow`, and `clarify-improvement-proposals` expose the same mandatory handoff classifier and lifecycle, while the schema declares the existing option and the Python/CLI signatures remain compatible. | Text-contract tests, schema assertions, and CLI fixture. | PASS — skill-contract tests verify the iff classifier, numeric-answer retention, clearing rule, and resume target; schema and CLI fixtures verify the unchanged public option and flag. |
| AC-004 | REQ-006 | Manifest, ALG-0003, deterministic Description Views, integration validation, version governance, and the development architecture gate all pass. | Repository validation commands with exit codes and generated-view comparison. | PASS — integration validates 28 skills, version and vendor governance pass, and the schema 2.2.0 development gate exits `0` with generated views byte-current. |
| AC-005 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 | The complete plugin test suite passes with zero failures and no unrelated behavior change. | Full unittest discovery and diff review. | PASS — 134 root tests, 3 proposal tests, 10 diagnosis tests, 13 explanation tests, 104 architecture-skill tests, and 67 device-validation tests pass; diff review finds no old execution-only reason or resume target, API rename, persistent state, version bump, or release action. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-002 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-002 |
| REQ-005 | depends_on | DEC-001 |
| REQ-006 | depends_on | DEC-004 |
| REQ-002 | depends_on | DEC-005 |
| REQ-003 | depends_on | DEC-005 |
| REQ-005 | depends_on | DEC-005 |

## Out of Scope

- Adding persistent conversation state, a conversation database, or a new router
  service.
- Changing ProjectState classification or the `grill-me` greenfield boundary.
- Changing pure read-only routing precedence.
- Implementing a new workflow-selection algorithm or renaming the existing Python
  and CLI unresolved-decision inputs.
- Releasing or publishing a new plugin version.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user selected the mandatory handoff option.
- Spec reconciliation: PASS — all requirements, decisions, and acceptance criteria
  have stable IDs, explicit relations, no conflicts, and no open decisions.
- Architecture impact: the existing `governed-engineering-route` and
  `governed-change-set-lifecycle` Flows gain explicit turn-boundary handoff semantics;
  module boundaries, Ports, Events, types, state, execution units, and dependencies
  remain unchanged.
- Algorithm screening: ALG-0003 remains the owner because the change refines its
  deterministic workflow-selection inputs and transition behavior.
- Flow-cost review: estimated PASS — the selected option adds one existing
  synchronous reroute at a design boundary, with no runtime Task, Queue, allocation,
  I/O, or performance claim.
- Spec verification: PASS — revision 4 satisfies strict structure and complete
  REQ → AC traceability with no open decisions or scope creep.
- Implementation authorization: PASS — the user supplied the exact
  `開始執行` authorization.
- Architecture authoring gate: PASS — design and development gates exit `0`;
  generated Description Views are deterministic and current.
- Code review Standards axis: PASS — the change preserves module, Port, Type, State,
  dependency, CLI, and callable boundaries; manifest, ALG, views, patch changeset,
  release intent, and vendor fingerprints are synchronized.
- Code review Spec axis: PASS — the router, schema, three skill contracts, tests, and
  governance artifacts implement all six requirements without scope creep.
- Spec review: PASS — all six requirements and five acceptance criteria are
  implemented and verified.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-05 | Materialized the authorized turn-boundary grilling handoff contract. |
| 2 | 2026-08-05 | Recorded implementation, deterministic routing fixtures, governance gates, and complete validation evidence. |
| 3 | 2026-08-05 | Defined the unresolved-decision classifier and lifecycle, selected `spec-governance` as the immediate resume target, and reopened implementation evidence. |
| 4 | 2026-08-05 | Recorded the corrected router behavior, synchronized contracts and architecture views, and complete validation evidence. |
