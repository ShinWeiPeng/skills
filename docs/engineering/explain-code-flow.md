Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/explain-code-flow)

## What it does

`explain-code-flow` guides a reader from governed System and parent views through an end-to-end Flow, then expands only the selected implementation detail. It does not invent high-level architecture when formal governance is missing or stale.

## When to reach for it

Type `/explain-code-flow`, or Codex reaches for it when you ask what code does, how data reaches a sink, where state changes, or why a branch exists.

## Progressive depth

Its leading idea is **zoom deliberately**: begin at the smallest useful L0/L1 view and descend to modules, symbols, or code regions only when the question needs it.

## Where it fits

This is the code-understanding path beside [diagnosing-bugs](https://aihero.dev/skills-diagnosing-bugs) and architecture governance. [ask-matt](https://aihero.dev/skills-ask-matt) selects the appropriate path.
