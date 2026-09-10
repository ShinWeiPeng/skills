Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/spec-governance)

## What it does

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
