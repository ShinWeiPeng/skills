---
"governed-engineering-skills": patch
---

Fix the Windows one-click installer so automatic Python discovery works when the
launcher is invoked without `-PythonCommand`. Prefer the executable Codex Desktop
PATH CLI when it can execute, fall back to the Codex Desktop runtime when it cannot,
and cover both user paths with
regression fixtures.
