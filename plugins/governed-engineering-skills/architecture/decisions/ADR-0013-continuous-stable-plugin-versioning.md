# ADR-0013: Continuous stable plugin versioning

- **Status:** accepted
- **Date:** 2026-08-05
- **Supersedes:** ADR-0007, ADR-0009

## Context and problem

The personally maintained governed plugin used alpha, beta, RC, release-group
selection, promotion evidence, and stable approval even though it has one owner
and no separate prerelease audience. The state machine made each ordinary
release carry maturity decisions and evidence fields that did not change the
owner's deployment decision.

The plugin-only release authority, changeset-backed intent, automated Version
pull request, synchronized metadata, production fingerprint, and immutable tags
remain useful independently of maturity stages.

## Decision

Use stable-only `MAJOR.MINOR.PATCH`. Formal versions reject prerelease and
general build metadata; the existing local-only `+codex.local-*` manifest
cachebuster remains supported outside CI.

Every release-affecting change declares a changeset bump. The highest pending
bump determines the next stable version. Release intent contains only the bump,
the complete pending changeset IDs, and structured changelog summary. Remove
target stage, release group, risk-promotion, approval, validation evidence,
final-RC fingerprint, and blocker fields from the current release contract.

Retain the plugin-only Version pull request on `plugin-release/main`, atomic
metadata updates, and immutable `governed-engineering-skills@<version>` tags.
Authorize exactly one migration from `0.5.0-beta.6` to `0.5.0`; do not accept
other prerelease versions and do not rewrite historical release artifacts.

## Alternatives considered

- Keep staged prereleases: rejected because the sole owner receives no maturity
  signal worth the additional branches and evidence maintenance.
- Force `0.5.0-beta.6` directly to `0.6.0`: rejected because `0.5.0` has never
  been released stable and stabilization is already a monotonic SemVer advance.
- Remove release intent and Version pull requests: rejected because atomic
  metadata generation and review remain valuable even without maturity stages.
- Retain obsolete fields but ignore them: rejected because silent compatibility
  fields make the active contract ambiguous.

## Benefits, costs, and tradeoffs

Release decisions become one bump with no separate maturity state. Intent and
state are smaller, tests cover fewer branches, and every published tag is a
stable version.

The cost is an incompatible release-tooling contract: old stage-bearing intents
and CLI flags fail validation. Historical ADRs, tags, changelog entries, and
validation reports remain readable but are no longer active policy.

## Risks and mitigations

- **Accidental prerelease reintroduction:** the parser and repository tests
  reject every prerelease except the exact authorized migration input.
- **Wrong bump across multiple changesets:** intent and application recompute
  the highest declared bump.
- **Partial metadata release:** Version PR generation continues to update
  package, manifest, changelog, state, fingerprint, and applied changesets
  together.
- **Moved tags:** the existing tag writer and workflow refuse to move a tag.
- **Unreviewed change quality:** functional, integration, architecture, and
  release gates remain required even though they are not promotion-state fields.

## Compatibility and migration impact

Plugin ID, installation path, Version PR branch, tag prefix, source ownership,
Modules, Ports, Events, Types, State, dependencies, and execution behavior do
not change. The release-tool CLI keeps `check`, `fingerprint`, `apply-intent`,
`next`, `promote`, and `tag`; `next` and `promote` no longer accept stage,
risk, approval, evidence, compatibility-ADR, or new-release-group inputs.

The explicitly authorized one-time migration commit converts
`0.5.0-beta.6` to `0.5.0` and rewrites the current release state to schema
`2.0` before pushing `main`. Later releases continue through the automated
Version pull request. Historical prerelease artifacts are not modified or
deleted.

## Validation and observable pass conditions

- Stable parser and transition tests reject prerelease and build metadata.
- Migration tests prove only `0.5.0-beta.6` can stabilize to `0.5.0`.
- Mixed changeset tests prove the highest bump wins.
- Intent tests reject every obsolete stage and promotion field.
- Repository fixtures prove atomic metadata, archive, fingerprint, and tag
  behavior.
- Version governance, integration validation, workflow contracts, architecture
  render/check, development/release gates, and diff hygiene pass.

## Approval

- **Approver:** human project owner
- **Approval date:** 2026-08-05
- **Approval reference:** Codex task selection “選 1，開始執行”
