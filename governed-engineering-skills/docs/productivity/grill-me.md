Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me)

## What it does

`grill-me` is the greenfield wrapper for the shared grilling workflow. `ask-matt` selects it when both implementation and durable project context are absent.

It asks **one question at a time** and waits. It never dumps a batch of questions at you — that is bewildering — and where a question can be answered by reading the codebase, it goes and reads rather than asking. Each question comes with the agent's own recommended answer, so you are reacting to a proposal, not staring at a blank prompt.

## When to reach for it

The router reaches for it automatically for a greenfield engineering request; you may also invoke it explicitly. If durable project context already exists, use [grill-with-docs](https://aihero.dev/skills-grill-with-docs) instead. If the effort is too large for one session and the route is still unclear, [wayfinder](https://aihero.dev/skills-wayfinder) maps the decisions first.

## The decision tree

The session walks the plan as a tree of decisions, resolving dependencies between them one by one — a parent decision settled before the choices that hang off it. The point is not to reach agreement quickly; it is to make every implicit call explicit, so nothing important is left silently assumed. You come out the other side with a plan whose branches have all been visited.

`grill-me` is **stateless**: it writes nothing and leaves no workspace behind. It runs anywhere, and the only artifact is the sharpened understanding in the conversation itself. That is the deliberate contrast with [grill-with-docs](https://aihero.dev/skills-grill-with-docs), which captures the same interview as durable ADRs and a glossary.

## Where it fits

`grill-me` is the stateless greenfield entry to the [grilling](https://aihero.dev/skills-grilling) primitive. Its closest neighbour is [grill-with-docs](https://aihero.dev/skills-grill-with-docs), which uses durable project context and records domain decisions. The automatic [ask-matt](https://aihero.dev/skills-ask-matt) router chooses between them.
