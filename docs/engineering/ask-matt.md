Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/ask-matt)

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

The router keeps an authorized change moving through preparation, implementation
and validation. It reuses retained authorization for missing validation definitions
and declared enablement checks, while keeping final evidence requirements intact.
A repairable setup gap is work to complete, rather than a reason to ask the user
for the same approval again.

`ask-matt` is the automatic router over the engineering skills in this repo. It assesses the repository state and risk, starts the canonical spec when work will modify the project, then sends the request into the required workflow.

It does not replace the focused skills. Its work is orchestration: determine the entry state, preserve required governance gates, and invoke the focused skill that performs the diagnosis, interview, implementation, review, or validation. Read-only questions remain read-only; only modifying work with an unresolved decision enters `grilling`.

## When to reach for it

The model reaches for `ask-matt` automatically on software-engineering requests; you may still invoke it explicitly. Use an explicit invocation when you want to inspect or discuss the routing decision itself.

In a new task, exact `開始執行` resumes a sole confirmed specification without repeating the interview. Add its canonical `specs/SPEC-####-<slug>.md` path when more than one confirmed specification exists. Quoted or negated uses of the phrase do not authorize execution.

After specification verification, the router passes modifying work through formatter governance. A canonical SPEC may trigger one confirmation for a clean full-program formatting write; formatter selection, installation permission, and CLI check evidence remain inside that gate before TDD or implementation begins.

## Flows, not just skills

The idea `ask-matt` gives you to think with is the **flow** — a path *through* the skills rather than a single one. Most work runs along one **main flow** (idea → ship: grill → spec → tickets → implement → review), two **on-ramps** merge onto it (a triage lane for incoming bugs and requests; a codebase-health lane that generates ideas), and everything else is a **standalone** you reach for on its own. Ask a question and you get placed on the right flow, at the right step — not just handed a tool.

Every turn reloads the task-bound working specification. A saved question survives short answers, interruptions and question-tool timeouts; factual follow-ups can continue without clearing it. Governed delivery checks the current specification and the original explicit execution instruction before writing.

## Where it fits

`ask-matt` is the **router** — the standalone map that sits over the whole set. It is the node every other docs page links back to as [ask-matt](https://aihero.dev/skills-ask-matt), so it never sits *in* a chain; it points *into* every chain. From here you'll most often land on [grill-with-docs](https://aihero.dev/skills-grill-with-docs), the head of the main flow, or [triage](https://aihero.dev/skills-triage), the on-ramp for work you didn't create. When even the router's own picture is stale, its [Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/ask-matt) is the map of record.

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

## Visible specification updates

Each saved working or confirmed SPEC update includes a clickable canonical link,
revision, status, change summary and execution authorization state in the reply.
Failed saves remain explicit so you can tell what was actually persisted.

The router uses the task's explicit project binding, so a parent desktop workspace
does not create a second SPEC beside its selected repository. It hands each new
engineering turn to source/item review and persistence. Valid execution approval
can remain pending during restricted acceptance-map repair; it does not grant
product access until full admission passes.

The workflow remains discussion → specification confirmation → execution authorization → implementation → verification → completion. Save every discussion turn in the same canonical SPEC; an unchanged turn does not increment its revision. A complete sourced review confirms an adopted contract in place, without an additional flag. Confirmation does not grant execution authority.
