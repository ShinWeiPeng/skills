Availability:

SPEC and execution planning share one acceptance-table parser. Evidence may be
absent while planning; that means unverified. A controlled preparation step can
add an empty Evidence column without a second authorization, while preserving
the original event, exact source document, validation definitions and audit chain.
Changes to requirements, thresholds or existing evidence do not qualify.

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/spec-governance)

## SPEC visibility and execution

In every project, the agent establishes and presents the current SPEC before
program changes. Each completed SPEC or reconfirmed revision appears in the reply
with its ID, title, clickable canonical link, scope summary or revision delta, and
authorization status. Opening a panel or saving a file is not a substitute.
The agent waits for your explicit `開始執行`; choosing an option or adding a
requirement does not authorize implementation. A later scope change returns to
SPEC discussion and fresh authorization. SPEC writing may continue while product
changes are paused. This shared plugin workflow does not require project reminders
and does not claim to intercept arbitrary host tools.

## What it does

A complete working specification may retain an existing execution instruction
while missing validation rules are prepared. Only additive validation definitions
are writable in this state. Confirmation of the unchanged contract can resume the
original instruction; product changes still require confirmation and normal
admission. Changed requirements and revoked authorization cannot use this path.

`spec-governance` owns one canonical change-set specification from the first durable decision through verified implementation. Writing or confirming a specification does not itself authorize product execution.

## When to reach for it

Codex invokes this automatically for every repository-modifying engineering change. Use it directly to reconcile, materialize, reopen, validate, or verify the active canonical specification.

## One contract

Its leading idea is **one canonical spec**: requirements, decisions, acceptance criteria, discussion context, and validation evidence stay traceable in one lifecycle.

Required questions are saved with their exact options and a version before presentation. They have no response deadline. Answers are reconciled against that saved version and recorded in Discussion Context; stale or duplicate answers cannot silently clear pending decisions.

## Where it fits

