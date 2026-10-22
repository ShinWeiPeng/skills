# Recoverable discussion synchronization (SPEC-0029 refined by SPEC-0032)

`grilling` owns engineering discussion. Routing may name a supporting skill, but
product delivery requires a saved entry with matching task, working identity and
current revision/hash. Investigation and discussion handoffs remain available when
synchronization fails; their results never authorize product writes. Neither a selected skill nor a caller's `done` flag is evidence.

## Explicit discussion entry

The bundle registers no lifecycle hooks. Invoke the router and discussion owner
explicitly with the actual task, turn and source references. Engineering requests
initialize the working SPEC; classify non-engineering turns with their actual
reason. Do not infer a new turn's intent solely from earlier engineering work.

Bind the selected canonical repository before the first SPEC when host cwd differs.
Send `operation: bind-project`, `task_ref` and an absolute `project_root` to the owner
at the host root. Router and owner resolve that same task binding. Rebinding
an established task or silently relocating an existing SPEC is refused. Existing
unknown source records transfer under the shared binding lock before the pointer
changes; conflicts preserve both stores and block the binding. Ambiguous
parent workspaces retain their pending source and require an explicit selection;
never guess a child repository or create a second SPEC. Task/turn IDs are source references, not user approval. Legacy records have no retroactive
entry evidence; resuming does not invent it.

Call guided_workflow_router with actual `--task-ref`,
`--turn-ref` and `--source-ref` before the first substantive engineering reply.
The owner CLI also accepts a request file:

```text
python <plugin>/skills/spec-governance/scripts/discussion_state.py --project-root <project> --request spec-governance/DISCUSSION-REQUEST-turn.json
```

Repairs may update the owner request surface and document records. They cannot
replace execution receipts or grant authority for product patches.

```json
{
  "operation": "classify",
  "task_ref": "actual-session-id",
  "turn_id": "actual-turn-id",
  "kind": "engineering",
  "reason": "The current user request concerns repository behavior."
}
```

`status` returns the current `binding` and required `source_refs`. First register
this turn's actual items. For a reviewed turn with no newly identified items:

```json
{
  "operation": "observe",
  "task_ref": "actual-session-id",
  "turn_id": "actual-turn-id",
  "source_refs": ["copy-every-source-from-status"],
  "items": []
}
```

For decisions, candidates, facts or questions, provide sourced item rows instead;
see the item contract below. Before the final reply, use `record` with
that exact binding, a sourced summary and prepared `reply_text`. The journal stores
only its reply hash as audit evidence, not a full assistant transcript. Stop checks
source/current binding and saved audit continuity, not reply wording equality.
The assistant still reconciles substantive requirements; hashes do not prove
semantic completeness. With no new content, verify without changing SPEC revision.

```json
{
  "operation": "record",
  "task_ref": "actual-session-id",
  "turn_id": "actual-turn-id",
  "binding": {"working_id": "copy-from-status", "revision": 1, "snapshot_hash": "copy-from-status"},
  "source_ref": "actual-visible-message-or-prepared-reply-reference",
  "summary": "Sourced goals, constraints, facts, decisions and remaining work.",
  "reply_text": "The exact final response to be emitted.",
  "candidates": [],
  "item_bindings": {}
}
```

Candidate rows have `id`, `status`, `source_ref`, `reason` and `impact`. Initial
status is `candidate`; `accepted`, `rejected` or `deferred` additionally needs the
actual `user_source_ref`. Accepted candidates also identify the lifecycle
`reconciliation_ref` and an observed accepted item with the same ID and user source; this summary operation cannot insert a formal requirement,
adopt a candidate or authorize execution. A complete sourced review automatically
confirms a settled adopted contract in place; no extra `confirm_contract` flag is
required. Candidates and unresolved gaps do not qualify. Do not invent IDs or adoption evidence.

## Persistence and completion

The spec owner keeps one authoritative `specs/SPEC-####-*.md` file with an embedded hash-linked audit. Existing DISC records and formal REQ/DEC/AC reconciliation remain intact.
The embedded audit additionally accepts normalized `discussion` observations with bounded,
redacted goal/summary/candidate fields, source references and a current binding.
These observations are not adopted decisions. Task-private `DISCUSSION-*.json`
indexes original turns, continuation aliases and consumed repair allowances; it
cannot substitute for a matching journal event and actual working snapshot.

A pure diagnosis/explanation can finish with a current saved discussion and no
formal SPEC. A complete adopted change still uses normal reconcile/materialize,
confirmed reopen and implemented successor rules. Record the current binding again
after reconciliation; old hashes must fail. Do not ask a question just to finish.

The owner persists a repair input key before requesting a continuation. The key
uses actual working binding, prompt content and owner runtime bytes, excluding turn
IDs and reply wording. Replaying the same input or restarting cannot gain another
automatic attempt. A nested Stop ends normally after reporting the missing scope.
Direct classification, saving and rechecking remain available regardless of old
repair failure. Actual changed inputs can be rechecked; never invent a repair token.
Schema v1 states migrate to v2 with historical flags retained and consumed input
reserved. Corrupt state remains unverifiable and is not overwritten with success.
A kernel file lock serializes consumption and releases on process termination.

