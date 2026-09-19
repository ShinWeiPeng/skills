---
name: spec-governance
description: Persist, reconcile, materialize, reopen, resolve, and verify the canonical repository specification for every modifying engineering change set. Model-invoked by ask-matt and delivery workflows.
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

Bundled trusted hooks establish task/turn obligations, inspect covered dependent
operations and check Stop persistence. Unknown intent is not silently exempt.
SPEC-0032 separates synchronization from recovery permission. Permit one automatic
repair per actual input state; replay or restart cannot reset its durable history.
After a failed repair, report unsaved scope and finish normally. Discussion, reading,
classification, saving and rechecking remain available; product changes still require
a current SPEC and valid execution authorization. Historical repair failure is not
a permanent denial. Reply wording hashes are audit evidence, not synchronization gates. Report support, trust, loading and actual firing separately; missing
hooks require the explicit owner CLI and remain a capability gap. Do not bypass
hook trust or claim interception of every tool, reply or interrupt.



## Universal SPEC visibility and execution boundary

Apply this workflow to every project, language, size of change and later turn.
Before any program writing (including bug fixes, tests, configuration, formatting
and generated output), establish the current confirmed SPEC, present it, and
observe the user's exact `開始執行` for that scope. A requirement, option answer,
adoption, small follow-up or prior task authorization is not a new execution grant.
Keep SPEC discussion and persistence active while product execution waits.

Every completed SPEC creation or reconfirmed revision must appear in the actual
user-visible reply: **SPEC ID and title linked to the canonical file**, a nonempty
scope summary or revision delta, and the actual authorization state. A saved file,
opened side panel, plain filename or `proposal_presented: true` alone is insufficient.
Without authorization, say `SPEC 已完成，等待「開始執行」。`; after current verified
authorization, say `SPEC 已完成，已取得本次「開始執行」授權。` and identify the scope.
Do not ask again when the user has already authorized the just-discussed scope.

Reload the current working reference and execution status before dependent product
operations. New requirements suspend the previous scope until reconciled and freshly
authorized. Use the managed entrypoint and inspect its result; do not fall back to
direct patch or Shell writes when blocked. No per-project or global AGENTS reminder
is needed. This is a plugin workflow contract, not host interception.

## Shared discussion and execution boundary

Apply the [managed delivery contract](../implement/references/managed-delivery.md)
to all projects and subsequent turns. Keep SPEC reconciliation active while product
execution is paused. Requirement changes and option adoption are not execution
authorization. Observe routing results before dependent tools; never compose a gate
and an unconditional write. Use managed receipts and the managed patch entrypoint
for supported product edits; do not fall back to direct tools on rejection.


# Spec governance

Own one canonical change-set contract from the first governed decision through
verified implementation and commit disposition.

## Public interfaces

- `spec-governance.start`: resolve explicit identity, task/branch evidence or unique
  fallback; create `specs/SPEC-####-<slug>.md` immediately in `working` status.
  Keep that ID and path through confirmation and reopening. Embed source and
  revision events in the same file; new discussions do not create a parallel
  WORKING-SPEC Markdown/JSONL pair. Legacy pairs migrate only after identity,
  revision, content and history checks; conflicts preserve the originals.
- `spec-governance.reconcile`: classify each new statement as a domain term,
  change-set contract, ADR candidate, or open decision; preserve stable IDs; reject
  stale revision/hash writers; atomically persist the Markdown snapshot and append
  one normalized hash-linked journal event before another question; then show the
  Spec delta, affected IDs, relationships, conflicts, open decisions, and
  `PASS/BLOCKED` verdict.
- `spec-governance.materialize`: when decision-complete, write
  `specs/SPEC-####-<feature-slug>.md` using the next repository-wide four-digit
  number without waiting for `開始執行`. This spec-only write never grants product
  execution authority.
- `spec-governance.reopen`: before clarifying a possible contract change, change a
  confirmed unimplemented spec to `working` in the same ID/path and create its
  bundle. Implemented specs are immutable.
- `spec-governance.prepare-commit`: inspect whether local bundles are tracked or
  staged and require an explicit delete, keep-local, or normalized-journal archive
  disposition. It never performs the disposition or Git operation itself.
- `spec-governance.verify`: resolve the active spec, validate structure and
  REQ → AC → validation seams, and return `PASS` or `BLOCKED` before TDD or
  implementation.

Use `scripts/spec_contract.py start|status|reconcile|materialize|reopen|prepare-commit`
for the lifecycle, `validate --spec <path>` for the strict Markdown contract, and
`resolve --project-root <root> --prompt <request> --branch <branch>` for deterministic
canonical resolution.

## Reconcile loop

