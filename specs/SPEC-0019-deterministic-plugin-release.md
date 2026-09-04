---
spec_version: 1
spec_id: SPEC-0019
revision: 6
status: implemented
change_set: deterministic-plugin-release
---

# Deterministic plugin release

## Problem

The 0.10.0 release workflow did not create its tag or Marketplace artifact because
the production fingerprint included local test artifacts and a calendar-sensitive
governance test expired.

## Solution

Make the assembler's deterministic source-to-artifact inventory the sole file-selection
authority for release fingerprints, make date-sensitive tests use a controlled
clock, and validate the exact clean-checkout release path before publication.

## User Stories

- As a maintainer, I want local and CI release fingerprints to be identical.
- As a maintainer, I want governance tests to remain deterministic over time.
- As an installer, I want the Marketplace version to advance only after release gates pass.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The production fingerprint MUST ignore untracked, ignored, test-generated, cache, build, and nested Git artifacts and MUST match a clean checkout on every supported OS. |
| REQ-002 | Date-sensitive governance tests MUST inject or patch the current date and MUST NOT expire because wall-clock time advances. |
| REQ-003 | Release validation MUST exercise the clean-checkout fingerprint, complete governance suite, tag, and Marketplace publication prerequisites before reporting readiness. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Apply durable root-cause repairs to fingerprint selection, clock-dependent governance tests, and release/tag/Marketplace readiness; do not use a one-off data-only unblock. |
| DEC-002 | Use one deterministic assembly inventory as the canonical source-to-artifact file selection for both plugin assembly and production fingerprinting. |

## Discussion Context

### DISC-001: Repair scope

- **Situation:** A minimal repair can unblock 0.10.0, while a durable repair can also prevent equivalent fingerprint and clock regressions.
- **Question:** Should the change only unblock this release or harden the release contract against recurrence?
- **Options and tradeoffs:** A minimal repair is smaller but preserves fragile mechanisms; durable hardening changes more tests and fingerprint selection but prevents the same class of failure.
- **User answer:** `1。三個都要修正`
- **Explicit rationale:** The repair must address all three diagnosed failure paths rather than only unblock the current release.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, AC-001, AC-002, AC-003.

### DISC-002: Fingerprint input authority

- **Situation:** Git-tracked files, assembled output, or the assembler's logical inventory could define which files participate in the production fingerprint.
- **Question:** Which source must be authoritative for fingerprint membership?
- **Options and tradeoffs:** Git tracking is simple but broader than installed content; hashing only the built artifact is exact but requires assembly for every check; a shared deterministic inventory requires a small refactor but gives assembly and fingerprinting one file-selection authority.
- **User answer:** `3`
- **Explicit rationale:** The deterministic assembly inventory prevents temporary local files from entering the fingerprint while keeping source and artifact selection aligned.
- **Resulting impact:** REQ-001, DEC-002, AC-001.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Dirty and clean checkouts produce the same fingerprint, while a tracked production change changes it. | Cross-platform fingerprint contract tests. | PASS: Plugin suite 198/198; dirty-worktree and tracked-source fingerprint regressions pass; tracked clean-checkout rehearsal passes. |
| AC-002 | REQ-002 | The baseline test passes under dates before, on, and after the former fixed expiry while production expiry behavior remains enforced. | Injected-clock unit tests. | PASS: Architecture-governance suite 105/105, including before/on/after review-date and production-clock expiry cases. |
| AC-003 | REQ-003 | A clean release rehearsal reaches tag and Marketplace eligibility only after all required gates pass. | Release workflow and distribution integration tests. | PASS: tracked-index rehearsal applies the pending intent and validates the 0.10.1 candidate, tag dry-run, Marketplace distribution, 30-skill integration, and both release gates. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-002 |
| AC-003 | depends_on | REQ-003 |
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-001 |
| REQ-001 | depends_on | DEC-002 |

## Out of Scope

- Bypassing release gates by manually creating the 0.10.0 tag.
- Changing plugin features unrelated to release determinism.

## Open Decisions

None.

## Routing/Gates

- TDD required.
- Code review required.
- Spec review: PASS.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 0 | 2026-09-04 | Captured confirmed failure evidence and opened repair-scope decision. |
| 2 | 2026-09-04 | Selected durable repair for fingerprint, clock, and release-publication readiness. |
| 3 | 2026-09-04 | Selected one deterministic assembly inventory as fingerprint input authority. |
| 4 | 2026-09-04 | Recorded passing implementation evidence and completed the Spec review gate. |
| 5 | 2026-09-04 | Corrected the versioned-artifact fixture to stage release-intent mutations before tracked-only assembly. |
| 6 | 2026-09-04 | Made the Version job stage its candidate before tracked-only metadata validation and cached-diff detection. |
