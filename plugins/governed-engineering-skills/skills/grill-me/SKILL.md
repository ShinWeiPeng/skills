---
name: grill-me
description: Interview a greenfield engineering request when both implementation and durable project context are absent. Model-invoked by ask-matt; users need not name it.
---

Run a `/grilling` session for a project assessed as `absent / absent`.

Read and enforce
[the shared Decision Question Contract](../ask-matt/references/decision-question-contract.md)
for every decision asked through this wrapper.

An empty Git repository is no codebase. A README, template, or empty scaffold is
insufficient evidence and must remain `indeterminate` until one
conclusion-changing question resolves it.

Ask one question at a time, recommend an answer, and investigate discoverable facts
instead of asking the user. Before the first decision, start or resolve the
project-local working bundle. Maintain stable REQ/DEC/AC IDs and, after every answer,
invoke `spec-governance.reconcile` to persist the Markdown snapshot and normalized
journal before showing the Spec delta, consistency verdict, relations, conflicts,
and open decisions.

During the interview, write only local `spec-governance/WORKING-SPEC-*` pairs and the canonical spec
lifecycle owned by `spec-governance`. When decision-complete, hand off immediately
to `spec-governance.materialize`; the resulting non-empty confirmed spec makes the
next task's stateful context present but does not authorize product changes. Show the
confirmed spec and intended non-spec diff, then wait for `開始執行`.

If the result contains at least two decision-ticket candidates, one blocking
dependency, and one fog area that cannot yet be phrased precisely, recommend
`wayfinder`. Otherwise hand off to `spec-governance`, then `to-spec` for tracker
publication or the decision-complete delivery flow.
