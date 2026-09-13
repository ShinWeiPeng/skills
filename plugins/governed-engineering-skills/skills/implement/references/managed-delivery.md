# Managed delivery contract

This contract applies to every project and every later engineering turn. It is
independent of language, framework, project age, and the words in an example.

## Discussion and execution are separate

| Input/state | SPEC work | Product work |
|---|---|---|
| Factual question | Read existing context; no invented decision | Read only |
| Requirement, option adoption or changed acceptance | Reconcile before the next decision; materialize when complete | Await exact execution authorization |
| Stop implementation / not yet authorized | Keep saving later discussion decisions | Suspend immediately |
| Explicit stop all work or stop SPEC writes | Honor that scope; do not continue those writes | Stop as requested |
| Current confirmed contract plus exact execution instruction | Preserve verified contract | Authorize the managed entrypoint |
| Contract, working snapshot or journal changed | Reconcile and verify the current state | Receipt is stale; do not replay an earlier instruction |

Do not say “wait for 開始執行 before updating SPEC.” An execution pause does not
erase accepted decisions. Once an implemented contract needs new requirements,
create a related new working change set rather than editing the immutable spec.

## Observe before acting

Read the actual route result. `PASS` means routing succeeded, not execution
permission. `product_code_allowed` is always false on router results; `next_action`
is the selected skill. Follow `grilling` or `spec-governance` instead of writing.

Run a gate in a separate tool invocation, inspect its result, then select the next
action. Never precompose a router/admission call and an unconditional patch, shell
write, build, installation or device operation in the same `exec`, command chain
or parallel batch. A rejected gate ends the dependent sequence.

## Managed file replacement

Invoke `python scripts/managed_delivery.py --project-root <root> --request <json>`.
Request files are local governance evidence, stored under `spec-governance/`.
Every request names `task_ref`. Authorization, status and apply also name the
canonical relative `spec` and `working_reference`.

Authorize only after observing the user's current exact execution message:

```json
{
  "operation": "authorize",
  "task_ref": "current-task-id",
  "spec": "specs/SPEC-0001-feature.md",
  "working_reference": "WORKING-SPEC-0123456789ab-feature",
  "expected_hash": "sha256-captured-during-spec-verification",
  "instruction": "開始執行",
  "source_event_id": "actual-current-user-message-id"
}
```

Never synthesize an instruction or source ID from a proposal, option choice,
quoted message, old execution turn, timeout or model-generated text. If the host
does not expose an identifiable actual user message, record that limitation and
do not fabricate evidence. IDs and receipts remain caller-attested, not proof of
host-authenticated human approval. Local receipt deletion or malicious rewriting
is outside this plugin's trust boundary.

The receipt binds the resolved project, task, SPEC bytes, working snapshot and
journal. The managed entrypoint rejects reused event IDs in the retained local
history. Every SPEC revision makes this receipt stale, including editorial,
evidence-only and no-semantic-delta reconfirmation. Reverify and wait for a fresh
exact `開始執行` covering the revision; never refresh the binding or reuse an old
message. A single user message may specify and explicitly authorize that exact
change; reconcile it before admission. Finish product checks before recording
final implementation evidence, then perform no further product operations on the
invalidated receipt. Read-only checks and SPEC persistence remain allowed.

After successful authorization, apply one reviewed replacement:

```json
{
  "operation": "apply",
  "task_ref": "current-task-id",
  "spec": "specs/SPEC-0001-feature.md",
  "working_reference": "WORKING-SPEC-0123456789ab-feature",
  "patch": {
    "path": "src/example.py",
    "before_sha256": "hash-of-reviewed-original-bytes",
    "content": "complete new UTF-8 file contents\n"
  }
}
```

Use null `before_sha256` only for create-only targets. Parent directories must
already exist. Each operation is limited to one file and 1 MiB, with no deletion,
rename, binary payload, symlink, VCS or governance-control target. Rejection leaves
the product target unchanged; successful replacement is atomic for that file.
There is no multi-file transaction or protection against out-of-band concurrent
writers. Unsupported edits must not silently fall back to direct tools: state the
limitation and prepare a supported reviewed operation or keep execution blocked.

For a pause, send `{"operation":"suspend","task_ref":"current-task-id"}`.
This clears product authority while leaving SPEC discussion allowed. `status`
rechecks the current binding and reports whether managed execution is admitted.
The project-level lock prevents concurrent managed receipt changes and writes;
lock contention blocks immediately. Investigate an abandoned lock before cleanup.

The older `spec_delivery.py` is a read-only preflight, not a receipt issuer or
write entrypoint. For build, test, Git, deployment and device operations, inspect
current managed `status` in a separate invocation and also enforce their existing
operation-specific authorization. This writer does not execute arbitrary commands.

## Completed SPEC reply evidence