Before presenting a required question, use `scripts/spec_contract.py question
--project-root <root> --working-id <id> --question-id <Q-id> --question <text>
--option <first> --option <second> --expected-revision <revision>
--expected-hash <hash>`. The pending question is part of the existing Markdown
snapshot, with a version and exact options; the journal remains normalized.
A persisted question returns BLOCKED because a decision is now pending; inspect
the returned working reference to distinguish successful persistence from errors.

Recover with `turn-context --reference <working-id> --task-ref <task-id>`.
There is no response deadline. A question-tool timeout, empty result or mode
change must not clear pending state. When an explicit answer arrives, pass
`--question-id`, `--question-version` and `--answer` to `reconcile`, together with
the next full snapshot containing a new DISC record of that answer and the
expected working revision/hash. The owner clears the pending question only after
those checks; remaining conflicts or open decisions still block materialization.
Free-form answers and explicit withdrawal are valid answers. Empty, stale and
duplicate answers are rejected. Reopen a confirmed spec before a new question.

Before the first decision, invoke `start` or `status`. After each user answer:

1. Reload the authoritative canonical SPEC Markdown; reuse unchanged REQ, DEC, AC,
   and DISC IDs.
2. Compare it with non-empty `CONTEXT.md`, accepted ADRs, and the architecture
   manifest.
3. Reconcile using its expected revision and SHA-256. Atomically replace the complete
   human-readable Markdown snapshot with structured Discussion Context, then append only normalized delta, IDs,
   relations, conflicts, open decisions, verdict, revision, and hashes to JSONL.
   Preserve the visible user answer and explicitly stated rationale in DISC records.
   Never persist full transcripts, hidden reasoning or secrets. The discussion-entry
   contract additionally permits bounded redacted goal/summary/candidate observations
   with source references; they never substitute for adopted DISC/REQ/DEC/AC records.
4. Render the Spec delta, affected IDs, explicit relations, conflicts, open
   decisions, and consistency verdict.
5. Investigate factual blockers; ask only a genuine unresolved user decision.
6. When an adopted change has complete scope, behavior and acceptance, materialize
   or reconfirm its canonical spec. Pure saved discussion can finish without one. Render
   the confirmed spec and intended non-spec diff, then wait for exact product
   execution authorization.

If the journal is missing or its chain is invalid, trust the WORKING-SPEC Markdown, start a new
epoch marked `continuity: unavailable`, and continue from settled IDs. Do not turn
journal loss alone into reopened decisions.

Route domain vocabulary to `CONTEXT.md`, change-set requirements and acceptance to
the canonical spec, qualifying architectural decisions to a **proposed** ADR, and
unconfirmed content only to the working spec. During grilling, canonical `specs/SPEC-####-*.md` lifecycle writes and task-private runtime state writes are allowed.
`CONTEXT.md`, ADRs, architecture artifacts, tests, generated views, implementation,
Git, and external actions still require exact `開始執行`. These outputs are one
change set; do not recursively start another interview.

## Canonical contract

Each spec contains metadata (`spec_version`, `spec_id`, `revision`, `status`,
`change_set`), Problem, Solution, User Stories, Requirements, Decisions, Acceptance
Criteria with validation methods and evidence, Relationships (`depends_on`,
`refines`, `conflicts_with`, `supersedes`), Out of Scope, Open Decisions,
Routing/Gates, and Revision History.

`confirmed` requires unique IDs, valid references, zero unresolved conflicts, zero
open decisions, and at least one AC per REQ. `implemented` additionally requires
actual PASS evidence for every AC and a passing code-review Spec axis with no missing,
incorrect, or scope-creep behavior.

A confirmed unimplemented spec reopens in place before a possible contract-changing
question. Every SPEC revision invalidates earlier execution authorization,
including editorial changes, evidence-only updates and reconfirmation with no
actual contract delta. The normalized contract hash may describe semantic changes
but never retains or restores permission. After persisting and verifying the
revision, wait for a fresh exact `開始執行` covering that revision before any further
product operation. When the same user message both specifies a change and explicitly
authorizes its execution, reconcile that exact change before admitting execution;
never carry that instruction forward to a later change. SPEC persistence and
read-only verification may continue without product authority. Recording final
implementation evidence also invalidates the receipt; finish product checks first
and do not run subsequent product operations after that final SPEC update.
An implemented spec never reopens; create a related `refines` or `supersedes` change
set instead.

## Resolution and delivery

Resolve in order: user-explicit canonical path, tracker canonical path, branch match,
then the repository's unique confirmed spec. Multiple candidates are `BLOCKED`; never
choose the latest. An implemented spec is not an active fallback.

The local spec is authoritative. Publish its complete snapshot to the tracker with
the local path. If publication fails after local materialization, keep the file and
report `BLOCKED: tracker publication pending`; retry publication by spec ID without
rewriting the canonical document.