Read/recovery operations are recognized before querying potentially broken state.
The recovery surface permits native request-file edits and a single bundled owner
CLI invocation, including the actual Windows Python executable and leading call
operator. It rejects shell chains, redirected requests and lookalike scripts.

The existing execution receipt remains independent. Save and verify the adopted
discussion before authorizing product operations. An entry alone is not current
synchronization. Finish product operations and checks before appending any final
report audit; journal changes can invalidate that receipt under the existing managed
delivery contract. Recovery never restores a stale receipt.

## Coverage and acceptance

Evaluate explicit router/owner persistence and managed delivery through their
public interfaces. Saving, classification, rechecking and document repair remain
available without implementation authorization. Missing synchronization blocks
only dependent product writes. No host trust, loading or firing proof is required;
these voluntary entrypoints do not intercept arbitrary tools or streamed replies.

Before explicit contract confirmation, the agent reviews goal, scope, behavior, exceptions
and acceptance against the actual adopted contract. Supply `completeness_review`
to `record`, with those five keys, each containing bounded `source_ref` and
`evidence` text. This is sourced review evidence, not user authorization. Empty
contract cells cannot confirm; missing review leaves the file working and the
agent continues the completeness review without asking for redundant approval.

## Review each turn's identified items

New engineering turns require `observe` before `record`, including an explicit
empty list for a reviewed factual turn with no newly identified items. Supply
`source_refs` covering every current/carried source returned by `status`, and
`items` with `id`, `kind`, `source_ref`, and bounded `text`. Kinds are `accepted`,
`candidate`, `fact`, and `question`. Preserve real sources; do not manufacture a
user decision from an assistant suggestion. Register new items before work depending
on them. Use a separately sourced correction instead of changing an item's identity.

Reconcile adopted changes into the same canonical file. In `record`, supply
`item_bindings`, an object with one entry for every observed item. Each value is a
list of existing REQ/DEC/AC IDs. Every accepted item needs a DEC row whose Source cell contains its source reference; candidates
cannot claim adopted rows. A missing item or missing contract row blocks sync even
when the summary is present. The owner reads back the actual document and matching
journal event. Replaying identical observations/records does not append duplicates;
new turns carry unresolved sources and items forward, including across non-engineering
interludes, without resetting repair history.

Legacy records remain readable and are labelled `legacy-unregistered`; this is not
retroactive proof of item coverage. The mechanism checks identified items, not the
model's ability to understand every natural-language decision. Report the actual
`spec_presentation` link, revision and status and any unsaved scope.

## Legacy adapter history

Legacy observations remain readable as history. The compatibility `hook-health`
query reports a retired adapter with no supported events and host trust/loading/
firing `not-applicable`; it does not grant authority. Recording new hook observations
is rejected. Use the explicit owner protocol for current discussion evidence.

## Diagnosis fix contract review

When diagnosis proposes a new fix or changes its behavior, register it with
`discussion_state.py` operation `propose-fix` before related product work, including
regression tests. Use the current task/turn and binding, a stable `FIX-###`, exact
fix description and source reference. A shared repair goal is not evidence that
specific behavior is already adopted. Read-only investigation remains available.

Use the same owner's `compare-fix` operation to compare `applicable_states`,
`ordering`, `success`, `failure`, `rollback` and `retry`. Each dimension has
`status` (`covered`, `changed`, `unknown`), `rationale`, and `clauses` containing
actual REQ/DEC/AC IDs and their exact behavioral `text`. A covered dimension needs
at least one clause; validation methods, evidence labels and the whole SPEC title
are not behavioral clauses. Explain applicability; exact text matching alone
cannot establish semantic coverage.

Both operations require `binding` exactly from current discussion `status`.
`compare-fix` additionally requires the latest `proposal_event_hash`, the complete
`dimensions` map, `summary`, `source_ref` and `presentation_ref`. Present the
six-dimension comparison and its result in the actual reply before dependent
modification. The presentation reference is caller-attested; it does not prove
that a reply was emitted or that the user read it.

| Result | Required continuation |
|---|---|
| All dimensions covered, no pending question, valid receipt | Save current discussion and continue the authorized repair. |
| Any changed dimension | Discuss the delta; use the existing confirmed reopen or implemented successor, then confirmation and applicable new execution authorization. |
| Any unknown dimension or missing/stale comparison | Investigate read-only and ask only the unresolved decision; related managed edits wait. |

The owner stores proposals and comparisons in the same canonical SPEC's discussion
audit, without changing its contract snapshot for a covered repair. No second
contract or authorization state is created. A changed proposal invalidates its
old comparison; a new contract snapshot requires a current comparison. Ordinary
unchanged test retries and exact operation replays preserve valid receipts.

A factual follow-up, including "why did application fail?" or a request to inspect
the fix, is not adoption. Answer it and reconnect the same saved question ID and
version. Timeout, empty replies and mode changes do not resolve pending questions.

`verify_delivery_admission` and the managed writer reject registered fixes without
current covered comparisons. This is a voluntary managed workflow: callers must
register fixes, and model/trace review must detect omitted or misleading semantic
classification. It does not intercept arbitrary host tools or prove semantics
from hashes. Normalized trace audit accepts `fix_proposed` with the returned
proposal hash and current binding, and `fix_comparison` with the owner's actual
assessment as `review`; neither event grants execution authority. Raw trace review
still requires tool provenance and independently verified command effects.
