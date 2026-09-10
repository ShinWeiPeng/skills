Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/clarify-improvement-proposals)

## What it does

`clarify-improvement-proposals` turns an underspecified improvement request into a decision-complete proposal with explicit impact, tradeoff, and validation evidence. It does not silently choose among unresolved product or architecture options.

## When to reach for it

Type `/clarify-improvement-proposals`, or Codex reaches for it when you ask how to improve, refactor, compare, or redesign something. Reach for it before implementation when the requested destination is still ambiguous.

## Decision completeness

Its leading idea is **clarify first**: inspect discoverable facts, ask only for conclusion-changing choices, and keep the proposal blocked until those choices are resolved.

Choice presentation stays in the current mode. Unanswered required choices remain pending without a deadline, including when a tool closes or times out. A mode change is relevant only when a completed proposal is actually ready for implementation; it is never an answer or approval.

## Where it fits

This is the proposal gate before architecture and implementation. [ask-matt](https://aihero.dev/skills-ask-matt) routes modifying engineering work through it when risk requires a proposal.

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
