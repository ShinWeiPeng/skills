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
resumes only with explicit evidence; invalid resume combinations block; existing
implementation, read-only, diagnosis, wayfinder, risk-gate, and execution-redecision
routes remain unchanged.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are the classified intent, three-state ProjectState, resolved spec context,
risk decision, capability set, completed stages, wayfinder signals, tracker
availability, unresolved-decision evidence, and optional
`resume_confirmed_spec: boolean` defaulting to `false`. ProjectState axes are
`present`, `absent`, or `indeterminate`; spec state is `none`, `ambiguous`, `working`,
`confirmed`, `implemented`, or `invalid`.

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
- All routing tests and the complete plugin regression suite must pass with zero
  failures.
- Intent matching remains `O(n*m)` for prompt length `n` and bounded term count `m`;
  workflow selection, including resume validation, remains `O(1)`.

## Candidate methods and comparative evidence

| Candidate | Determinism | Failure mode | Evidence |
|---|---|---|---|
| Explicit boolean resume evidence, default false | Exact and auditable | Invalid evidence blocks | Focused unit and CLI fixtures cover default, valid, and invalid states. |
| Infer continuity from prompt text | Model- and vocabulary-dependent | False resume or repeated interviews | Rejected because equivalent prompts cannot guarantee identical classification. |
| Auto-resume every unique confirmed spec | Exact but semantically incomplete | New work bypasses `grill-with-docs` | Reproduced by the `thesis-trace` Proxmox/VM case. |

A performance benchmark is not required: the selected method adds one boolean branch
to constant-time workflow selection and has no material resource uncertainty.

## Selected method and reasons for rejecting alternatives

Use an explicit optional `resume_confirmed_spec` boolean at the Python and CLI
boundaries, defaulting to `false`. Treat a resolved confirmed spec as durable context
only. With explicit resume evidence, verify and resume exactly one valid confirmed
spec; otherwise apply ProjectState interview precedence or fail closed.

Prompt inference is rejected because it is not deterministic or independently
auditable. Unconditional unique-spec resume is rejected because spec discovery does
not prove that a request continues the same change set.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. Preserve an explicit skill; otherwise classify hard intents in versioned order.
2. Resolve spec context by explicit path, tracker path, branch match, then unique
   confirmed fallback; never select the newest.
3. If resume evidence is true and spec state is not `confirmed`, return `BLOCKED`
   through `spec-governance`.
4. If resume evidence is true and the confirmed spec is not yet verified, select
   `spec-governance`; after `spec-verified`, resume the recorded target.
5. If resume evidence is false, a confirmed spec contributes only
   `stateful_context=present`; choose `grill-me`, `grill-with-docs`, or `grilling`
   from ProjectState.
6. Preserve diagnosis, read-only, risk-gate, wayfinder, capability, and
   execution-redecision precedence.

Ordered rules are the tie-breaker. Ambiguous or invalid evidence never falls back to
newest, model preference, or prompt similarity.

## Parameters, calibration, versioning, and compatibility

`resume_confirmed_spec` is the only new parameter. Its fixed default is `false`; it
has no calibration or threshold. The CLI spelling is `--resume-confirmed-spec`.
Adding the opt-in parameter is source-compatible for existing callers, while changing
the previous auto-resume behavior is recorded in the current pre-1.0 `0.5.0` minor
changeset.

## Time and space complexity and resource budgets

Workflow selection remains constant time over bounded state enums and capability
sets. The option adds no persistent state, allocation, I/O, network access, or
measurable workload budget. Intent classification remains `O(n*m)` and repository
evidence/spec resolution costs are owned by their upstream components.

## Errors, degradation, fallback, and forbidden behavior

Malformed rules or contracts are fatal. Resume evidence with none, ambiguous,
invalid, working, or implemented spec context returns `BLOCKED`. Missing
`grill-me` may degrade only to `grilling`; other missing required capabilities
remain blocked. A new discretionary execution decision returns to general grilling.

It is forbidden to infer resume evidence, auto-select the newest spec, bypass
ProjectState interviewing from discovery alone, bypass `spec-verified`, or downgrade
a required risk gate.

## Validation cases and evidence

`tests/test_guided_routing.py` covers empty, docs-only, confirmed-without-resume,
confirmed-with-resume, every invalid resume state, implementation-present,
read-only, diagnosis, wayfinder, risk-gate, execution-redecision, schema, and CLI
behavior. The complete plugin suite, integration validator, vendor lock check,
version governance, architecture development gate, and real `thesis-trace` route
provide regression and composition evidence.

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
