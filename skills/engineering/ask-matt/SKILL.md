---
name: ask-matt
description: Automatically route every software-engineering request, including implementation, modification, debugging, review, code explanation, tests, architecture, and deployment. Model-invoked; users never need to name this skill.
---

## Engineering discussion entry

For every engineering task, `grilling` owns discussion state from entry, including
read-only diagnosis, explanation and proposal exploration. Start or resume the
same task's canonical working SPEC in `specs/` before a substantive answer. Initial
fact discovery may precede entry; ask only genuine unresolved user decisions.
Supporting skills still diagnose, explain and compare alternatives.

Use the spec-governance discussion entry contract at
`references/discussion-entry.md` in the resolved spec-governance skill. Save sourced
goals, constraints, facts, answers and candidate suggestions. A candidate is not an
adopted requirement or execution grant; rejected/deferred candidates do not block
the original task. If saving fails, disclose the gap and continue discussion or repair; only dependent product changes wait for synchronization. Pure discussion may finish with a saved working record and no
formal SPEC. Materialize only a complete adopted change scope, expected behavior,
decisions and acceptance criteria. Reopen confirmed changes and create successors
for implemented contracts using the existing lifecycle.

Bundled trusted hooks establish task/turn obligations, inspect covered dependent
operations and check Stop persistence. Unknown intent is not silently exempt.
SPEC-0032 separates synchronization from recovery permission. Permit one automatic
repair per actual input state; replay or restart cannot reset its durable history.
After a failed repair, report unsaved scope and finish normally. Discussion, reading,
classification, saving and rechecking remain available; product changes still require
a current SPEC and valid execution authorization. Historical repair failure is not
a permanent denial. Reply wording hashes are audit evidence, not synchronization gates. Report support, trust, loading and actual firing separately; missing
hooks require the explicit owner CLI and remain a capability gap. Do not bypass
hook trust or claim interception of every tool, reply or interrupt.



## Universal SPEC visibility and execution boundary

Apply this workflow to every project, language, size of change and later turn.
Before any program writing (including bug fixes, tests, configuration, formatting
and generated output), establish the current confirmed SPEC, present it, and
observe the user's exact `開始執行` for that scope. A requirement, option answer,
adoption, small follow-up or prior task authorization is not a new execution grant.
Keep SPEC discussion and persistence active while product execution waits.

Every completed SPEC creation or reconfirmed revision must appear in the actual
user-visible reply: **SPEC ID and title linked to the canonical file**, a nonempty
scope summary or revision delta, and the actual authorization state. A saved file,
opened side panel, plain filename or `proposal_presented: true` alone is insufficient.
Without authorization, say `SPEC 已完成，等待「開始執行」。`; after current verified
authorization, say `SPEC 已完成，已取得本次「開始執行」授權。` and identify the scope.
Do not ask again when the user has already authorized the just-discussed scope.

Reload the current working reference and execution status before dependent product
operations. New requirements suspend the previous scope until reconciled and freshly
authorized. Use the managed entrypoint and inspect its result; do not fall back to
direct patch or Shell writes when blocked. No per-project or global AGENTS reminder
is needed. This is a plugin workflow contract, not host interception.

## Shared discussion and execution boundary

Apply the [managed delivery contract](../implement/references/managed-delivery.md)
to all projects and subsequent turns. Keep SPEC reconciliation active while product
execution is paused. Requirement changes and option adoption are not execution
authorization. Observe routing results before dependent tools; never compose a gate
and an unconditional write. Use managed receipts and the managed patch entrypoint
for supported product edits; do not fall back to direct tools on rejection.


# Automatic Engineering Router

Use this skill automatically whenever the user's intent is software engineering.
The user describes the work; never require them to know or invoke `ask-matt`.
Standalone notes and non-engineering writing remain outside this router.

Before any governed engineering workflow asks the user to choose a design or
specification outcome, read and enforce
[the shared Decision Question Contract](references/decision-question-contract.md).
The contract applies to explicit downstream skills as well as inferred routes.
Before any question surface, run spec-governance question-policy with current host
instructions and saved question context. Default must not invoke menu tools; use
permitted numbered text or one persisted open text question. Only already-active
Plan may use a permitted menu. Apply the same policy to retries and alternatives.

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

