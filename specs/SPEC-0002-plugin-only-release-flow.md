---
spec_version: 1
spec_id: SPEC-0002
revision: 3
status: implemented
change_set: plugin-only-release-flow
---

# Plugin-only release flow

## Problem

The repository still treats the private root `mattpocock-skills` package as a
release unit even though only `governed-engineering-skills` is maintained,
installed, and published. Root Changesets sees plugin file changes as root package
changes but cannot read the plugin-owned nested changeset, so ordinary plugin pull
requests repeatedly fail `npx changeset status` unless they add an unrelated root
empty changeset.

## Solution

Remove the root Changesets and Node release toolchain, make the plugin's Python
version-governance CLI the only release authority, and retain an automated
plugin-only Version pull request. Apply pending plugin release intent after a
feature pull request reaches `main`, create the release tag only when it is absent,
and keep existing tags immutable.

## User Stories

- As the plugin maintainer, I can submit a valid plugin change without adding an
  unrelated root empty changeset.
- As the plugin maintainer, I receive one automated plugin Version pull request
  after a release-affecting feature pull request merges.
- As an installer, I continue to receive the same plugin ID, SemVer metadata, and
  tag format.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The repository MUST treat `governed-engineering-skills` as its only maintained and published release unit and MUST remove the root Changesets release state and Node release dependencies. |
| REQ-002 | Pull-request release validation MUST invoke the plugin Python version-governance check directly and MUST NOT invoke root Changesets, Node setup, npm installation, or npm audit. |
| REQ-003 | A push to `main` with pending plugin release intent MUST apply and validate that intent, then create or update one open Version pull request from `plugin-release/main` titled `chore: version governed engineering skills`. |
| REQ-004 | A push with no generated version diff MUST create `governed-engineering-skills@<version>` only when that tag is absent; it MUST neither move an existing tag nor fail merely because the tag already exists on an earlier commit. |
| REQ-005 | Plugin installation behavior, plugin ID, SemVer policy, changelog ownership, and tag format MUST remain compatible. Root release history and remote branches MUST not be rewritten or deleted. |
| REQ-006 | Versioning documentation, proposed ADR-0007, architecture manifest descriptions, and generated Description Views MUST describe the plugin-only release authority consistently without changing Modules, Ports, Events, Types, State, or dependency edges. |
| REQ-007 | The change MUST add a plugin patch changeset and release intent that leave the feature branch at `0.5.0-beta.2` and cause the automated Version pull request to promote it to `0.5.0-beta.3`. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Remove root `.changeset`, `package.json`, and `package-lock.json` instead of retaining a dormant root release facade. |
| DEC-002 | Keep the two-step feature PR then automated Version PR lifecycle, but make every step plugin-specific. |
| DEC-003 | Rename the automation branch to `plugin-release/main` and leave the historical `changeset-release/main` remote branch untouched. |
| DEC-004 | Preserve the strict tag writer and guard it in the workflow by checking tag existence before invoking it. |
| DEC-005 | Revise proposed ADR-0007 rather than create or accept a new ADR. |
| DEC-006 | Update only descriptive properties of `plugin_release_governance_technical`; no architecture boundary changes are required. |
| DEC-007 | Classify the release-flow correction as a patch within the existing `0.5.0` beta release group. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002 | Active release configuration contains no root Changesets files, Node release manifest or lockfile, `npx changeset status`, Node setup, npm install, or npm audit. | File-existence and targeted text checks plus workflow contract tests. | PASS — root release artifacts are absent, targeted active-workflow search is empty, and plugin-only workflow contract tests pass. |
| AC-002 | REQ-003 | The workflow directly applies and validates plugin intent and creates or updates only an open `plugin-release/main` Version pull request with the confirmed title and plugin-only body. | Workflow contract tests and GitHub Actions pull-request run. | PASS — workflow contracts pass and PR #14 run `30874535006` completed the plugin release check plus all six Governance jobs successfully. |
| AC-003 | REQ-004 | The workflow skips an existing version tag and creates and pushes a missing version tag without changing the strict tag-writer behavior. | Workflow contract tests plus controlled local tag tests. | PASS — workflow guards on the exact remote tag, pushes only that tag when absent, and the CLI regression proves an existing tag cannot move. |
| AC-004 | REQ-005, REQ-006 | Plugin public metadata and tag format remain unchanged; source documentation, proposed ADR, manifest, and generated views consistently describe one release unit. | Version governance, documentation assertions, deterministic render comparison, and architecture release gate. | PASS — version check, deterministic renderer, plugin release gate, and Standards review pass with no findings. |
| AC-005 | REQ-007 | Pending patch release metadata validates at `0.5.0-beta.2`; applying it in an isolated fixture produces `0.5.0-beta.3`. | Version-governance unit tests and repository check. | PASS — branch metadata remains beta.2, release intent validates, and the successive-intent fixture produces beta.3. |
| AC-006 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007 | Focused tests, complete plugin tests, integration validation, version governance, architecture release gates, and diff hygiene all pass. | Recorded commands, exit codes, and minimal raw output in the implementation handoff. | PASS — 119 local tests, 28-skill integration, version governance, spec validation, workflow YAML parsing, both architecture release gates, `git diff --check`, six hosted Governance jobs, and the hosted plugin release check exit successfully. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-002 |
| REQ-003 | depends_on | DEC-003 |
| REQ-004 | depends_on | DEC-004 |
| REQ-006 | depends_on | DEC-005 |
| REQ-006 | depends_on | DEC-006 |
| REQ-007 | depends_on | DEC-007 |

## Out of Scope

- Publishing an npm package or creating GitHub Releases.
- Changing plugin installation paths, plugin ID, skills, or runtime behavior.
- Deleting or rewriting historical root tags or remote release branches.
- Adding Modules, Ports, Events, Types, State, execution profiles, workloads, or
  product algorithms.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the maintainer confirmed plugin-only ownership and an automated
  Version pull request.
- Spec verification: PASS — revision 3 has complete REQ-to-AC traceability,
  no open decisions, and PASS evidence for every acceptance criterion.
- Clarify improvement proposal: PASS — release scope, compatibility, migration,
  tag behavior, and validation were confirmed.
- Architecture proposal: PASS — only existing module descriptions and generated
  views change; no boundary or algorithm change is proposed.
- TDD: PASS — four workflow contract slices recorded red before green, and the
  complete 119-test suite passes.
- Code review Standards axis: PASS — no documented-standard violation or
  actionable Fowler smell.
- Code review Spec axis: PASS — no missing requirement, unverified acceptance
  criterion, incorrect behavior, or scope creep.
- Spec review: PASS — all requirements and acceptance criteria are covered by
  local or hosted evidence, including PR #14 run `30874535006`.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-04 | Materialized the authorized plugin-only release-flow contract. |
| 2 | 2026-08-04 | Recorded passing local implementation, validation, architecture, and two-axis review evidence; kept hosted AC-002 pending. |
| 3 | 2026-08-04 | Recorded PR #14 hosted Actions evidence and marked the fully verified change set implemented. |
