# Recoverable discussion synchronization (SPEC-0029 refined by SPEC-0032)

`grilling` owns engineering discussion. Routing may name a supporting skill, but
product delivery requires a saved entry with matching task, working identity and
current revision/hash. Investigation and discussion handoffs remain available when
synchronization fails; their results never authorize product writes. Neither a selected skill nor a caller's `done` flag is evidence.

## Host and manual entry

The bundled hook config uses `SessionStart`, `UserPromptSubmit`, `PreToolUse` and
`Stop`. Install/enable is separate from reviewing and trusting the exact definition.
Linux uses `python3`. Windows uses the explicit `GOVERNED_ENGINEERING_PYTHON`
executable or the current project's `.codex-arch-deps/venv/Scripts/python.exe`,
verifies Python 3.11+, and does not select an incompatible PATH Python. Codex
supplies `PLUGIN_ROOT`. Runtime failure emits a capability gap without terminating the task; unverified product operations remain denied. Never set managed trust or use a hook-trust bypass to manufacture evidence.

Prompt hooks establish an unknown obligation because the host payload has no
engineering-intent field. The engineering router classifies it and initializes the
working SPEC in `specs/` automatically. For a non-engineering request, explicitly classify that
turn as `non-engineering` with a reason; no working SPEC is created. Do not inherit
engineering classification merely because an earlier turn discussed code.

Bind the selected canonical repository before the first SPEC when host cwd differs.
Send `operation: bind-project`, `task_ref` and an absolute `project_root` to the owner
at the host root. Hook, router and owner resolve that same task binding. Rebinding
an established task or silently relocating an existing SPEC is refused. Existing
unknown source records transfer under the shared binding lock before the pointer
changes; conflicts preserve both stores and block the binding. Ambiguous
parent workspaces retain their pending source and require an explicit selection;
never guess a child repository or create a second SPEC. Hook session/turn IDs
are source observations, not user approval. Legacy records have no retroactive
entry evidence; resuming does not invent it.

Without loaded hooks, call guided_workflow_router with actual `--task-ref`,
`--turn-ref` and `--source-ref` before the first substantive engineering reply.
The owner CLI also accepts a request file:

```text
python <plugin>/skills/spec-governance/scripts/discussion_state.py --project-root <project> --request spec-governance/DISCUSSION-REQUEST-turn.json
```

A repair may create/update only that `DISCUSSION-REQUEST-*.json` request surface via
apply_patch before invoking the owner. The pre-tool recovery allowance does not
permit an arbitrary script, shell chain, receipt replacement or product patch.

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

| Capability | Required evidence |
|---|---|
| Supported | Host version and documented event schema |
| Trusted | Host review of current hook definition; never inferred from install |
| Loaded | Host resolves this exact candidate's config and command |
| Fired | Real event/task/turn trace and resulting owner files |

The configured pre-tool surface covers Bash and apply_patch/Edit/Write. Bounded
reads and owner-request recovery remain possible when saving is blocked. MCP,
other local functions, hosted tools, ongoing process stdin, already streamed text
and interruptions are not claimed to be fully intercepted by this config. Stop
cannot retract a reply already shown. Timeout, startup failure or missing hooks
must be reported as a gap even when voluntary CLI persistence works.

Synthetic events and launcher-process tests establish host-side contracts only.
Real desktop traces are required for AC-001/002/009/010/011 and overall acceptance;
missing trust/loading/firing evidence keeps those criteria pending.

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

## Hook observations are separate from host verification

Query `hook-health` for declared event support and adapter observations. A direct
owner save is manual and creates no hook observation. The stdin adapter records its
event, task/turn, host and canonical roots, entrypoint hash, package version, and
input/output hashes. Those records are caller-attested observations, not authenticated
proof that Codex trusted, loaded or fired that candidate. `trusted`, `loaded`, and
`fired` remain `unverified` without external host evidence; absent observations never
mean success. Bounded observation history discloses truncation. Do not enable trust
automatically or substitute simulated subprocess events for desktop validation.
