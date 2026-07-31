# ADR-0007: Isolated plugin SemVer lifecycle

- **Status:** proposed
- **Date:** 2026-07-31

## Context

The repository already versions the upstream `mattpocock-skills` package with
Changesets. The governed Codex plugin has a separate compatibility lifecycle,
and repository-wide Changesets prerelease mode would place unrelated packages
into the same beta state.

## Decision

Give `governed-engineering-skills` its own private package metadata, changeset
records, changelog, release fingerprint, and alpha/beta/RC/stable state
machine. Keep the root Changesets workflow for the upstream package and invoke
the plugin's deterministic validation and tag adapter from the same Version
workflow.

Use `MAJOR.MINOR.PATCH[-STAGE.NUMBER]`. MAJOR and MINOR changes pass through
beta and RC. Low-risk PATCH releases may be stable directly; high-risk PATCH
releases pass through RC. A feature added after RC opens the next release group
because returning to a same-base beta would be a SemVer downgrade.

Stable promotion requires matching final-RC production fingerprint, reinstall
and new-task evidence, no open blocker, and non-AI approval. Version `1.0.0`
additionally requires an accepted compatibility ADR.

## Alternatives considered

- Repository-wide Changesets prerelease mode: rejected because prerelease state
  is shared and would affect unrelated packages.
- Version-only manifest edits: rejected because they provide no changelog,
  transition validation, or evidence binding.
- A second public governance CLI: rejected; version scripts remain a
  release-automation adapter while `architecture_cli.py` remains the only
  architecture-governance CLI.

## Benefits, costs, and tradeoffs

The plugin gains visible maturity stages and reproducible promotion evidence.
The cost is additional private package metadata and a plugin-specific release
state file.

## Risks and mitigations

- **Drift between package and plugin manifest:** CI requires exact equality.
- **Accidental local cachebuster release:** CI rejects build metadata.
- **Stable release differs from RC:** the production fingerprint must match.
- **Self-approval:** stable and `1.0.0` gates reject AI approver identities.

## Compatibility and migration impact

The current `0.1.0` development line enters `0.2.0-beta.1`. No npm package is
published; package metadata exists only for version governance.

## Validation

- Unit-test every legal and illegal version transition.
- Validate package, manifest, changelog, state, changeset, fingerprint, evidence,
  and approval consistency in CI.
- Run plugin integration validation and both architecture release gates.

## Approval

- **Approver:** pending non-AI review
- **Approval date:** pending
- **Approval reference:** pending