After every materialization or reconfirmation, obtain `turn-context` and use its
`spec_presentation` identity (ID, title, absolute path, revision and snapshot hash).
The observed `spec_presentation` adds `summary`, `status` (`awaiting-authorization`
or `executing`), `stage: emitted`, actual reply `source_ref` and `reply_text`.
The reply contains a rendered Markdown link whose label includes ID and title,
the nonempty summary/delta, and the exact appropriate status sentence from ask-matt.
Do not put the evidence inside code blocks, HTML or comments. Completion verifies
this content rather than accepting a presented flag. Executing status additionally
requires current successful managed status evidence and its matching binding.
It never grants permission itself.

Normalized `proposal_presented` events carry `spec_presentation`; a separate
`reply` supplies the actually emitted text and source reference. A prepared event
cannot claim delivery. Reloading context invalidates earlier presentation.

`--audit-trace` also accepts a version 2 object with `schema_version: 2`,
`project_root`, normalized `events` (each with `source_ref`), and raw desktop
`sources` (each with the original item `id` and `type`). Preserve the original
userMessage, agentMessage, fileChange and commandExecution items. The auditor
cross-checks source coverage and emitted replies, and independently detects raw
direct product file changes even when normalization omits them. Opaque command
effects and incomplete raw evidence are BLOCKED; observed violations are FAIL.
The bounded adapter does not prove arbitrary shell commands safe. Legacy lists
remain normalized-only evidence, never proof of raw trace coverage. Source records
are caller-supplied, not authenticated host events. Retain hashes and provenance.

Managed product protection covers root `specs/` and `spec-governance/`, plus
`.git`, `.codex` and `.agents` at every depth. Ordinary nested source directories
with governance-related names are not this project's control store. Existing
canonical-target, traversal, symlink, junction and shared-file checks remain.

## Evidence and honest limits

`--audit-trace <json>` checks a normalized, observed event list: `requirement`,
`decision`, `spec_saved` (verdict), `pause`, `admission` (verdict and permission),
`managed_write` (verdict), `direct_write`, `gate_and_write`, `read`, `question`,
`timeout`, and `mode_change`. A direct write or gate/write precomposition fails
the audit; pending unsaved decisions fail too. Preserve raw tool IDs and source
file hashes beside the normalized trace. An auditor must check that normalization
matches actual observations; this input is not an authenticated host event stream.

Unit fixtures prove managed code behavior only. Release evidence must additionally
include real multi-turn assistant traces from fresh tasks with new/existing
projects: discussion, adoption, pause, resumed discussion, contract change, fresh
authorization and writing. Missing traces are BLOCKED evidence, not implicit PASS.
Never infer global tool interception from successful managed tests. Direct tools
remain technically callable; their use is a workflow violation, not something
this plugin can prevent at the host boundary.

## Per-turn discussion trace

For discussion evidence, use `turn_start` with recovered `context`, then observed
`decision`/`requirement`, `spec_saved` with verdict and reloaded context, and
`context` after recording the next question. A `question` event supplies `question`
(the complete saved pending question) and `presentation_ref`. A
`proposal_presented` event supplies `presentation_ref`. `discussion_pause` supplies
the original scoped `pause` record; `blocker` supplies the evidenced `blocker`
record, using the finish-turn schema. End every started turn with `turn_end`.
The auditor derives completion from preceding events; a turn_end reason alone
cannot pass. Each new turn clears presentation evidence. Context reloads clear
previous presentation evidence, and working/task identities cannot change mid-turn.

Normalize all components of mixed messages. Preserve raw user/tool/reply references
and verify them independently; omitted or fabricated events cannot establish real
compliance. Legacy write-only traces remain supported but prove no discussion
completion coverage. No host-wide interception is claimed.

Completion observations also include `project_root` exactly as recovered in
turn-context. Context changes invalidate presentation and observed admission;
question count persists until the next turn. Raw source references and pause
interpretation must be checked against the original messages.

## Question tool and reply evidence

Apply ask-matt's Decision Question Contract and spec-governance question-policy
before selecting any question tool. Default forbids menus regardless of availability
or retry. Only an already-active Plan with current host permission may use one.
Record actual host evidence on turn_start.host (mode, mode_ref, policy_ref,
numbered_text_allowed, menu_tool_allowed). Unknown mode does not permit a menu.
A mid-turn mode_change invalidates presentation evidence; it never unlocks Plan.

Normalize every actual question tool invocation as question_tool with tool name,
including accepted calls later followed by correct text. The auditor checks current
mode and saved failed surfaces. A question event additionally supplies presentation
as specified by spec-governance. The auditor forces its stage to prepared; neither
accepted=true nor a draft reference counts as an emitted reply. Record a separate
reply event with actual final text and source_ref before turn_end. The auditor
checks that text contains the current saved question in the permitted form.

Missing/false normalization cannot establish compliance: preserve raw host, tool
and reply source references for independent review. This plugin does not disable
arbitrary host tool calls or authenticate visibility. Unit fixtures are not actual
model observations. Report each evidence category and any missing coverage honestly.
