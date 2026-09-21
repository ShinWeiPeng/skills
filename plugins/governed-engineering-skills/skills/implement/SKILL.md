---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

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


Implement the work described by the user in the spec or tickets.

## Governed entry gate

Invoke `$engineering-risk-routing` and follow its shared governed entry gate before mutation.

Resolve the canonical spec through `spec-governance`. Require a `confirmed` spec and
a `spec-verified: PASS` result. Before implementation, render a REQ → AC → test-seam
traceability assessment; missing requirements, validation methods, invalid
references, conflicts, or open decisions are `BLOCKED`.

Use /tdd where possible, at pre-agreed seams.

Immediately before governed mutation, run `scripts/spec_delivery.py --project-root
<root> --spec <canonical-path> --expected-hash <verified-file-sha256>
--authorization <original-explicit-execution-instruction> --working-reference
<working-id> --task-ref <task-id>`. Require `product_code_allowed: true` and PASS.
Record the hash during spec verification, not by replacing a stale hash after an
unreviewed change. Replay the actual user authorization, never synthesize it from
proposal adoption, a numbered answer, silence or mode changes. This CLI checks the
plugin's governed entry point; it is not a host-wide write interceptor.

Before handing off to TDD or authoring product source, the delivery workflow invokes
`/formatter-governance` with the original ProjectState evidence. Continue only after
its applicable non-mutating formatter gate passes; keep formatter mappings with
their owning skill.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

After every AC has actual PASS evidence and the code-review Spec axis reports no
missing, incorrect, or scope-creep behavior, the implement orchestration may update
the canonical spec revision to `implemented` and append the evidence. Standalone
code review remains read-only and never performs this lifecycle mutation.

Commit only when the user or repository instructions explicitly authorize a commit. Otherwise report the completed diff and validation evidence without committing.

## Project validation obligations

Managed modification admission verifies the current SPEC and valid authorization. Generate `validation/acceptance-SPEC-####.json` from SPEC through the common entry; planning and enablement are checked when their operations require them, not as preconditions for the edits that produce them. Final HIL evidence is not required to perform authorized implementation that produces it. Before reporting overall acceptance, call managed `complete` with phase `acceptance`; release requires a separate `release` assessment. Preserve partial host PASS while missing necessary evidence keeps overall acceptance BLOCKED.

## Test and validation storage governance

Apply [the shared test/validation contract](../govern-modular-event-architecture/references/test-validation-architecture.md). Keep test source and support
in tests/ by Module/Flow ownership, authored validation definitions in validation/,
and generated evidence in unique immutable artifacts/ runs. specs/ only references
fixed runs. Run the whole-project layout gate for positions, roles, owners and references.
Language, dependency and isolation checks are outside layout scope; independently
required architecture or device checks retain their own completion requirements. Do not change project Git policy.

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
investigation, never success. Existing discussion repair allowances are untouched.

## SPEC update visibility

Every successful SPEC save, including a working revision, must be reported in that
turn with a clickable canonical SPEC ID/title link, actual revision and lifecycle
status, a short change summary and the current execution authorization state.
A failed save must be described as failed; never claim that an unpersisted change
was saved. Link the same canonical file through reopening and confirmation.

## Shared implementation and correction path

Follow the common modification entry in `references/managed-delivery.md` and the
consolidated discussion policy in spec-governance. Setup, implementation and
same-scope verification repairs use the same current authorization. Missing
results to be produced do not prohibit their implementation; final acceptance
still requires the confirmed layers and evidence. Read `generate-acceptance`
output before applying its derived patch and preserve unresolved planning gaps.
