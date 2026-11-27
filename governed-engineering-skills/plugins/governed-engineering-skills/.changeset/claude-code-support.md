---
"governed-engineering-skills": minor
---

Support Claude Code alongside Codex. The Windows and Linux launchers can now install for Codex, Claude Code, or both: double-clicking asks, `-Target`/`--target` chooses from a terminal, and non-interactive runs still default to Codex. The Claude Code path uses an existing `claude` CLI to add or update the `mattpocock` Marketplace from `ShinWeiPeng/skills` and install `mattpocock-skills` at user scope; it does not install Claude Code itself and points to the setup guide when `claude` is missing.

Skills now hand off with neutral wording ("the `skill-name` skill") instead of Codex-only `$skill-name` calls, and describe the agent rather than Codex as the actor. Question policy accepts Claude Code's `AskUserQuestion` as a structured menu under the unchanged Plan-only menu rule, and architecture governance now rejects `Claude` as an AI approver. The Claude plugin manifest points to `ShinWeiPeng/skills` and moves to 1.4.0.