On every turn, call the router with the current task's `--task-ref`, actual
`--turn-ref` and `--source-ref`, and, once
resolved, `--working-reference`. The router reloads the persisted canonical working SPEC;
do not rely on a remembered `has_unresolved_decision` boolean. Never select a
different task's spec to make a route pass. Use `--turn-kind read-only` for a
factual follow-up, `decision-answer` for an explicit answer, and `change-request`
for a semantic modification not recognized by the keyword hints. Missing or
ambiguous context blocks dependent modification and must be recovered.

Pending questions route through spec-governance even when the latest input is
empty, numeric, a mode change, or `開始執行`. A read-only follow-up can proceed while
preserving that pending state. Changes to Git tracking and configuration are
modifying work. After an answer, reconcile against the saved question ID/version
and working revision/hash before rerouting; do not clear pending state yourself.

Before governed delivery, run the `implement/scripts/spec_delivery.py` admission
CLI with the resolved canonical path, hash captured at verification, original
explicit execution instruction, working reference and task reference. It reloads
the actual spec and rejects stale, invalid, pending or mismatched state. Neither
an old `spec-verified` label nor proposal adoption replaces this check. This is
a plugin workflow boundary, not interception of arbitrary tool calls.

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

Keep factual, read-only follow-ups in their supporting diagnosis, review, or
code-understanding flow while grilling retains discussion ownership. Once `grilling` owns a change set, start or resolve its
persistent canonical working SPEC and reconcile every answer through
`spec-governance.reconcile` before asking the next decision. Return to the recorded
supporting or proposal workflow only after the interview is decision-complete and
the confirmed canonical spec has materialized.

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
follows the ProjectState interview route. In a fresh task, exact `開始執行`, optionally
followed by one explicit `specs/SPEC-####-<slug>.md` path, is
`resume_confirmed_spec=true` evidence. Select the sole valid confirmed candidate or
the explicit path; ask one selection question when several confirmed candidates
remain, and fail closed when none exists. Quoted, negated, or longer conversational
uses of the phrase are not resume evidence.

A README, template, empty scaffold, or empty formal-context file alone is not proof
of a codebase or durable project knowledge.

## Change-set interview contract

Every repository-modifying change set completes grilling before product mutation,
regardless of size or an explicitly requested skill such as `tdd`.

- Interview the whole change set once. Source, tests, docs, migrations, generated
  views, versions, and changelog entries required by that change do not restart it.
- A bug may complete read-only diagnosis first. Choosing the fix then requires
  grilling.
- Ask one decision question at a time under the shared Decision Question Contract.
- Do not ask discoverable facts.
- Before the first substantive engineering answer, start or resolve the same canonical working file
  `specs/SPEC-####-<slug>.md`, including its embedded discussion history.
  Persist every answered decision and its structured `DISC-###`
  context before another question.
- Invoke `spec-governance.reconcile` after every answer and display its Spec delta,
  affected IDs, relations, conflicts, open decisions, and verdict. Missing journal
  continuity is explicit and never reopens already settled decisions by itself.
- When an adopted change contract is decision-complete, invoke `spec-governance.materialize` to confirm
  that same canonical `specs/SPEC-####-<slug>.md` in place. This spec-only lifecycle write does not
  authorize product changes.
- Do not modify product source, tests, configuration, `CONTEXT.md`, ADRs,
  architecture artifacts, generated files, Git, or external state until the user
  says exact `開始執行`. Every modifying path must complete `spec-verified` before
  TDD or implementation.
- Enforce this boundary from the plugin's bundled contracts. Never require, create,
  edit, or depend on a user-global `AGENTS.md` to make spec governance work.
- On a later task, resolve and verify a confirmed spec only with the exact fresh-task
  phrase or equivalent caller-supplied `resume_confirmed_spec` evidence. Resume its TDD/implementation target without
  repeating grilling when there is no new decision or conflict.
- If execution exposes any possible contract-changing discretionary decision, invoke
  `spec-governance.reopen` before clarification, suspend the existing execution
  authorization, and return to grilling one question at a time. Every SPEC revision,
  including reconfirmation with no actual contract delta, requires a fresh exact
  `開始執行` covering that revision. Compiler errors and test failures that can be investigated are
  facts, not user decisions.
- After spec verification, the delivery parent invokes `/formatter-governance`
  before handing modifying work to TDD or implementation. Preserve its original
  ProjectState evidence and stop on a formatter `BLOCKED` verdict. When the verified
  canonical SPEC triggers full-program formatting, let that skill ask once for
  write authorization, protect the clean product-and-test scope, prefer a
  repository CLI with governed fallback, and keep installation permission plus CLI
  write/check evidence inside the same formatter gate.

