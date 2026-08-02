---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

Implement the work described by the user in the spec or tickets.

## Governed entry gate

Read [the shared governed entry gate](../engineering-risk-routing/references/entry-gate.md) and invoke `$engineering-risk-routing` before mutation.

Resolve the canonical spec through `spec-governance`. Require a `confirmed` spec and
a `spec-verified: PASS` result. Before implementation, render a REQ → AC → test-seam
traceability assessment; missing requirements, validation methods, invalid
references, conflicts, or open decisions are `BLOCKED`.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

After every AC has actual PASS evidence and the code-review Spec axis reports no
missing, incorrect, or scope-creep behavior, the implement orchestration may update
the canonical spec revision to `implemented` and append the evidence. Standalone
code review remains read-only and never performs this lifecycle mutation.

Commit only when the user or repository instructions explicitly authorize a commit. Otherwise report the completed diff and validation evidence without committing.
