# ADR-0014: Personal Git Marketplace publication

- **Status:** accepted
- **Date:** 2026-08-10
- **Supersedes:** the private Workspace publication lane in SPEC-0013 revisions 10-17

## Context and problem

The assembled governed Plugin is ignored under `dist/`, so GitHub `main` cannot be
consumed directly by the personal Marketplace form. The selected product scope is
one personal account using the same Plugin release in ChatGPT Work web and Codex
Desktop, without a managed Workspace administrator or private listing.

The repository already reserves `plugin-release/main` for automated Version Pull
Requests. A consumer branch must remain distinct from that release-authoring state
and from the editable root Skill sources.

## Decision

Publish a deterministic consumer tree to `marketplace-release` in the existing
`https://github.com/ShinWeiPeng/skills.git` repository after stable release gates
pass. The branch contains `.agents/plugins/marketplace.json`, the complete
`plugins/governed-engineering-skills` package, and publication identity metadata.

`main` root `skills/engineering` and `skills/productivity` remain the only editable
Skill source. `plugin-release/main` remains the Version Pull Request branch.
`marketplace-release` is generated and must not be edited manually.

ChatGPT Work web and Codex Desktop install the same Git source independently.
Automatic synchronization of installation or enablement state is not required.

## Alternatives considered

- A separate generated distribution repository was rejected because it adds a
  repository authority, credential boundary, synchronization step, and rollback
  reference without an access-isolation requirement.
- Committing the complete generated Plugin tree on `main` was rejected because it
  reintroduces duplicate editable-looking Skill copies and source drift.
- A managed private Workspace listing was superseded because it does not match the
  selected personal-account scope and requires administrator evidence.
- Naming the consumer branch `plugin-release` was rejected because it is easily
  confused with the existing `plugin-release/main` Version Pull Request branch.

## Architecture and compatibility impact

The L0 `plugin_assembly_composition` module retains ownership. No runtime Port,
Event, named Type, mutable State Object, dependency edge, execution unit, queue,
callback, or installed Plugin contract changes. The release workflow performs the
external Git branch update after local assembly and validation.

Plugin ID, root Skill ownership, stable SemVer authority, immutable version tags,
bundled paths, and invocation behavior remain compatible. Only the distribution
channel, evidence schema, and user installation instructions change.

## Flow and failure behavior

The selected best-effort CI flow assembles one artifact, generates an exact
Marketplace tree, validates relative paths and release identity, and atomically
updates the consumer branch. Validation failure, stale source identity, fingerprint
mismatch, incomplete tree, or publication race leaves the previous branch commit
available as the rollback target.

No performance or real-time claim is made; Flow assurance is `estimated` until the
functional publication and two-surface installation evidence passes.

## Validation

- Deterministic temporary-tree and temporary-Git-repository fixtures.
- Negative path, mutation, stale identity, and fingerprint fixtures.
- Complete distribution, Plugin, version, and architecture gates.
- Generated branch tree comparison against the assembled release candidate.
- Matching identity and four representative cross-surface invocation records.

## Approval

- **Approver:** Hugo Peng
- **Approval date:** 2026-08-10
- **Approval reference:** SPEC-0013 DISC-011 through DISC-013 selections and explicit `開始執行` authorization.
