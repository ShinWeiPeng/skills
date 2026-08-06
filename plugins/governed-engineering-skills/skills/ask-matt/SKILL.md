---
name: ask-matt
description: Automatically route every software-engineering request, including implementation, modification, debugging, review, code explanation, tests, architecture, and deployment. Model-invoked; users never need to name this skill.
---

# Automatic Engineering Router

Use this skill automatically whenever the user's intent is software engineering.
The user describes the work; never require them to know or invoke `ask-matt`.
Standalone notes and non-engineering writing remain outside this router.

Before any governed engineering workflow asks the user to choose a design or
specification outcome, read and enforce
[the shared Decision Question Contract](references/decision-question-contract.md).
The contract applies to explicit downstream skills as well as inferred routes.

## Ordered route

Use this fixed precedence:

```text
explicit skill
→ ordered hard intent
→ three-state ProjectState
→ active SpecContext
→ R0–R3 required gates
→ capability check
→ authoritative handoff
```

1. Read the repository and task context without mutation. Discover Git and filesystem
   facts instead of asking the user.
2. Run `scripts/guided_workflow_router.py` from the
   `engineering-risk-routing` skill, or apply its contracts exactly when the runtime
   cannot execute the script.
3. Treat `GuidedRouteDecision.selected_skill` as authoritative.
   `RoutingDecision.next_skill` is only a risk advisory.
4. Hand off to the selected skill automatically. Do not ask the user to invoke it.
5. Stop on `BLOCKED`. Continue transparently on `DEGRADED` only when the decision
   names an equivalent primitive.

## Turn-boundary rerouting

Reassess every user turn through the authoritative router. A short reply such as a
numbered choice inherits a pending governed decision; do not classify it in
isolation and let the previously active skill retain control.

Set `has_unresolved_decision=true` if and only if an unresolved user decision is not
discoverable from repository facts and affects the change set's implementation
behavior, interface, persistent parameter, failure policy, specification scope, or
acceptance threshold. Set it before the first such question, preserve it for short
or numeric answers through reconciliation, and clear it only when
`spec-governance.reconcile` reports no open decisions.

Before any active skill presents such a repository-modifying question, rerun the router with
`has_unresolved_decision=true` (CLI `--unresolved-decision`). Do this before showing
the options, not after the user answers. When
`GuidedRouteDecision.selected_skill=grilling`, the active skill stops leading and
hands off automatically. The route must name `spec-governance` as the immediate
resume target.

Keep factual, read-only follow-ups in their existing diagnosis, review, or
code-understanding flow. Once `grilling` owns a change set, reconcile every answer
through `spec-governance.reconcile` before asking the next decision, then return to
the recorded supporting or proposal workflow only after the interview is
decision-complete.

## ProjectState

Assess both axes independently as `present`, `absent`, or `indeterminate`:

- `implementation`: product source or tests provide strong implementation evidence.
- `stateful_context`: formal context such as `CONTEXT.md`, a spec, PRD, ADR, or
  architecture manifest provides durable project knowledge. Empty formal-context
  files are `indeterminate`, not present.

Scan tracked files and non-ignored untracked files. Exclude Git metadata, ignored
dependencies, caches, build output, and generated artifacts.

Route modifying work as follows:

- `absent / absent` → `grill-me`
- implementation absent and stateful context present → `grill-with-docs`
- implementation present → intent-specific exploration, then `grilling`
- either axis indeterminate → show the evidence and use `grilling` to ask exactly one
  conclusion-changing question; never guess

A resolved confirmed specification proves durable context, not that the current
request continues the same change set. New or specification-changing work still
follows the ProjectState interview route. Set `resume_confirmed_spec=true` only when
the user explicitly asks to execute or continue the selected confirmed spec and the
request introduces no new decision or conflict; every other combination fails closed.

A README, template, empty scaffold, or empty formal-context file alone is not proof
of a codebase or durable project knowledge.

## Change-set interview contract

Every repository-modifying change set completes grilling before mutation, regardless
of size or an explicitly requested skill such as `tdd`.

- Interview the whole change set once. Source, tests, docs, migrations, generated
  views, versions, and changelog entries required by that change do not restart it.
- A bug may complete read-only diagnosis first. Choosing the fix then requires
  grilling.
- Ask one decision question at a time under the shared Decision Question Contract.
- Do not ask discoverable facts.
- Do not modify anything until the plan is decision-complete and the user says
  `開始執行`.
- Invoke `spec-governance.reconcile` after every answer and display its Spec delta,
  affected IDs, relations, conflicts, open decisions, and verdict.
- After authorization, materialize one canonical `specs/SPEC-####-<slug>.md`. Every
  modifying path must complete the `spec-verified` stage before TDD or implementation.
- On a later task, resolve and verify a confirmed spec only with explicit
  `resume_confirmed_spec` evidence. Resume its TDD/implementation target without
  repeating grilling when there is no new decision or conflict.
- If execution exposes any new discretionary decision, stop immediately, return to
  grilling one question at a time, update the plan, and wait for authorization again.
  Compiler errors and test failures that can be investigated are facts, not user
  decisions.

Resolve active specs by explicit path, tracker canonical path, branch match, then the
unique confirmed spec. Multiple candidates are `BLOCKED`; never select the newest.
Implemented specs are not active fallback. Resolution alone never supplies resume
evidence.

## Wayfinder escalation

After grilling, recommend `wayfinder` only when all three signals exist:

1. at least two decision-ticket candidates;
2. at least one blocking dependency;
3. at least one fog area that cannot yet be phrased as a precise ticket.

Missing `wayfinder` or tracker capability is `BLOCKED`. Creating a map or tickets is
an external write and still requires `開始執行`. Wayfinder hands off to `to-spec`,
then `to-tickets`; it never jumps directly to implementation for a large effort.

## Capability and presentation

- Missing `grill-me` with `grilling` available → `DEGRADED`; use the primitive
  transparently.
- Missing `ask-matt` from a fresh-task inventory → plugin discovery/release failure.
- Missing a required non-substitutable skill → `BLOCKED`.
- A normal `PASS` route gets one concise summary line.
- Expand project, intent, risk, and capability evidence for `DEGRADED`, `BLOCKED`,
  or any `indeterminate` assessment.
