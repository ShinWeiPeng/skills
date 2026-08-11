# Plugin distribution

The repository has one editable Skill source: `skills/engineering` and
`skills/productivity`. The tracked `plugins/governed-engineering-skills`
directory is only the Plugin shell and intentionally contains no `skills/`
directory.

Assembly removes Claude's `disable-model-invocation: true` frontmatter only from
the OpenAI Plugin copy. The root source keeps Claude's field, while
`agents/openai.yaml` remains the Codex invocation-policy authority. This is a
deterministic packaging normalization, not a second editable Skill source.

## User installation

On Windows, double-click `Install Governed Engineering Skills.cmd` at the
repository root. It performs this fail-closed sequence:

1. Assemble `dist/governed-engineering-skills` from the tracked Plugin shell and
   the promoted root Skill buckets.
2. Validate the formal artifact and distribution contracts.
3. Add a local-only Codex cachebuster to the ignored artifact.
4. Register the repository Marketplace and install
   `governed-engineering-skills@personal`.
5. Open the Plugin page and ask the user to start a new Codex task.

The formal Plugin version remains `0.7.2`; only the ignored local artifact gets
the `+codex.<cachebuster>` suffix. Failures stop before later phases and retain a
bounded log in the operating-system temporary directory.

ChatGPT web does not expose Git Marketplace installation for this personal
account and is not supported by this distribution. No Workspace administrator,
web publication record, or cross-surface invocation evidence is required.

## Optional Git Marketplace

Maintainers may also build the deterministic Codex Marketplace candidate:

```powershell
python scripts/assemble_plugin.py assemble --marketplace-publication
python scripts/validate_distribution.py
python scripts/assemble_plugin.py validate
```

This writes ignored outputs at `dist/governed-engineering-skills` and
`dist/marketplace-release`. The optional publication tree contains the
Marketplace catalog, complete Plugin package, and `publication-record.json`.
The release workflow may publish it to `marketplace-release`; it is not an
editable Skill source and is not needed for local installation.

`skill-compatibility.json` is the Codex capability inventory. A
`codex-compatible` entry names any repository, terminal, tracker, device, or
runtime dependencies. A `blocked` entry prevents release until its dependency
is available or removed.
