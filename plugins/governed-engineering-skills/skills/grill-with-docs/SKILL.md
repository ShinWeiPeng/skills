---
name: grill-with-docs
description: Interview engineering work when durable project context exists but implementation is absent. Model-invoked by ask-matt; users need not name it.
---

Run a `/grilling` session, using the `/domain-modeling` skill.

Use this wrapper only when ProjectState has `implementation: absent` and
`stateful_context: present`. Formal specs, PRDs, ADRs, `CONTEXT.md`, and governed
architecture records count as durable context; a README or template alone does not.

Ask one question at a time, recommend an answer, and investigate discoverable facts
instead of asking the user.

Before writing `CONTEXT.md`, ADRs, or other files, read [the shared governed entry gate](../engineering-risk-routing/references/entry-gate.md) and invoke `$engineering-risk-routing`. In Plan mode, describe the intended documentation diff but do not write it.

Documentation created by this wrapper belongs to the same change set and does not
trigger a second interview. Never write it until the user says `開始執行`.
