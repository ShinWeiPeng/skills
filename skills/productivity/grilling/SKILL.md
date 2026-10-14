---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
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

Explicitly invoke the discussion owner and router with the actual task, turn and
source references. Save and verify the current discussion before dependent product
operations and before completing the turn. The bundle registers no lifecycle hooks
and requires no host trust, loading or firing evidence. Preserve legacy observations
as history. Permit bounded repair; after failed synchronization, report the unsaved
scope and keep reading, discussion and document repair available. Product changes
still require the current SPEC and valid execution authorization. Reply hashes are
audit evidence; they do not prove semantic completeness or intercept host tools.



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

Do not implement or perform product, Git, or external actions until I confirm we
have reached a shared understanding.

For all engineering work, start or resolve the same canonical working
`specs/SPEC-####-<slug>.md` before the first substantive answer or decision question.
After each turn invoke `spec-governance.reconcile` for new adopted content and append sourced
discussion history there. Do not create a separate working document or journal.
Persist readable requirements and structured `DISC-###` context before displaying the
Spec delta, affected stable IDs, relationships, conflicts, open decisions, and
`PASS/BLOCKED` consistency result or asking another question. Preserve the visible
user answer and explicitly stated rationale in DISC records, but never store a full
transcript, hidden reasoning or secrets. The journal may retain bounded sourced goals and discussion summaries.

If a confirmed unimplemented spec may change, invoke `spec-governance.reopen` before
asking the clarifying question. Preserve its SPEC ID and path. Implemented specs
never reopen.

Investigate factual blockers first; ask only an unresolved user decision. When an adopted change contract is decision-complete,
present the complete proposal and intended non-spec diff once. After explicit user
confirmation, invoke `spec-governance.materialize`; confirmation is separate from
the exact `開始執行` execution authorization. Follow spec-governance's consolidated
discussion and delivery policy for relevant history, resumption and lock recovery.

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

Discussion starts in one `specs/SPEC-####-*.md` working file. Each new answer updates that file; confirmation keeps its ID and path. Decisions, pending discussion, completeness gaps and source history remain together. New discussions do not create a parallel WORKING-SPEC/journal pair.

## SPEC update visibility

Every successful SPEC save, including a working revision, must be reported in that
turn with a clickable canonical SPEC ID/title link, actual revision and lifecycle
status, a short change summary and the current execution authorization state.
A failed save must be described as failed; never claim that an unpersisted change
was saved. Link the same canonical file through reopening and confirmation.

Word each decision question so "yes" accepts the recommended answer. Keep the fork's one-question-at-a-time persisted discussion contract.
