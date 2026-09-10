---
name: implement
disable-model-invocation: true
description: "Implement a piece of work based on a spec or set of tickets."
---

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
