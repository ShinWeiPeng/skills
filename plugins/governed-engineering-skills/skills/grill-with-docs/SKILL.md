---
name: grill-with-docs
description: Interview engineering work when durable project context exists but implementation is absent. Model-invoked by ask-matt; users need not name it.
---

Run a `/grilling` session, using the `/domain-modeling` skill.

Read and enforce
[the shared Decision Question Contract](../ask-matt/references/decision-question-contract.md)
for every decision asked through this wrapper.

Use this wrapper only when ProjectState has `implementation: absent` and
`stateful_context: present`. Formal specs, PRDs, ADRs, `CONTEXT.md`, and governed
architecture records count as durable context; a README or template alone does not.

Ask one question at a time, recommend an answer, and investigate discoverable facts
instead of asking the user.

Invoke `spec-governance.reconcile` after every answer. Compare the working spec with
non-empty legacy context, accepted ADRs, and the architecture manifest; show the Spec
delta, affected IDs, relationships, conflicts, open decisions, and verdict. A
A confirmed spec found on a later task is verified and resumed without another
interview only when the caller supplies explicit resume evidence and the request
introduces no new decision or conflict. Resolution alone proves durable context and
does not bypass this interview.

Before writing `CONTEXT.md`, ADRs, or other files, read [the shared governed entry gate](../engineering-risk-routing/references/entry-gate.md) and invoke `$engineering-risk-routing`. In Plan mode, describe the intended documentation diff but do not write it.

Documentation created by this wrapper belongs to the same change set and does not
trigger a second interview. Never write it until the user says `開始執行`.
