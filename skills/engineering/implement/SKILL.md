---
name: implement
disable-model-invocation: true
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
