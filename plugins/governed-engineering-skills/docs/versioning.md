# Plugin versioning

The governed plugin uses:

```text
MAJOR.MINOR.PATCH[-STAGE.NUMBER]
```

## Compatibility numbers

- `MAJOR` changes after `1.0.0` when a public CLI, schema, data contract, or
  behavior becomes incompatible.
- `MINOR` adds compatible behavior. Before `1.0.0`, incompatible public
  changes also increment MINOR.
- `PATCH` fixes behavior without changing a public contract.

## Maturity stages

- `alpha.n` is experimental and may change its interface.
- `beta.n` is feature-complete enough for integration testing.
- `rc.n` freezes features and public interfaces; only release blockers may
  change.
- A version without a suffix is stable.

MAJOR and MINOR releases progress through beta, RC, then stable. A low-risk
PATCH may release directly to stable. A PATCH that changes schema, public CLI,
security, persisted data, scheduling/timing, persistent state, or a gate verdict
must pass through RC.

SemVer ordering makes a same-base transition from RC back to beta a downgrade.
If an RC receives a new feature, open the next release group at `beta.1`
instead. For example, `0.2.0-rc.1` becomes `0.3.0-beta.1`, not
`0.2.0-beta.2`.

## Promotion evidence

RC requires unit, integration, bootstrap, renderer, skill release-gate, and
plugin release-gate evidence. Stable requires the exact final-RC production
fingerprint, reinstall evidence, new-task evidence, no open blocker, and a
non-AI approval reference. `1.0.0` additionally requires an accepted
compatibility ADR.

The package version and `.codex-plugin/plugin.json` version are identical in
formal commits. A local reload may temporarily append exactly one
`+codex.local-<timestamp>` cachebuster to the plugin manifest; CI rejects that
suffix as a formal version.

The plugin owns the repository's only active release lifecycle and keeps all
release records in its private `.changeset` directory. The repository root has no
package version, Changesets state, or Node release dependencies.

Each release-affecting plugin change adds a plugin changeset and
`.changeset/release-intent.json`. The intent names the bump, target stage,
risk, changeset IDs, structured changelog summary, and any approval or
validation evidence. After a feature pull request reaches `main`, the Version
workflow applies the isolated plugin intent and commits the resulting version,
changelog, and release state to `plugin-release/main`. It creates or updates one
open plugin Version pull request. After that pull request is merged, the workflow
creates `governed-engineering-skills@<version>` only when the tag does not already
exist. Pushes with no new release safely leave existing tags unchanged.

Resolve a supported Python 3 runtime before invoking
`scripts/version_governance.py`. CI does this with `actions/setup-python`; an
older `python` executable already present on a workstation is not a supported
fallback.