This is the durable contract between grilling, implementation, and review. [ask-matt](https://aihero.dev/skills-ask-matt) routes modifying work through it.

## Discussion remains active while execution is paused

Across new and existing projects, accepting a requirement updates the current SPEC
before implementation. A pause stops product work while later decisions continue
to be recorded. Routing success never grants write permission. Managed delivery
binds explicit execution evidence to the current project, task and specification,
and checks it inside each supported file replacement. Direct host tools remain
outside that boundary; real assistant traces are required in addition to unit tests.

See the [managed delivery contract](https://github.com/ShinWeiPeng/skills/blob/main/skills/engineering/implement/references/managed-delivery.md)
for request examples, supported operations and evidence limits.

## Decisions in the current mode

Default/execution mode must not invoke menu tools, including async questions.
Use numbered text only when host rules permit it; otherwise persist and ask one
concise open text question. Already-active Plan may use a permitted menu after
shared question-policy preflight. Questions have no response deadline. Neither a timeout nor selecting an option grants
execution permission. Higher-priority host interaction rules still apply.

Except for the verified SPEC-0038 preparation transition below, every SPEC revision, including editorial changes and reconfirmation with no
semantic change, requires a fresh `開始執行` covering that revision. Discussion
continues to update SPEC while product work waits. Final evidence updates also
end the previous permission; subsequent product work needs fresh authorization.

## Keep discussion moving

An answer can also contain a scope correction and a technical question. The
workflow handles all three, saves decisions to SPEC, and presents the next
unresolved question in the same turn. Pure factual follow-ups return to the saved
unanswered choice. Waiting requires a presented question, a concrete blocker,
your request to pause discussion, or a complete proposal awaiting authorization.
The completion check uses existing SPEC state and observed presentation evidence;
it does not control the app's final-response behavior or grant execution permission.

Question feedback and alternative revisions remain in the existing SPEC journal.
A failed popup is not automatically resent; changed options receive a new version
before display. Prepared reply checks and actual emitted reply audits are separate;
accepted tool requests and presentation files do not prove visible delivery.

Project verification requirements now follow the current specification across reloads and short continuation commands. The workflow distinguishes implementation progress from acceptance: missing hardware evidence cannot be replaced by host tests or a successful build. The shared validation plan records the applicable layers and their evidence sources.

## Test and evidence boundaries

Tests now have explicit Module or Flow ownership under `tests/`. Authored validation
plans stay under `validation/`; each execution keeps its own immutable run under
`artifacts/`. This keeps specifications readable and prevents later runs from
replacing the evidence they cite. Whole-project checks include existing files and
report misplaced files and broken references. Layout does not impose language
analysis, dependency or isolation proofs; independent architecture and runtime
verification requirements remain applicable; project-specific retention and Git ignore choices remain separate.

## Discussion is saved from entry

Engineering work automatically starts or resumes a task-specific working record,
including diagnosis and code explanation. Grilling manages that discussion while
specialist skills provide facts. Questions are reserved for decisions the user
must make. A saved explanation does not need a formal SPEC; an adopted change with
complete scope and acceptance does. Suggested changes remain candidates until
accepted and do not expand authorization.

The candidate plugin includes prompt, resume, pre-tool and Stop hooks. Review and
trust their exact definitions before activation. Missing discussion can trigger
one automatic continuation for an actual input state. Unchanged failures do not
loop, and restarting does not erase retry history. Failed saving reports the missing
scope and ends the reply normally; discussion and recovery can continue. After a
repair, saving and rechecking can succeed in the same task. Product changes still
require a current SPEC and execution authorization. Reply wording differences do
not count as missing requirements. Script tests alone do not prove desktop hooks were loaded
or fired. The covered tool paths are Bash, exec_command and file edits; other tools, hosted
search, streamed text and interruptions have explicit coverage limits.

## Bounded diagnosis and recovery

Separate discovered skill names, callable CLI capabilities and actual check
verdicts. `test-validation-layout` resolves to the validated `architecture_cli.py
layout` result; a callable FAIL or BLOCKED remains a failed or blocked check.
An explicit caller capability limit is never expanded by discovery.

A blocker records category, original evidence, affected branch, repair suggestion,
authorization requirement, reproducible recheck, success condition and resume target.
Investigate discoverable facts and prepare the concrete repair first. Reuse current
authorization for deterministic repairs within the confirmed contract; ask only
for missing decisions, authority or external conditions. Never change acceptance
thresholds or replace required runtime evidence with host results.

Managed `recover` stores branch state beside the existing execution receipt. It
checks the same task/SPEC binding, reserves each attempt before effects, and allows
at most three attempts and 120 seconds per input cycle. Identical failed inputs
require evidenced temporary failure to retry; changed actual inputs or repair
start a new bounded cycle while preserving history. Unsupported rechecks remain
investigation, never success. Existing discussion repair allowances are untouched.

Discussion starts in one `specs/SPEC-####-*.md` working file. Each new answer updates that file; confirmation keeps its ID and path. Decisions, pending discussion, completeness gaps and source history remain together. New discussions do not create a parallel WORKING-SPEC/journal pair.

Before contract confirmation, the agent reviews goal, scope, behavior, exceptions
and acceptance against the actual adopted contract. For a settled adopted scope, present the complete proposal and obtain explicit user confirmation. Supply `user_confirmed` and its observed `confirmation_source_ref` together with `completeness_review`. Pass that review
to `record`, with those five keys, each containing bounded `source_ref` and
`evidence` text. This is sourced review evidence, not user authorization. Empty
contract cells cannot confirm; missing review leaves the file working and the
agent continues the completeness review without asking for redundant approval.

## Visible specification updates

Each saved working or confirmed SPEC update includes a clickable canonical link,
revision, status, change summary and execution authorization state in the reply.
Failed saves remain explicit so you can tell what was actually persisted.

## Every decided item stays traceable

Each new engineering turn explicitly reviews its sources and identified items.
Accepted items must map to saved decision rows; a summary mentioning only some of
them cannot pass synchronization. Unsaved items carry forward, while unchanged
observations do not duplicate decisions. Continuing discussion keeps one working
SPEC until an explicit confirmation step. An explicit task root binding lets a
parent workspace and its selected child repository use the same document.

Hook observations report their runtime and task identity separately from host
trust, loading and firing. Manual saves and simulated events cannot prove desktop
hook enforcement; missing real evidence remains unverified.

Distinct accepted items need distinct saved decision rows with matching sources. An unrelated non-engineering reply keeps earlier engineering obligations pending until they are saved.


## Version compatibility

When the plugin or governance inputs change, the workflow inventories the current
SPEC, retained authorization and validation settings before continuing. Unchanged
verified inputs reuse the inventory; execution admission still runs. The report
separates readable state, proven legacy authorization, unusable historical grants
and validation definitions requiring checks or preparation.

Known equivalent repairs stay within the existing authorization. A legacy receipt
is preserved and accepted only after its original byte hashes and continuous
unchanged discussion suffix are proven. Missing history cannot be replaced by a
matching revision number. Unknown or scope-changing repairs return to discussion;
format migration never counts as validation success or device authorization.

## Discussion, confirmation and correction

The shared workflow restores the relevant decision history and pending question,
then presents a complete proposal for explicit user confirmation. A completeness
check does not confirm it automatically. Decision choices have at least three
meaningful alternatives; numeric and clear free-text answers are supported.

SPEC saving uses a short shared lock with a 30-second maximum wait and rereads the
latest version before saving. A SPEC revision requires fresh execution authority unless the verified SPEC-0038 preparation exception below applies.
With an unchanged confirmed SPEC, implementation and correction use one managed
entry. The result a change must produce is checked after that change. Definitions
are rebuilt from SPEC; missing verification selectors or evidence remain explicit
and cannot be reported as completed acceptance.

See [spec-governance](https://aihero.dev/skills-spec-governance) for the shared
responsibility and [implement](https://aihero.dev/skills-implement) for execution.

## Review the validation plan before confirming

The assistant prepares the readable validation methods and tool selections from
the same SPEC. Missing selections are listed together before confirmation, while
drafts can still be saved. A generated mapping is not a complete plan or passing
test evidence. Explicit user waivers are recorded with their scope and source and
shown separately from tests that passed; other evidence remains required.


## Verified preparation continuation (SPEC-0038)

Complete AC prose and machine-readable selectors together before presenting a
decision-complete proposal. Reloaded discussion context reports every selector gap;
confirmation checks the plan again. Saving drafts remains available.

The sole revision exception is a retained, unrevoked pending grant whose missing
scenario selectors are uniquely determined by explicit SPEC-scoped project rules.
Use managed prepare-validation with acceptance_mapping: true. The SPEC owner
derives the additions; delivery reserves original bytes, input hashes and a
versioned transition proof before reconciliation. Verify the entire document and
ordered journal, then confirm and retry the original event through full admission.
A preparation PASS never grants product or device authority or acceptance PASS.

Capture original validation definitions with the pending grant. Existing rules,
scenarios and layers remain exactly equal; only independent definitions may be added.
Legacy recovery requires grant-bound validation history and original_document_hex
matching both retained file hashes. Missing original definitions stay unverified.
Unprovable history, ambiguous scenarios, modified existing values, definition drift,
reopen, revocation and unrelated identities remain denied with their cause. Preserve
old receipts and source events. Generic reconcile and same-ID contract changes are
not covered by this exception. Missing claims, rationale or build selections still
require an evidenced specification decision; do not guess them.

## Automatic preparation and execution continuation (SPEC-0039)

Use managed `continue-execution` as the parent entry after explicit execution
authorization and on same-scope retries. Supply the actual `source_event_id`,
original `instruction`, reviewed `expected_hash`, and the usual task/SPEC/working
references. The parent retains the same event while deriving missing AC scenario
selectors, saving transition evidence, confirming through the SPEC owner,
retrying full admission, generating the acceptance projection and checking planning.
Do not stop at a child `next_action`, or ask again merely because preparation
changed a file. Hashes still protect concurrency and integrity; the owner-derived
transition proves the allowed scope.

Optional `preparation_patches` holds at most four reviewed additive definition
patches handled by existing `prepare-validation`. Never invent ambiguous scenario,
claim, rationale, threshold or build selections. Optional `continuation` is exactly
`{"operation":"status"}` (default) or `{"operation":"apply","patch":{...}}`.
The latter runs the reviewed managed replacement after readiness checks. A status
continuation means implementation is admitted, not that code was written: resume
the implementation workflow in the same turn, then test, repair within scope,
review and call `complete` with actual acceptance evidence. Build, device and
release actions retain their own operation-specific requirements.

The parent saves product continuation checkpoints and rechecks receipts/target
hashes on replay. Owner transition journals and grant history are preparation
checkpoints. Identical deterministic preparation blockers are returned without
repeating effects; changed real inputs permit re-evaluation. External planning
conditions are rechecked instead of cached as permanent failures. Concurrent or
revoked state never authorizes a blind retry.

Legacy migration searches persisted authorization history for matching original
event, binding and instruction, verifies original document hashes and validates
the saved definition baseline, then appends a versioned migration record retaining
the old application. This is caller-attested local evidence, not host-authenticated
approval. It cannot reconstruct never-recorded data: report `legacy-baseline-missing`
with the missing evidence, preserve the original record and investigate. If a real
new user authorization already exists, bind that event to the current reviewed
specification without requiring the missing old baseline; never manufacture one
from a reload, quotation or automatic retry. Superseded events cannot regain authority.

Report authorization validity, admission, source event, bound revision/hash,
reason, next action and source trust separately. Preparation/admission success
does not imply acceptance success. Ask only when a genuine user decision or missing
authority remains, not to compensate for a recoverable preparation gap.

## Maintained document collections

Each design has one maintained Markdown source. The compact SPEC entry points to
requirements, acceptance, discussion and fixed design versions. The SPEC owner
checks the full collection and preserves confirmed history. Interrupted updates
retain original bytes and current authority so the cause can be repaired and the
original update completed without overwriting later edits.

## Design candidate staging

Use the SPEC owner document_candidates.py JSON entry to save affected candidates before confirmation. Each immutable candidate path includes its content hash. The owner advances the working revision and embeds a derived collection digest in the authored Solution; confirmation and execution therefore bind every fixed reference, including a changed source index. Formal current designs and generated products still require the execution grant. Architecture-owned update/resume entries check the confirmed collection, versions and all resulting views.
