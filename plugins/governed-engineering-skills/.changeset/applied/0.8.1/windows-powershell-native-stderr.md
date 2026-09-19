---
"governed-engineering-skills": patch
---

Treat Codex native command exit codes as authoritative on Windows PowerShell 5.1
so successful stderr diagnostics do not abort Marketplace installation, while
preserving actionable stderr when Codex returns a failure.
