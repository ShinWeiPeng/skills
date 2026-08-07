# ALG-0003: Ordered intent and workflow selection

## Metadata

- Status: proposed
- Owner module: `workflow_routing_domain`
- Product feature: Automatic authoritative engineering handoff
- Flow IDs: `governed-engineering-route`
- Related ADRs: `ADR-0010`, `ADR-0011`
- Source paths:
  - `skills/engineering-risk-routing/references/intent-rules.json`
  - `skills/engineering-risk-routing/references/guided-routing-contract.schema.json`
  - `skills/engineering-risk-routing/scripts/workflow_selection.py`
  - `skills/engineering-risk-routing/scripts/guided_workflow_router.py`
- Test and benchmark paths: `tests/test_guided_routing.py`
- Supersedes: none

## Problem and observable success

Select the safe primary engineering workflow without letting risk gates replace user
intent, spec discovery imply change-set continuity, or model judgment guess ambiguous
states. Identical versioned inputs must produce the same `GuidedRouteDecision`.

Observable success is exact route equality for the fixture matrix: empty repositories
select `grill-me`; docs-only repositories select `grill-with-docs`; a confirmed spec
resumes only with explicit evidence; invalid resume combinations block; read-only
follow-ups remain in their active explanation Flow; and a downstream skill preparing
the first repository-modifying decision reroutes to `grilling` before asking it.
Existing diagnosis, wayfinder, risk-gate, and execution-redecision routes remain
unchanged.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are the classified intent, three-state ProjectState, resolved spec context,
risk decision, capability set, completed stages, wayfinder signals, tracker
availability, caller-supplied unresolved-decision evidence, and optional
`resume_confirmed_spec: boolean` defaulting to `false`. ProjectState axes are
`present`, `absent`, or `indeterminate`; spec state is `none`, `ambiguous`, `working`,
`confirmed`, `implemented`, or `invalid`.

`has_unresolved_decision` is true if and only if an unresolved user choice is not
discoverable from repository facts and affects the change set's implementation
behavior, interface, persistent parameter, failure policy, specification scope, or
acceptance threshold. It becomes true before the first such question, remains true
for short or numeric answers through reconciliation, and becomes false only when no
open decisions remain.

The output is one `GuidedRouteDecision` with `PASS`, `DEGRADED`, or `BLOCKED` status
and an authoritative selected skill or explicit absence. Repository evidence,
canonical spec resolution, and caller-supplied resume evidence are assumed to have
passed their own structural validation. The router never infers resume evidence from
prompt wording.

## Constraints and quantitative acceptance thresholds

- Every versioned routing fixture must produce the exact expected status, selected
  skill, fallback, and resume target; tolerated mismatches: zero.
- `resume_confirmed_spec=false` must never bypass ProjectState interview precedence.
- `resume_confirmed_spec=true` requires exactly one valid `confirmed` spec; every
  other spec state must return `BLOCKED`.
- A `working` canonical spec always returns `BLOCKED` through `spec-governance`,
  even when completed stages contain evidence from its prior confirmed revision.
- All routing tests and the complete plugin regression suite must pass with zero
  failures.
- A multi-turn fixture must preserve a pure read-only follow-up and must reroute a
  numeric answer to a pending design question through `grilling`, with
  `resume_target=spec-governance`; tolerated transition mismatches: zero.
- Intent matching remains `O(n*m)` for prompt length `n` and bounded term count `m`;
  workflow selection, including resume validation, remains `O(1)`.

## Candidate methods and comparative evidence

| Candidate | Determinism | Failure mode | Evidence |
|---|---|---|---|
| Explicit boolean resume evidence, default false | Exact and auditable | Invalid evidence blocks | Focused unit and CLI fixtures cover default, valid, and invalid states. |
| Reuse unresolved-decision evidence at every turn boundary | Exact, compatible, and auditable | A caller that omits the signal violates the cross-skill contract | Multi-turn and skill-contract fixtures cover explanation retention and pre-question handoff. |
| Documentation-only reminder without mandatory rerouting | No deterministic handoff | The active skill can continue an ungoverned design interview | Rejected because it reproduces the observed explanation-to-design drift. |
| Persistent conversation-state router API | Exact but introduces new state ownership and migration | Stale or ambiguously owned conversation state | Rejected because the existing boolean already represents the required decision boundary. |
| Infer continuity from prompt text | Model- and vocabulary-dependent | False resume or repeated interviews | Rejected because equivalent prompts cannot guarantee identical classification. |
| Auto-resume every unique confirmed spec | Exact but semantically incomplete | New work bypasses `grill-with-docs` | Reproduced by the `thesis-trace` Proxmox/VM case. |

A performance benchmark is not required: the selected method adds one boolean branch
to constant-time workflow selection and has no material resource uncertainty.

## Selected method and reasons for rejecting alternatives

