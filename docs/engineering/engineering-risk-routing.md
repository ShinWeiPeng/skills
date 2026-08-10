Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/engineering-risk-routing)

## What it does

`engineering-risk-routing` classifies an engineering task and returns the gates that must pass before work continues. Ordered hard triggers take precedence, so missing evidence cannot be downgraded by a softer rule.

It also recognizes exact fresh-task `開始執行` as a confirmed-spec resume intent. A unique confirmed specification proceeds to verification; several candidates require one selection, and no candidate fails closed. Ordinary discussion containing a quoted or negated phrase is not execution authorization.

## When to reach for it

Codex invokes this automatically through the engineering router. Use it directly when you need to inspect the risk class, required gates, PASS/BLOCKED result, or resume target.

## Fail closed

Its leading idea is **preserve the gate**: unavailable architecture, proposal, code-flow, or runtime evidence remains blocking rather than being replaced by a guess.

## Where it fits

This is routing infrastructure behind [ask-matt](https://aihero.dev/skills-ask-matt), not a standalone planning method.
