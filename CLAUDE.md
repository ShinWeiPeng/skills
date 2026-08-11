Skills are organized into bucket folders under `skills/`:

- `engineering/` — daily code work
- `productivity/` — daily non-code workflow tools
- `misc/` — kept around but rarely used, not promoted
- `personal/` — tied to my own setup, not promoted
- `in-progress/` — drafts not yet ready to ship
- `deprecated/` — no longer used

Every skill in `engineering/` or `productivity/` (the **promoted** buckets) must have a reference in the top-level `README.md` and an entry in `.claude-plugin/plugin.json`'s `skills` array (the Claude Code plugin ships exactly the promoted set). Skills in `misc/`, `personal/`, `in-progress/`, and `deprecated/` must not appear in either.

The repo is also its own single-plugin Claude Code marketplace: `.claude-plugin/marketplace.json` lists the one `mattpocock-skills` plugin. Validate `.claude-plugin/plugin.json` with `claude plugin validate . --strict` after manifest changes. Its Claude Marketplace version is independent of the governed OpenAI Plugin SemVer under `plugins/governed-engineering-skills`; there is no root `package.json`. The historical Codex deferral in `.agents/adr/0002-ship-as-a-claude-code-plugin.md` is superseded by `SPEC-0013`.

The governed OpenAI Plugin uses `skills/engineering` and `skills/productivity` as its only editable Skill source. Keep only its manifest, versioning, tests, and release infrastructure under `plugins/governed-engineering-skills`; never commit a second `skills/` tree there. Build `dist/governed-engineering-skills` with `python scripts/assemble_plugin.py assemble --marketplace-publication`, then run `python scripts/validate_distribution.py`. The ignored artifact is the candidate used by manual maintainer testing and to generate the personal Git Marketplace tree; the release workflow alone publishes that tree to `marketplace-release`.

Each skill entry in the top-level `README.md` must link the skill name to its `SKILL.md`.

Each bucket folder has a `README.md` that lists every skill in the bucket with a one-line description, with the skill name linked to its `SKILL.md`. The promoted buckets' `README.md`s and the top-level `README.md` group entries into **User-invoked** and **Model-invoked**; non-promoted bucket `README.md`s (`misc/`, `personal/`) use a flat list.

Skills in `engineering/` and `productivity/` also have a human-facing docs page at `docs/<bucket>/<skill-name>.md` (the docs tree mirrors those two bucket folders under `skills/`). The published URL is `https://aihero.dev/skills-<skill-name>` regardless of bucket — the docs path is repo organisation only. When you add, rename, or change the behaviour of a skill in `engineering/` or `productivity/`, create or re-sync its docs page following [.agents/writing-docs.md](./.agents/writing-docs.md). Skills in the non-promoted buckets (`misc/`, `personal/`, `in-progress/`, `deprecated/`) get **no** docs page.

Every `SKILL.md` is either user-invoked (`disable-model-invocation: true` plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, reachable only by the human) or model-invoked (model- or user-reachable). See [.agents/invocation.md](./.agents/invocation.md).

[`ask-matt`](./skills/engineering/ask-matt/SKILL.md) is the router that maps every user-reachable skill and how they relate. The same trigger that re-syncs a docs page applies to it: whenever you add, rename, remove, or change how a user-reachable skill fits the flows, re-read `ask-matt`'s `SKILL.md` and update it so the map stays accurate — a new skill it never mentions, or a stale one it still routes to, is a router that lies.

For maintainer development only, `scripts/link-skills.sh` can link repository Skills into local harness directories. The supported Windows user path is the repository-root `Install Governed Engineering Skills.cmd`, which assembles, validates, cache-refreshes, registers, and installs the local Plugin for Codex Desktop and CLI. The generated `marketplace-release` branch is an optional Codex-only source; ChatGPT web installation is unsupported.