Before commit, invoke `spec-governance.prepare-commit`. Staged or tracked local
working state blocks commit. Ask whether to delete the bundle, keep it local, or
archive its normalized journal under `specs/history/`; never perform that disposition
or Git action implicitly.

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

## Preserve active discussion through the final reply

Apply the shared Decision Question Contract's discussion completion loop. Mixed
answer/requirement/question messages retain every component. Reconcile decisions,
reload SPEC context, then present the next saved question in this turn. A factual
side answer reconnects the same unanswered question. Run spec-governance
`finish-turn` and inspect its result before finalizing; a statement that discussion
will continue later is insufficient. A product pause does not pause discussion.
Only a presented pending question, an evidenced blocker with required input, an
explicit user discussion pause, or a presented decision-complete proposal permits
waiting. The check grants no product execution authority.

## Project validation obligations

At entry, resume, and explicit skill reload, run the guided router with current task/SPEC references. Inspect `project_validation`: it rereads project policy, manifest, matrix and device profile with hashes. Preserve its additive `required_gates` on short prompts. A reload is not complete merely because SKILL.md was read. Missing mappings remain BLOCKED for dependent acceptance; continue read-only discovery and spec repair. Unchanged reload does not create a new execution-authorization requirement.

## Test and validation storage governance

Apply [the shared test/validation contract](../govern-modular-event-architecture/references/test-validation-architecture.md). Keep test source and support
in tests/ by Module/Flow ownership, authored validation definitions in validation/,
and generated evidence in unique immutable artifacts/ runs. specs/ only references
fixed runs. Run the whole-project layout/dependency gate; unknown ownership or
missing required capability blocks completion. Do not change project Git policy.

## Bounded diagnosis and recovery

Separate discovered skill names, callable CLI capabilities and actual check
verdicts. `test-validation-layout` resolves to the validated `architecture_cli.py
layout` result; a callable FAIL or BLOCKED remains a failed or blocked check.
An explicit caller capability limit is never expanded by discovery.

A blocker records category, original evidence, affected branch, repair suggestion,
authorization requirement, reproducible recheck, success condition and resume target.
Investigate discoverable facts and prepare the concrete repair first. Reuse current
authorization for deterministic repairs within the confirmed contract; ask only
for missing decisions, authority or external conditions. Never change acceptance
thresholds or replace required runtime evidence with host results.

Managed `recover` stores branch state beside the existing execution receipt. It
checks the same task/SPEC binding, reserves each attempt before effects, and allows
at most three attempts and 120 seconds per input cycle. Identical failed inputs
require evidenced temporary failure to retry; changed actual inputs or repair
start a new bounded cycle while preserving history. Unsupported rechecks remain
investigation, never success. Discussion repair uses SPEC-0032 input-state deduplication; historical failure never bars saving or rechecking.

## SPEC update visibility

Every successful SPEC save, including a working revision, must be reported in that
turn with a clickable canonical SPEC ID/title link, actual revision and lifecycle
status, a short change summary and the current execution authorization state.
A failed save must be described as failed; never claim that an unpersisted change
was saved. Link the same canonical file through reopening and confirmation.

## Persistent discussion and pre-receipt repair

Resolve the task's explicitly selected project root through the spec owner's binding
before router, hook or owner work. Every new engineering turn reviews its sources
and identified items through `observe`, then records actual contract row mappings
in the same working SPEC; a summary alone is insufficient. Confirmation is explicit,
not a side effect of saving discussion. Follow the spec-governance discussion entry
contract for recovery and honest hook-health reporting.

Delivery retains valid pending authorization separately from a receipt. Route a
missing acceptance mapping through `plan-acceptance-repair` / `repair-acceptance`
in the managed delivery contract; unknown mappings stay as durable drafts. Full
admission still controls product operations, and regular recovery keeps its receipt
requirement. Never equate an adapter invocation with verified desktop hook firing.

For other missing validation definitions, use `prepare-validation` with the same
retained authorization. Use `enablement-status` to admit the declared preparation
checks before requiring their evidence. Follow the managed delivery continuation
contract through preparation, implementation and final validation. Do not return
control merely on a repairable configuration gap or request the same permission
again. Preserve required evidence and report only genuine unresolved decisions,
unavailable external conditions or failures that bounded recovery cannot repair.

The workflow remains discussion → specification confirmation → execution authorization → implementation → verification → completion. Save every discussion turn in the same canonical SPEC; an unchanged turn does not increment its revision. A complete sourced review confirms an adopted contract in place, without an additional flag. Confirmation does not grant execution authority.