At commit preparation, a tracked or staged `spec-governance/WORKING-SPEC-*` path is
`BLOCKED`. Even when the bundle is untracked, ask exactly one disposition question:
delete it, keep it local, or archive only the normalized journal to
`specs/history/`. Do not auto-delete, auto-archive, stage, commit, or alter ignore
policy.

## Discussion completion assessment

After each mixed answer/question, reconcile all explicit decisions and reload
`turn-context`. Its `continuation.next_action` describes the remaining discussion
step and never grants execution authority. Follow the shared Decision Question
Contract from ask-matt for the complete same-turn loop.

Before ending an active discussion, run:

```text
python scripts/spec_contract.py finish-turn --project-root <root> --reference <working-id> --task-ref <task> --observation <json-file>
```

The observation supplies `working_spec` exactly as returned by the latest
turn-context. For a question, include `question_presented` equal to the complete
saved `pending_question` and a nonempty `presentation_ref` linking the rendered
reply or prepared reply artifact. For a complete proposal, include
`proposal_presented: true` and its `presentation_ref`. A `pause` must include
`scope: discussion` (or `all`), the original `user_text` and `source_ref`.
A `blocker` requires `detail`, `required_input`, `evidence_ref` and
`presentation_ref`. Set `unreconciled_decision: true` if an answer/change remains
unsaved; never omit an observed change to obtain a passing result.

Inspect `can_end_turn` and `next_action` before finalizing. A reference must identify
actual observed/prepared content, not a fabricated token. The model must render the
same checked question/proposal; the host does not intercept final replies. External
trace review checks that source references and normalized observations agree.
No second authority is created; the SPEC and its embedded audit remain authoritative.

Completion observations also include `project_root` exactly as recovered in
turn-context. Context changes invalidate presentation and observed admission;
question count persists until the next turn. Raw source references and pause
interpretation must be checked against the original messages.

When context recovery itself returns `invalid` or `absent`, include that exact
result as `context_error` plus the concrete blocker and required input. This
permits reporting an evidenced recovery problem without pretending a SPEC was
resolved. Unrecognized pause wording remains blocked for clarification; never
convert a product-only stop into a discussion pause.

## Mode and question presentation lifecycle

Use the shared [Decision Question Contract](../ask-matt/references/decision-question-contract.md)
before every surface selection, including retries and alternative requests.
Default/execution mode must not invoke menu tools. Use numbered text only when
host instructions permit it; otherwise persist one open question. Already-active
Plan may use a permitted menu; do not change mode to obtain permission.

Run `question-policy --project-root <root> --reference <working-id> --task-ref
<task> --host <json> --surface <surface>` and observe its result before presentation.
Host evidence contains mode, mode_ref, policy_ref, numbered_text_allowed and
menu_tool_allowed from the actual current instructions. Surfaces are numbered-text,
open-text, structured-menu, request_user_input or request_user_input_async. Default
and unknown modes never permit menus. Failed surfaces stay blocked until explicit
retry/recovery evidence is saved. No result authorizes product operations.

`question --kind open-text` accepts no options; absent kind remains legacy choice
with two or three options. Reconciliation accepts a free-form answer for either.
`question-update --project-root <root> --working-id <id> --request <json>
--expected-revision <revision> --expected-hash <hash>` preserves identity and records
history. The request includes action, question_version, original user_text and
source_ref. Action revise adds question, kind and options; presentation-failed and
retry-requested add surface. Updates never count as design answers. Use revise
before changing choice to open text or expanding alternatives. Reload afterwards;
stale answer versions and out-of-range numeric choices remain blocked.

Question observations additionally require presentation: host, surface, stage
(prepared or emitted), text, full reply_text and source_ref. Choice text is the
saved question plus a blank line and exactly numbered saved options; open text is
the saved question itself. The reply must contain that text. Include question_tools
with every observed question tool name and current host at observation.host so
completion also rejects a prohibited call even if text later repairs the reply.
A prepared file or accepted request alone proves no delivery. finish-turn reports
delivery_verified=false; independent emitted-reply trace review checks the actual
final response. Retain failed-surface feedback in the existing Question Record and
journal; never automatically resend a failed popup or treat feedback as an answer.

Place the saved question as the final block of the reply. Introductory prose may
precede it; do not add numbered alternatives elsewhere or append unpersisted
options. Completion compares all numbered lines with the saved option list.

For an allowed Plan menu, presentation.text records its exact saved question and
options. The final reply may repeat just that question; do not repeat numbered
choices when the host prohibits them. Menu payload evidence and actual reply
remain separate, and neither proves that the user saw the menu.

## Project validation obligations

Before recording any AC PASS, including evidence-only updates to a confirmed SPEC, invoke the shared project evidence assessment. Reconciliation, both materialization paths and implemented transitions reject unsupported PASS claims. Free-text PASS is a request to validate, never evidence itself. Preserve historical results but bind acceptance to current SPEC/policy/build/profile. Clear obsolete PASS assertions before revising a contract; replan and collect appropriate evidence for its new requirements.