Use the existing caller-supplied `has_unresolved_decision` boolean at every user turn
and before an active skill presents the first repository-modifying design or
specification question. When true, select `grilling` before lexical intent or a short
numeric reply can retain the previous read-only workflow and set the immediate resume
target to `spec-governance`. Keep the existing optional
`resume_confirmed_spec` boolean at the Python and CLI boundaries, defaulting to
`false`. Treat a resolved confirmed spec as durable context only. With explicit
resume evidence, verify and resume exactly one valid confirmed spec; otherwise apply
ProjectState interview precedence or fail closed. A reopened `working` canonical
spec routes to `spec-governance` with `grilling` as its resume target until it is
confirmed again.

Prompt inference is rejected because it is not deterministic or independently
auditable. Unconditional unique-spec resume is rejected because spec discovery does
not prove that a request continues the same change set.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. At each user turn, and before a downstream skill asks a repository-modifying
   decision, rerun the authoritative router.
2. Set caller-supplied unresolved-decision evidence true exactly while an unresolved,
   non-discoverable user choice affects implementation behavior, an interface, a
   persistent parameter, failure policy, specification scope, or an acceptance
   threshold.
3. If unresolved-decision evidence is true, select `grilling` with
   `resume_target=spec-governance`; the previously active skill stops leading and
   the signal remains true for short or numeric answers until reconciliation proves
   no open decision remains.
4. Preserve an explicit skill for all other requests; otherwise classify hard
   intents in versioned order.
5. Resolve spec context by explicit path, tracker path, branch match, then unique
   confirmed fallback; never select the newest.
6. If resume evidence is true and spec state is not `confirmed`, return `BLOCKED`
   through `spec-governance`.
7. If spec state is `working`, return `BLOCKED` through `spec-governance` with
   `resume_target=grilling`, regardless of prior completed stages.
8. If resume evidence is true and the confirmed spec is not yet verified, select
   `spec-governance`; after `spec-verified`, resume the recorded target.
9. If resume evidence is false, a confirmed spec contributes only
   `stateful_context=present`; choose `grill-me`, `grill-with-docs`, or `grilling`
   from ProjectState.
10. Preserve diagnosis, read-only, risk-gate, wayfinder, capability, and
   execution-redecision precedence.

Ordered rules are the tie-breaker. Ambiguous or invalid evidence never falls back to
newest, model preference, or prompt similarity.

## Parameters, calibration, versioning, and compatibility

No new parameter is introduced by the turn-boundary handoff.
`has_unresolved_decision` and CLI `--unresolved-decision` retain their existing
spelling and boolean type. Their documented semantics are narrowed to the exact
classifier and lifecycle above without changing the public callable or CLI.
`resume_confirmed_spec` retains its fixed default of `false` and CLI spelling
`--resume-confirmed-spec`.

## Time and space complexity and resource budgets

Workflow selection remains constant time over bounded state enums and capability
sets. The turn-boundary handoff reuses one synchronous route and adds no persistent
state, allocation, runtime Task, Queue, I/O, network access, or measurable workload
budget. Intent classification remains `O(n*m)` and repository evidence/spec
resolution costs are owned by their upstream components.

## Errors, degradation, fallback, and forbidden behavior

Malformed rules or contracts are fatal. A downstream skill asking a
repository-modifying decision without first rerouting with unresolved-decision
evidence is a contract violation. Clearing the signal while an open decision remains
or retaining it after reconciliation proves decision-complete is also a contract
violation. Resume evidence with none, ambiguous,
invalid, working, or implemented spec context returns `BLOCKED`. Missing
`grill-me` may degrade only to `grilling`; other missing required capabilities
remain blocked. A new discretionary decision returns to general grilling, and its
answer returns immediately to `spec-governance` rather than execution.

A reopened `working` spec remains blocked even if old completed-stage evidence
contains `grilling` and `spec-verified`.

It is forbidden to infer resume evidence, auto-select the newest spec, bypass
ProjectState interviewing from discovery alone, bypass `spec-verified`, or downgrade
a required risk gate.

## Validation cases and evidence

`tests/test_guided_routing.py` covers empty, docs-only, confirmed-without-resume,
confirmed-with-resume, every invalid resume state, implementation-present,
read-only, diagnosis, wayfinder, risk-gate, execution-redecision, schema, CLI, and
the explanation-to-design multi-turn transition. Skill-contract tests require
`ask-matt`, `explain-code-flow`, and `clarify-improvement-proposals` to expose the
same handoff rule. The complete plugin suite, integration validator, vendor lock
check, version governance, architecture development gate, and real `thesis-trace`
route provide regression and composition evidence.

Pass requires zero test failures, zero contract mismatch, architecture exit `0`, and
the real case output `implementation=absent`, `stateful_context=present`,
`selected_skill=grill-with-docs`.

## Risks and monitoring

- A caller may set resume evidence without proving semantic continuity. Mitigation:
  the skill contract restricts the flag to explicit no-new-decision requests, and
  execution redecision returns to grilling.
- Existing integrations may have relied on auto-resume. Mitigation: default false is
  deliberate fail-safe behavior and the changeset documents it.
- Documentation may drift from routing code. Mitigation: contract tests, generated
  Description Views, vendor fingerprints, and architecture gates run in the release
  validation matrix.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
