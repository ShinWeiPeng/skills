Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/ask-matt)

## What it does

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

Execution-mode decisions use numbered text options, accepting a number or a
free-form answer without a deadline. A conversation already in Plan mode keeps
its available choice surface. Neither a timeout nor selecting an option grants
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
