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
| Contract or working snapshot changed | Reconcile and verify the current state | Receipt is stale; do not replay an earlier instruction |
| Only discussion history appended | Verify unchanged snapshot and continuous history from the receipt anchor | Preserve the current authorization |

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

The receipt retains project, task, SPEC and snapshot hashes plus the journal tip
observed at authorization. A later binding may differ only by a continuous suffix
of discussion events with the identical snapshot. The original anchor must still
exist; changed requirements, reopened/reconfirmed contracts, rewritten history,
suspension and unrelated tasks remain rejected. No new user event is fabricated.
Legacy receipts without an anchor require exact binding or reconstructed original-byte proof of a discussion-only extension. Concurrent product
writes still require exact current hashes under the existing commit lock.
A single user message may specify and authorize the same change; reconcile it before
admission. Confirmation itself never authorizes product execution.

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

## Composed project validation entrypoint

For a governed project, run existing commands through the composition wrapper so
the demand-owned validation callable is injected:

```powershell
python skills/implement/scripts/project_validation_workflow.py spec -- <spec_contract arguments>
python skills/implement/scripts/project_validation_workflow.py managed -- --project-root <root> --request <request.json>
python skills/implement/scripts/project_validation_workflow.py admission -- <spec_delivery arguments>
```

Use skills/engineering/implement in a source checkout. This is an internal CLI,
not a new skill. Library callers pass validation_assessor explicitly. Without it,
direct governed library/CLI calls fail closed with a remediation message; legacy
host projects with no governance markers retain their previous behavior.

## Explicit combined execution scope

An instruction such as `開始執行SPEC-0029/0030` can be admitted with a `scope`
array containing each canonical `spec`, `working_reference` and verified
`expected_hash`. The scope must exactly match the explicit IDs. All bindings pass
before one source event is consumed; per-spec receipts remain in the same task
state. A stale contract cannot use its receipt; suspend clears every scope.
Preserve the original instruction and user source event without synthesizing
additional user messages. Legacy single-spec receipts remain readable.

## Recoverable synchronization (SPEC-0032)

Historical repair_used/repair_failed flags are audit history, never a permanent
denial. Managed admission still requires the matching current saved discussion with
a PASS synchronization verdict and an
independent valid execution receipt. Stale or missing entry is recoverable through
the spec owner; routing to discussion/diagnosis must remain available. Saving a
new SPEC may invalidate an old execution receipt under the existing binding rules;
recovery never silently restores product authorization.

## Concurrent operations and recovery

Independent SPEC tasks may work concurrently. Before dependent product changes,
require each transitive `depends_on` SPEC to be uniquely identified and implemented;
missing prerequisites or cycles pause only affected work. Managed state uses short
OS-owned locks and optimistic state versions. Locks are released on process exit;
validation runs outside locks. Never delete a live lock file to steal ownership.
For same-file edits, provide optional `before_content` matching `before_sha256`.
The managed patch rereads and integrates disjoint line edits with at most three
commit attempts. Overlaps pause the affected write for a reviewed resolution.
Before a merged commit, composition must supply a candidate_validator that checks
the proposed content outside the lock and returns PASS with its exact SHA-256.
Without this port, the CLI returns a reviewable_candidate and pauses that write.
Validate it with the project tests, reread its base, and submit the reviewed result;
no extra user permission is needed within the same authorized scope. Admission
checks alone do not prove the integrated program's behavior. No retry may overwrite a concurrent edit.
Recovery fingerprints include the validation phase, inputs and success condition.
A fresh valid current-binding grant starts a new recovery cycle and preserves the
previous cycle in history; it never restores stale authority.

## Pending authorization and additive acceptance repair

A valid current execution instruction is retained separately from its receipt when
planning or enablement is incomplete. `authorization_status: pending` always has
`product_code_allowed: false`. Retry the same event and exact contract after fixing
preparation; do not ask for the same approval again. Changed bindings, revoked
applications and different scopes cannot reuse that event. Successful retries of
a previously pending application verify its existing receipt without issuing another.
Use `authorization-status` with `task_ref` and `source_event_id` to recover the
application, retained draft, and authorization/repair history. This read never grants
product authority. Source IDs remain caller-attested rather than host-authenticated.

`plan-acceptance-repair` is read-only and uses the current canonical SPEC. Automatic
mapping is deliberately limited to explicit machine-readable data in that confirmed
contract's `## Acceptance Mapping` section, a JSON object keyed by AC ID. Each row
contains exactly `evidence_claims`, `contract_dimensions`, `execution_changes`
(string arrays) and a nonempty `rationale`. The owner derives `criterion_sha256`
from the actual criterion. For example:

```json
{
  "AC-001": {
    "evidence_claims": ["host-semantics"],
    "contract_dimensions": ["call-order"],
    "execution_changes": [],
    "rationale": "The reviewed host contract requires a call-order test."
  }
}
```

Do not add or infer that declaration merely to get past a gate. If the reviewed
contract does not determine a mapping, submit the bounded candidate as a draft;
`repair-acceptance` retains it with its binding and reason without applying it.
A caller's `deterministic` flag is not evidence. More complex or stale existing
mappings require review; this additive route does not rewrite or lower them.

To apply a deterministic plan, send `operation: repair-acceptance`, the current
`task_ref`, `spec`, `working_reference`, retained `source_event_id`, and the exact
`patch` returned by the planner. Only `validation/acceptance-SPEC-####.json` is
eligible. Existing rows remain unchanged; old target hashes, redirects, different
content and unrelated paths are rejected. Interrupted attempts retain their inputs;
a matching committed result can be rechecked without rewriting it.

Repair success reruns all admission checks and does not mean acceptance passed.
If the verification plan is stale, regenerate it through the planning owner and
retry the retained application; do not reset receipts or invent a new user event.
Normal `recover` still requires an effective current receipt. Suspension preserves
history and drafts while revoking authority.

## Continue preparation through implementation and validation

A retained current authorization also admits `prepare-validation` for additive
definitions in `architecture/adoption.yaml`, `validation/verification-ladder.yaml`,
`validation/on-device.yaml` and `validation/layout.yaml`. Supply the same `task_ref`,
`spec`, `working_reference`, retained `source_event_id` and one reviewed `patch`
with `path`, `before_sha256` and complete `content`. Reuse facts from the confirmed
contract and project; ask only for a genuinely missing decision. Every existing
value and list prefix is preserved. Adoption edits may only add a required runtime
validation policy. Product code, acceptance results, scope changes, stale hashes
and revoked or mismatched authority remain inadmissible through this operation.

Preparation does not require the receipt whose prerequisites it repairs. It uses
the managed writer's atomic replacement and concurrency checks, then retries the
retained application. `preparation_applied` records only a definition write;
inspect the nested `admission` result. Continue remaining preparation on
`continue-validation-preparation`; on `resume-implementation`, verify managed
status and continue source edits and checks without a new user event. A retry of
an interrupted write first rereads the target; never overwrite a stale base.

When declared enablement scenarios themselves need to run before admission, use
`enablement-status` with the same binding and source event. It requires passing
planning and layout, not the enablement evidence being produced. A PASS grants
only `enablement_allowed`; execute the declared bounded preparation checks and
save their evidence using the existing validation owner. This is not firmware
write, flash, device-action or acceptance authority. Reuse separately established
device authorization for the same scope; ask only if it is actually missing.
Retry the retained application after recording enablement evidence, then continue
implementation, build/tests, authorized device checks and `complete`. Never end
the task merely because a recoverable preparation item was discovered. Full
acceptance/release still requires the existing evidence gates; a passing
preparation result cannot substitute for real runtime evidence.


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
