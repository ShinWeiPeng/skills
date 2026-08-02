---
name: grill-me
description: Interview a greenfield engineering request when both implementation and durable project context are absent. Model-invoked by ask-matt; users need not name it.
---

Run a `/grilling` session for a project assessed as `absent / absent`.

An empty Git repository is no codebase. A README, template, or empty scaffold is
insufficient evidence and must remain `indeterminate` until one
conclusion-changing question resolves it.

Ask one question at a time, recommend an answer, and investigate discoverable facts
instead of asking the user. Maintain an in-conversation working spec with stable
REQ/DEC/AC IDs. After every answer invoke `spec-governance.reconcile` and show the
Spec delta, consistency verdict, relations, conflicts, and open decisions.

Do not create project files during the interview. When decision-complete, show the
full canonical spec and intended file diff, then wait for `開始執行`. After
authorization hand off to `spec-governance.materialize`; the resulting non-empty
confirmed spec makes the next task's stateful context present.

If the result contains at least two decision-ticket candidates, one blocking
dependency, and one fog area that cannot yet be phrased precisely, recommend
`wayfinder`. Otherwise hand off to `spec-governance`, then `to-spec` for tracker
publication or the decision-complete delivery flow.
