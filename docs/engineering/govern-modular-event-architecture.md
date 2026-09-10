Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/govern-modular-event-architecture)

## What it does

`govern-modular-event-architecture` makes module boundaries, ports, events, named types, runtime state, algorithms, and scheduling claims explicit and machine-checkable. The editable manifest is authoritative; rendered views are derived evidence.

## When to reach for it

Type `/govern-modular-event-architecture`, or Codex reaches for it whenever an engineering change affects architecture, ownership, algorithms, execution units, or real-time claims.

## Prerequisites

The repository needs supported architecture governance or must be bootstrapped through the skill before architectural source changes proceed.

## Authoring first

Its leading idea is **ownership before code**: settle boundaries, type and state authority, dependency direction, and applicable scheduling evidence before implementation.

## Where it fits

This is the formal architecture gate used by [clarify-improvement-proposals](https://aihero.dev/skills-clarify-improvement-proposals), [explain-code-flow](https://aihero.dev/skills-explain-code-flow), and [ask-matt](https://aihero.dev/skills-ask-matt).

## Decisions in the current mode

Execution-mode decisions use numbered text options, accepting a number or a
free-form answer without a deadline. A conversation already in Plan mode keeps
its available choice surface. Neither a timeout nor selecting an option grants
execution permission. Higher-priority host interaction rules still apply.

Every SPEC revision, including editorial changes and reconfirmation with no
semantic change, requires a fresh `開始執行` covering that revision. Discussion
continues to update SPEC while product work waits. Final evidence updates also
end the previous permission; subsequent product work needs fresh authorization.
