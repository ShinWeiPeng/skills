Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/clarify-improvement-proposals)

## What it does

`clarify-improvement-proposals` turns an underspecified improvement request into a decision-complete proposal with explicit impact, tradeoff, and validation evidence. It does not silently choose among unresolved product or architecture options.

## When to reach for it

Type `/clarify-improvement-proposals`, or Codex reaches for it when you ask how to improve, refactor, compare, or redesign something. Reach for it before implementation when the requested destination is still ambiguous.

## Decision completeness

Its leading idea is **clarify first**: inspect discoverable facts, ask only for conclusion-changing choices, and keep the proposal blocked until those choices are resolved.

## Where it fits

This is the proposal gate before architecture and implementation. [ask-matt](https://aihero.dev/skills-ask-matt) routes modifying engineering work through it when risk requires a proposal.
