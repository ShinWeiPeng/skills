# ADR-0007: Isolated plugin SemVer lifecycle

- **Status:** superseded by ADR-0013
- **Date:** 2026-07-31

## Context

The repository previously versioned the private upstream `mattpocock-skills`
root package with Changesets while the governed Codex plugin used a separate
compatibility lifecycle. Only the plugin is maintained, installed, and
published. Keeping the unused root release unit makes root Changesets interpret
plugin files as root package changes and reject valid plugin pull requests that
do not contain a duplicate root changeset.

## Decision

Give `governed-engineering-skills` its own private package metadata, changeset
records, changelog, release fingerprint, and alpha/beta/RC/stable state
machine. Make it the repository's only release unit. Remove root Changesets and
Node release dependencies, validate plugin metadata directly with the Python
governance CLI, and apply pending intent through an automated Version pull
request on `plugin-release/main`. Create the immutable plugin version tag only
when it is absent.

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
- Dual root/plugin release ledgers: rejected because the root package is not
  published and duplicate empty root changesets add no release information.
- Path-based root validation exemption: rejected because repository-level
  specifications can accompany a plugin change and make ownership ambiguous.
- Version-only manifest edits: rejected because they provide no changelog,
  transition validation, or evidence binding.
- A second public governance CLI: rejected; version scripts remain a
  release-automation adapter while `architecture_cli.py` remains the only
  architecture-governance CLI.

## Benefits, costs, and tradeoffs

The plugin retains visible maturity stages and reproducible promotion evidence
while pull requests no longer require root empty changesets. Removing the Node
release dependency reduces CI time and supply-chain surface. The cost is that
the upstream root package no longer receives new versions or tags.

## Risks and mitigations

- **Drift between package and plugin manifest:** CI requires exact equality.
- **Accidental local cachebuster release:** CI rejects build metadata.
- **Stable release differs from RC:** the production fingerprint must match.
- **Self-approval:** stable and `1.0.0` gates reject AI approver identities.
- **Duplicate tag attempts on non-release pushes:** the workflow checks the
  remote tag before invoking the strict tag writer and never moves an existing
  tag.

## Compatibility and migration impact

Existing root versions, tags, and remote branches remain historical and are not
rewritten or deleted. No npm package is published; plugin package metadata
exists only for version governance. The plugin ID, installation path, SemVer
policy, changelog, and `governed-engineering-skills@<version>` tag format remain
unchanged.

## Validation

- Unit-test every legal and illegal version transition.
- Validate package, manifest, changelog, state, changeset, fingerprint, evidence,
  and approval consistency in CI.
- Verify active release automation contains no root Changesets or Node release
  dependency and only selects open `plugin-release/main` pull requests.
- Verify existing version tags are skipped and missing tags are created exactly
  once.
- Run plugin integration validation and both architecture release gates.

## Approval

- **Approver:** pending non-AI review
- **Approval date:** pending
- **Approval reference:** pending
