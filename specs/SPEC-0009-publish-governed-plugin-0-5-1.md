---
spec_version: 1
spec_id: SPEC-0009
revision: 1
status: confirmed
change_set: publish-governed-plugin-0-5-1
---

# Publish governed plugin 0.5.1

## Problem

SPEC-0008 and its patch changeset are committed and pushed on
`agent/turn-boundary-grilling-handoff`, but they have not reached `main`. The
governed engineering plugin therefore remains at `0.5.0`, and no stable release tag
contains the corrected turn-boundary grilling handoff.

## Solution

Follow the accepted ADR-0013 continuous stable release flow. Create a
Ready-for-review feature pull request to `main` without merging it. After the user
merges that pull request, let GitHub Actions apply the pending release intent and
create or update the `plugin-release/main` Version pull request. Verify that Version
pull request and its checks without merging it. After the user merges the Version
pull request, verify that the workflow creates the immutable
`governed-engineering-skills@0.5.1` tag at the release commit.

## User Stories

- As the plugin owner, I can review and merge both release-affecting pull requests
  myself while Codex prepares and verifies them.
- As a plugin consumer, I can identify the corrected behavior through one stable,
  immutable `0.5.1` release tag.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The pending `turn-boundary-grilling-handoff` patch changeset MUST produce stable version `0.5.1`. |
| REQ-002 | Codex MUST create a Ready-for-review pull request from `agent/turn-boundary-grilling-handoff` to `main`. |
| REQ-003 | Codex MUST NOT merge the feature pull request, and its required checks MUST be available for the user to review. |
| REQ-004 | After the user merges the feature pull request, GitHub Actions MUST create or update the `plugin-release/main` Version pull request. |
| REQ-005 | Codex MUST verify that the Version pull request synchronizes package version, plugin manifest, changelog, release state, production fingerprint, and applied changesets, and MUST NOT merge it. |
| REQ-006 | After the user merges the Version pull request, the workflow MUST create immutable tag `governed-engineering-skills@0.5.1`. |
| REQ-007 | The release MUST NOT directly push `main`, bypass the Version pull request, move an existing tag, or tag the feature commit as `0.5.0`. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use the accepted ADR-0013 automated Version pull request release flow. |
| DEC-002 | The user, not Codex, merges both the feature and Version pull requests. |
| DEC-003 | Create the feature pull request as Ready for review rather than Draft. |
| DEC-004 | Use the existing changeset's patch declaration, producing target version `0.5.1`. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-002, REQ-003 | A Ready-for-review feature pull request exists with base `main`, head `agent/turn-boundary-grilling-handoff`, visible checks, and no Codex-authored merge. | GitHub pull request metadata and check results. | Pending. |
| AC-002 | REQ-001, REQ-004, REQ-005 | The automated Version pull request targets `0.5.1`, contains the complete synchronized release metadata diff, and passes version and release checks without a Codex-authored merge. | Pull request diff, GitHub checks, and `version_governance.py check`. | Pending. |
| AC-003 | REQ-006 | Remote tag `governed-engineering-skills@0.5.1` exists and resolves to the release commit produced by the merged Version pull request. | Remote tag and commit SHA comparison. | Pending. |
| AC-004 | REQ-007 | Git and GitHub history contain no direct Codex push to `main`, manual metadata bypass, tag movement, or incorrect `0.5.0` tag on the feature commit. | Branch, pull request, workflow, and remote tag history inspection. | Pending. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| SPEC-0009 | depends_on | SPEC-0008 |
| REQ-002 | depends_on | DEC-003 |
| REQ-003 | depends_on | DEC-002 |
| REQ-004 | depends_on | DEC-001 |
| REQ-005 | depends_on | DEC-001 |
| REQ-005 | depends_on | DEC-002 |
| REQ-006 | depends_on | DEC-001 |
| REQ-006 | depends_on | DEC-004 |
| REQ-007 | depends_on | DEC-001 |

## Out of Scope

- Changing the release workflow or ADR-0013.
- Publishing `0.6.0`, a prerelease, another plugin, or a marketplace artifact.
- Codex merging either pull request.
- Directly pushing `main`, moving a tag, or bypassing synchronized release metadata.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user selected user-controlled merges and a Ready-for-review
  feature pull request.
- Spec reconciliation: PASS — requirements, decisions, acceptance criteria, and
  relationships have stable IDs with no conflicts or open decisions.
- Architecture impact: not applicable — this release orchestration adds no Module,
  Port, Event, Type, State, dependency, Flow, execution unit, or runtime behavior.
- Feature validation: PASS locally — 331 tests and the applicable integration,
  version, vendor, spec, and architecture development gates passed for SPEC-0008;
  pull request CI remains required.
- Release validation: pending GitHub Actions governance, release-tooling, and release
  architecture gates.
- GitHub authentication: PASS for account `ShinWeiPeng`.
- Implementation authorization: PASS — the user supplied exact `開始執行`.
- Spec verification: PASS — revision 1 satisfies the strict canonical structure and
  complete REQ to acceptance traceability with no scope creep.
- Code review Standards axis: pending pull request checks.
- Code review Spec axis: pending completion evidence for AC-001 through AC-004.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-06 | Materialized the authorized `0.5.1` release contract with user-controlled merges. |
