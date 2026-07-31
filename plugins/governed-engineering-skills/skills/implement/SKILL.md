---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

Implement the work described by the user in the spec or tickets.

## Governed entry gate

Read [the shared governed entry gate](../engineering-risk-routing/references/entry-gate.md) and invoke `$engineering-risk-routing` before mutation.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit only when the user or repository instructions explicitly authorize a commit. Otherwise report the completed diff and validation evidence without committing.
