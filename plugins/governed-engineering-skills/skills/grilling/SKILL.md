---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Before asking, read and enforce
[the shared Decision Question Contract](../ask-matt/references/decision-question-contract.md).

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not implement or perform product, Git, or external actions until I confirm we
have reached a shared understanding.

For repository-modifying engineering work, start or resolve one persistent working
bundle under `.codex/spec-governance/<working-id>/` before the first decision
question. After every answer invoke `spec-governance.reconcile`; persist
`working.md` and its normalized hash-linked `journal.jsonl` before displaying the
Spec delta, affected stable IDs, relationships, conflicts, open decisions, and
`PASS/BLOCKED` consistency result or asking another question. Never store raw chat
or hidden reasoning in the journal.

If a confirmed unimplemented spec may change, invoke `spec-governance.reopen` before
asking the clarifying question. Preserve its SPEC ID and path. Implemented specs
never reopen.

If blocked, ask exactly one conclusion-changing question. When decision-complete,
invoke `spec-governance.materialize` immediately without treating that write as
product execution authorization. Then show the confirmed spec and intended
non-spec repository diff and wait for the user's exact `開始執行` authorization.
