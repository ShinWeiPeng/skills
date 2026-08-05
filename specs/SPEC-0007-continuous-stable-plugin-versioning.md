---
spec_version: 1
spec_id: SPEC-0007
revision: 1
status: confirmed
change_set: continuous-stable-plugin-versioning
---

# Continuous stable plugin versioning

## Problem

The personally maintained plugin uses alpha, beta, RC, promotion evidence, and
manual maturity decisions even though there is no separate prerelease audience.
The stage state machine adds release branches and evidence maintenance without
improving the owner's deployment decision.

## Solution

Replace staged promotion with stable-only SemVer. Retain the plugin as the sole
release unit, retain changeset-backed intent, automated Version pull requests,
immutable tags, changelog ownership, and exact package/manifest consistency.
Migrate `0.5.0-beta.6` to stable `0.5.0`; subsequent compatible fixes increment
PATCH and compatible features increment MINOR.

## User Stories

- As the sole plugin owner, I can release every approved change without choosing
  a maturity stage or collecting promotion-only evidence.
- As an installer, I receive monotonically increasing stable SemVer tags with
  unchanged plugin identity and installation behavior.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Formal plugin versions MUST use stable `MAJOR.MINOR.PATCH` only; prerelease and build metadata MUST be rejected. |
| REQ-002 | Compatible fixes MUST increment PATCH, compatible behavior additions MUST increment MINOR, and incompatible public behavior MUST follow SemVer major/minor rules appropriate to the current pre-1.0 lifecycle. |
| REQ-003 | Release intents MUST record bump, complete pending changeset IDs, and structured changelog summary without target stage, release-group, risk-promotion, approval, or validation-evidence fields. |
| REQ-004 | The one-time migration MUST convert `0.5.0-beta.6` to `0.5.0` without rewriting historical tags or releases. |
| REQ-005 | Version application MUST update package metadata, plugin manifest, changelog, release state, production fingerprint, and applied changesets atomically. Future intents use the plugin Version pull request; the explicitly authorized one-time stabilization MAY be committed directly before pushing `main`. |
| REQ-006 | Existing tags MUST remain immutable, and a missing current-version tag MUST still be created exactly once. |
| REQ-007 | Version documentation, repository instructions, workflow contracts, ADRs, architecture manifest descriptions, and generated views MUST describe stable-only ownership consistently. |
| REQ-008 | The change MUST preserve the existing release module boundary, public CLI commands, plugin ID, installation path, and tag format. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Select stable-only SemVer rather than retain staged prereleases. |
| DEC-002 | Keep the automated `plugin-release/main` Version pull request rather than committing generated version files from feature branches. |
| DEC-003 | Treat the migration from the current prerelease as a one-time direct stabilization commit of the existing `0.5.0` release group, not as `0.6.0`; retain Version pull requests for later releases. |
| DEC-004 | Remove obsolete promotion evidence and stage fields instead of retaining ignored compatibility fields. |
| DEC-005 | Supersede ADR-0007 and ADR-0009 with a new accepted decision authorized by the human project owner. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-004 | Transition tests prove prerelease migration to `0.5.0`, stable PATCH/MINOR progression, and rejection of prerelease/build metadata. | Version-governance unit tests. | Pending implementation verification. |
| AC-002 | REQ-003, REQ-005 | Repository validation and intent application accept the simplified intent and atomically synchronize all release metadata. | Repository-policy tests and isolated intent fixture. | Pending implementation verification. |
| AC-003 | REQ-006 | Workflow and tag tests prove existing tags never move and missing tags are created once. | Workflow contract and CLI tag tests. | Pending implementation verification. |
| AC-004 | REQ-007, REQ-008 | Instructions, docs, ADR, manifest, generated views, workflow, CLI names, plugin ID, and tag format are consistent. | Text contracts, architecture render/check, integration validation, and diff review. | Pending implementation verification. |
| AC-005 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008 | Complete plugin tests, integration validation, architecture development/release gates, version governance, YAML parsing, and diff hygiene pass. | Recorded local commands and exit codes. | Pending implementation verification. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-004 |
| REQ-004 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-002 |
| REQ-007 | depends_on | DEC-005 |

## Out of Scope

- Publishing an npm package or GitHub Release.
- Rewriting or deleting historical prerelease tags, changelog entries, validation
  reports, or remote branches.
- Changing plugin installation, skill runtime behavior, architecture boundaries,
  execution units, or product algorithms.
- Removing changesets, release intent, automated Version pull requests, or
  immutable tag enforcement.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the owner selected stable-only continuous versioning.
- Improvement proposal: PASS — staged and stable-only candidates were compared,
  and the user selected stable-only.
- Architecture authoring gate: PASS — the existing release technical module owns
  the behavior; Boundary, Type, State, dependency, and parent mappings are
  unchanged.
- Flow-cost review: estimated PASS — both candidates are best-effort CI flows;
  stable-only removes branches and manual evidence while preserving atomic
  metadata, immutable tags, and the Version pull request.
- Product algorithm screening: not applicable — release infrastructure is not a
  user-facing product algorithm.
- Spec verification: pending strict contract validation.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-05 | Materialized the authorized stable-only release contract. |
