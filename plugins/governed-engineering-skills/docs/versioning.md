# Plugin versioning

The governed plugin uses **stable-only SemVer**:

```text
MAJOR.MINOR.PATCH
```

Formal versions never contain alpha, beta, RC, or general build metadata.
A local Codex reload may temporarily append exactly one
`+codex.local-<timestamp>` cachebuster to `.codex-plugin/plugin.json`; CI
rejects that suffix, and it never changes the package version or release tag.

## Compatibility numbers

- `MAJOR` changes after `1.0.0` when a public CLI, schema, data contract, or
  behavior becomes incompatible.
- `MINOR` adds compatible behavior. Before `1.0.0`, incompatible public changes
  also increment MINOR.
- `PATCH` fixes behavior without changing a public contract.

Every release-affecting change declares its bump in a plugin changeset. When a
release contains multiple changesets, the highest declared bump wins:
`major > minor > patch`.

## Continuous release flow

The plugin is the repository's only active release unit. Its private
`.changeset` directory owns release intent, applied changesets, and release
state; the repository root has no package version, Changesets state, or Node
release dependencies.

Each release-affecting plugin change adds a changeset. One
`.changeset/release-intent.json` lists:

- the resulting bump;
- every pending changeset ID exactly once;
- a structured changelog summary.

Stage, release-group, risk-promotion, approval, and validation-evidence fields
are invalid. Functional, integration, architecture, and release gates still run
as ordinary change validation; they are not inputs to a maturity-stage state
machine.

After a feature change reaches `main`, the Version workflow applies the isolated
plugin intent and commits the synchronized package version, plugin manifest,
changelog, release state, production fingerprint, and applied changesets to
`plugin-release/main`. It creates or updates one open plugin Version pull
request. After that pull request is merged, the workflow creates
`governed-engineering-skills@<version>` only when the immutable tag does not
already exist.

## One-time migration

The authorized lifecycle migration converts `0.5.0-beta.6` to stable `0.5.0`.
It does not rewrite or delete historical prerelease tags, changelog entries,
validation reports, or remote branches. The migration exception is exact;
other prerelease versions remain invalid.

After migration, releases progress normally:

```text
0.5.0 --patch--> 0.5.1
0.5.1 --minor--> 0.6.0
0.6.0 --major--> 1.0.0
```

## Validation

Keep `package.json`, `.codex-plugin/plugin.json`, `CHANGELOG.md`,
`.changeset/release-state.json`, changesets, release intent, and the production
fingerprint consistent. Run:

```powershell
python scripts/version_governance.py check
```

Resolve a supported Python 3 runtime first. CI does this with
`actions/setup-python`; an older `python` already present on a workstation is
not a supported fallback.
