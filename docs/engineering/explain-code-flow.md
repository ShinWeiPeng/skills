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
