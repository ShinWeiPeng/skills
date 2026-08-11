# ADR-0014: Optional Codex Git Marketplace publication

- **Status:** accepted
- **Date:** 2026-08-10
- **Superseded in part by:** the local Codex installer decision in SPEC-0013 revision 25

## Context and problem

The assembled governed Plugin is ignored under `dist/`, so GitHub `main` cannot be
consumed directly as a complete Plugin. Product-surface verification later showed
that this personal ChatGPT web account exposes MCP Plugin creation but not Git
Marketplace installation. The supported scope is therefore Codex Desktop and CLI.

The repository already reserves `plugin-release/main` for automated Version Pull
Requests. A consumer branch must remain distinct from that release-authoring state
and from the editable root Skill sources.

## Decision

Optionally publish a deterministic consumer tree to `marketplace-release` in the existing
`https://github.com/ShinWeiPeng/skills.git` repository after stable release gates
pass. The branch contains `.agents/plugins/marketplace.json`, the complete
`plugins/governed-engineering-skills` package, and publication identity metadata.

`main` root `skills/engineering` and `skills/productivity` remain the only editable
Skill source. `plugin-release/main` remains the Version Pull Request branch.
`marketplace-release` is generated and must not be edited manually.

The repository-root launcher is the primary installation path: it assembles and
validates the same source, applies a local-only cachebuster, registers the local
Marketplace, and installs the Plugin. The generated branch remains a Codex-only
alternative and is not required for installation.

## Alternatives considered

- A separate generated distribution repository was rejected because it adds a
  repository authority, credential boundary, synchronization step, and rollback
  reference without an access-isolation requirement.
- Committing the complete generated Plugin tree on `main` was rejected because it
  reintroduces duplicate editable-looking Skill copies and source drift.
- ChatGPT web publication was rejected because the available personal-account UI
  creates MCP connections and cannot add this private Git Marketplace.
- Naming the consumer branch `plugin-release` was rejected because it is easily
  confused with the existing `plugin-release/main` Version Pull Request branch.

## Architecture and compatibility impact

The L0 `plugin_assembly_composition` module retains assembly ownership and the L3+
`local_install_adapter` owns Marketplace registration, Plugin reinstall, stable
failure statuses, and the Codex Desktop page handoff. The release workflow may
perform the external Git branch update after local assembly and validation.

Plugin ID, root Skill ownership, stable SemVer authority, immutable version tags,
bundled paths, and invocation behavior remain compatible. Only the distribution
channel and user installation instructions change. Web release-evidence schemas
and acceptance gates are removed.

## Flow and failure behavior

The selected best-effort CI flow assembles one artifact, generates an exact
Marketplace tree, validates relative paths and release identity, and atomically
updates the consumer branch. Validation failure, stale source identity, fingerprint
mismatch, incomplete tree, or publication race leaves the previous branch commit
available as the rollback target.

No performance or real-time claim is made. The local installation flow is verified
through bounded Windows fixtures; optional branch publication remains best effort.

## Validation

- Deterministic temporary-tree and temporary-Git-repository fixtures.
- Negative path, mutation, stale identity, and fingerprint fixtures.
- Complete distribution, Plugin, version, and architecture gates.
- Generated branch tree comparison against the assembled release candidate.
- Positive, repeated, missing-runtime, incomplete-artifact, cache-refresh, and
  simulated partial-failure local installer fixtures.

## Approval

- **Approver:** Hugo Peng
- **Approval date:** 2026-08-10
- **Approval reference:** SPEC-0013 DISC-011 through DISC-013 selections and explicit `開始執行` authorization.
