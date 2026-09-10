---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

## Shared discussion and execution boundary

Apply `references/managed-delivery.md` from the resolved `implement` skill
to all projects and subsequent turns. Keep SPEC reconciliation active while product
execution is paused. Requirement changes and option adoption are not execution
authorization. Observe routing results before dependent tools; never compose a gate
and an unconditional write. Use managed receipts and the managed patch entrypoint
for supported product edits; do not fall back to direct tools on rejection.


Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Before asking, follow the shared Decision Question Contract supplied by `/ask-matt`.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not implement or perform product, Git, or external actions until I confirm we
have reached a shared understanding.

For repository-modifying engineering work, start or resolve one persistent flat
`spec-governance/WORKING-SPEC-<id>-<slug>.md` snapshot and same-stem
`.journal.jsonl` before the first decision question. After every answer invoke
`spec-governance.reconcile`; persist the human-readable snapshot, structured
`DISC-###` context, and normalized hash-linked journal before displaying the
Spec delta, affected stable IDs, relationships, conflicts, open decisions, and
`PASS/BLOCKED` consistency result or asking another question. Preserve the visible
user answer and explicitly stated rationale in DISC records, but never store a full
transcript, hidden reasoning, secrets, or context prose in the journal.

If a confirmed unimplemented spec may change, invoke `spec-governance.reopen` before
asking the clarifying question. Preserve its SPEC ID and path. Implemented specs
never reopen.

If blocked, ask exactly one conclusion-changing question. When decision-complete,
invoke `spec-governance.materialize` immediately without treating that write as
product execution authorization. Then show the confirmed spec and intended
non-spec repository diff and wait for the user's exact `開始執行` authorization.

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
