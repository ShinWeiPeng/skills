Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/implement)

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

An authorized task continues through validation preparation, implementation and
verification. Missing runtime policy, device profile, verification matrix or layout
definitions can be added under the retained authorization before a receipt exists.
Declared enablement checks can then produce the evidence needed for admission.
Preparation never counts as acceptance, and existing validation values remain
protected. Recoverable setup gaps do not require repeating the same permission.

`implement` builds the work described in a spec or a set of tickets — driving it through test-driven development, typechecking, and the full test suite, then handing off to review and committing to the current branch.

It does **not** decide what to build. The spec is already settled and the seams are already agreed; `implement` executes that plan rather than reopening it. It is the hands, not the head — the thinking happened upstream.

## When to reach for it

You invoke this by typing `/implement` — the agent won't reach for it on its own.

Reach for it once the work is written down as a spec or split into tickets and you're ready to turn that into code. If the spec doesn't exist yet, write it first — for that, use [to-spec](https://aihero.dev/skills-to-spec), or [to-tickets](https://aihero.dev/skills-to-tickets) to break a spec into tickets. If you just want to build something test-first without a full spec, drop to [tdd](https://aihero.dev/skills-tdd) directly.

## Pre-agreed seams

The idea `implement` runs on is the **seam** — the stable interface a feature is tested at, chosen before any code is written. It doesn't invent seams mid-build; it uses the ones already picked (during [to-spec](https://aihero.dev/skills-to-spec)) and writes tests against them via [tdd](https://aihero.dev/skills-tdd). Working at pre-agreed seams is what keeps the implementation honest: the tests target something durable, so the code underneath can move without the tests moving.

Around that core it keeps the loop tight — typecheck often, run single test files as it goes, run the whole suite once at the end — then closes out with a review pass and a commit to the current branch.

Delivery reloads the actual canonical specification and rejects stale verification hashes, pending questions and mismatched task state. The original explicit execution instruction remains the final human checkpoint. This protects the governed plugin entry point and does not claim to intercept arbitrary host tool calls.

## Where it fits

`implement` is the build step near the end of the main chain, just before the review:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review
```

Reach for it after the work has been specced and sequenced, not before. Its key neighbours are [to-tickets](https://aihero.dev/skills-to-tickets), which produces the tickets — each declaring its blocking edges — that it works through, and [tdd](https://aihero.dev/skills-tdd), which it drives internally to write the tests at each seam before running its own [code-review](https://aihero.dev/skills-code-review) pass and committing. When you're unsure which skill or flow fits, [ask-matt](https://aihero.dev/skills-ask-matt) routes you.

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

Every SPEC revision, including editorial changes and reconfirmation with no
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
report missing analyzer coverage. Fixture sharing and test-only hooks have explicit
boundaries; project-specific retention and Git ignore choices remain separate.

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

## Explicit combined execution scope

An instruction such as `開始執行SPEC-0029/0030` can be admitted with a `scope`
array containing each canonical `spec`, `working_reference` and verified
`expected_hash`. The scope must exactly match the explicit IDs. All bindings pass
before one source event is consumed; per-spec receipts remain in the same task
state. A stale contract cannot use its receipt; suspend clears every scope.
Preserve the original instruction and user source event without synthesizing
additional user messages. Legacy single-spec receipts remain readable.

## Visible specification updates

Each saved working or confirmed SPEC update includes a clickable canonical link,
revision, status, change summary and execution authorization state in the reply.
Failed saves remain explicit so you can tell what was actually persisted.

Independent SPEC tasks can run concurrently. Dependencies wait for prerequisite
completion, while same-file conflicts use bounded reread and integration.
Short OS locks release after a crash; long validation does not lock the project.
Recovery rechecks the requested phase and retains prior recovery history.

## When validation preparation is incomplete

A valid execution instruction can remain pending while its acceptance mapping is
repaired. Pending approval grants no product-write permission. Deterministic repair
adds only missing rows explicitly declared by the reviewed SPEC; ambiguous mappings
remain durable drafts. Existing rows, draft history and revocations are preserved.
The tool reruns full admission after repair and reuses the still-valid instruction,
so a preparation failure does not make you approve the same contract again.

Saving a discussion-only suffix preserves current execution authority when the unchanged SPEC snapshot and original audit anchor are verified. Contract changes, revoked authority and broken history still block dependent edits. Legacy receipts without an anchor keep exact-binding checks.


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