## Test and validation storage governance

Apply [the shared test/validation contract](../govern-modular-event-architecture/references/test-validation-architecture.md). Keep test source and support
in tests/ by Module/Flow ownership, authored validation definitions in validation/,
and generated evidence in unique immutable artifacts/ runs. specs/ only references
fixed runs. Run the whole-project layout/dependency gate; unknown ownership or
missing required capability blocks completion. Do not change project Git policy.

## Continuous discussion and recovery

Keep readable Current Specification, Decision History, Pending Discussion and
Completeness Gaps views in the same file. Save new information before the next
question; an identical reconciliation does not increment revision. Reuse settled
question IDs and decisions; new premises require a sourced superseding decision.
Inspect behavior, exception handling and acceptance gaps before declaring closure.
A sourced completeness review of a settled adopted contract automatically confirms
the same file when all five dimensions are reviewed and no blocking gaps remain.
No extra `confirm_contract` flag or user reminder is required. Pure explanation
without an adopted complete change remains working.
Confirmation never grants implementation authority.

Acceptance planning is separate from saving: report missing/removed/changed ACs,
including same-ID criterion, requirement-reference and validation-method changes.
Changed criteria remain blocked after reload until the mapping explicitly binds
its `criterion_sha256` to the current reported criterion hash. Do not reuse evidence
for changed contracts. Only derive an unambiguous mapping from the confirmed SPEC;
otherwise preserve the gap and ask about the actual missing decision.

Use `migrate --working-id <id> [--note <project-relative-note>]` for legacy records.
Verified originals are retained with `.migrated` suffixes; failures restore inputs.
Never reset execution grants or the original-turn discussion repair allowance.

Before explicit contract confirmation, the agent reviews goal, scope, behavior, exceptions
and acceptance against the actual adopted contract. Supply `completeness_review`
to `record`, with those five keys, each containing bounded `source_ref` and
`evidence` text. This is sourced review evidence, not user authorization. Empty
contract cells cannot confirm; missing review leaves the file working and the
agent continues the completeness review without asking for redundant approval.

## SPEC update visibility

Every successful SPEC save, including a working revision, must be reported in that
turn with a clickable canonical SPEC ID/title link, actual revision and lifecycle
status, a short change summary and the current execution authorization state.
A failed save must be described as failed; never claim that an unpersisted change
was saved. Link the same canonical file through reopening and confirmation.

For each new turn, use `observe` to register identified items and reviewed source
references before `record`; map every accepted item to an actual DEC row through
`item_bindings`. Summary text cannot replace those mappings. Follow
[the discussion entry contract](references/discussion-entry.md) for task root
binding, carried unsaved items, idempotent saves and unverified hook observations.
For missing acceptance mappings, keep saving the SPEC independently and follow
[managed delivery](../implement/references/managed-delivery.md) for a retained
pending application and its restricted additive repair. Do not demand repeated
approval for the same still-valid contract.


## Version compatibility before continuing (SPEC-0035)

On resume or reload, inspect the router's `compatibility` report before dependent
operations. The loaded rules/manifest digest, supported state format, SPEC contract
history, retained authority and validation input hashes key the owner's cache.
Changed inputs or a missing/corrupt record trigger a full inventory; only an
unchanged verified record may be reused. Present the version, inventory and next
action when a full scan runs. Do not treat a version label or cached PASS as an
execution receipt or as acceptance evidence. Existing admission always reruns.

The managed `compatibility` operation takes the usual task, spec and working
reference and never grants product authority. It can run while execution is
blocked; unknown history keeps diagnosis and specification saving available.
A legacy receipt without `journal_tip` can be read compatibly only when the owner
reconstructs its original document bytes and matches BOTH old file hashes, then
proves the suffix consists solely of unchanged-snapshot discussion events. Preserve
the original receipt/source. Matching revision or snapshot alone is insufficient;
unknown historical serializers, tampering, changed contracts and revocation never
become permission. A stale older application must not invalidate a separately
verified current application, and must never itself be reused.

For a deterministic same-scope gap, use the existing acceptance planner and
`repair-acceptance`, or reviewed additive `prepare-validation`, preserve original
inputs/hashes and recovery evidence, then replan and retry the original grant.
Do this automatically within the retained scope; do not ask for the same grant
again. The compatibility inventory does not infer arbitrary missing settings,
reduce thresholds, select an ambiguous SPEC or approve firmware/device actions.
If equivalence cannot be established, report the concrete gap and return to
investigation/discussion. Keep rejection evidence and never overwrite concurrent
changes, clear receipts, or fabricate a successful validation.
