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
