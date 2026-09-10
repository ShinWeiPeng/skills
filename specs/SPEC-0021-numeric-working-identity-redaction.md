---
spec_version: 1
spec_id: SPEC-0021
revision: 2
status: implemented
change_set: numeric-working-identity-redaction
---

# Preserve numeric working identity during redaction

## Problem

Release PR #38 run [REDACTED: personal data] failed a working snapshot redaction test. A legal random working ID with a numeric token is mistaken for a telephone number, making the snapshot invalid. Deterministic reproduction with WORKING-SPEC-123456789012-payment-retry returns BLOCKED.

## Solution

Treat hyphens as identifier boundaries for phone matching. Preserve legal working identity and continue redacting standalone phone values. This repairs delivery under the existing execution and commit/push authorization; it does not change the accepted governance policy in SPEC-0020.

## User Stories

- As a user, I need specification creation to succeed regardless of randomly generated identifier digits.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Preserve numeric tokens embedded in hyphenated working identifiers during redaction. |
| REQ-002 | Continue redacting standalone local, hyphenated and international telephone numbers. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Correct phone token boundaries without retries, weakened validation or deterministic production identifiers. |

## Discussion Context

### DISC-001: CI failure report

- **Situation:** Version PR validation failed after the preceding release-test fix.
- **Question:** What caused the reported CI failure?
- **Options and tradeoffs:** No new user choice was required; diagnosis found a deterministic identifier-redaction defect.
- **User answer:** User supplied the Release #110 failure screenshot, continuing the authorized delivery repair.
- **Explicit rationale:** No additional rationale stated.
- **Resulting impact:** REQ-001, REQ-002, DEC-001, AC-001, AC-002.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Creating a working snapshot with a fixed numeric ID succeeds and retains the exact ID. | test_numeric_working_identity_is_not_redacted_as_a_phone | PASS: deterministic numeric identity test and 217-test suite. |
| AC-002 | REQ-002 | Supported standalone phone forms remain redacted. | test_phone_redaction_preserves_identifier_boundaries and existing sensitive discussion test | PASS: standalone phone redaction forms and existing credential/personal-data fixtures; 217-test suite. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| AC-001 | depends_on | REQ-001 |
| AC-002 | depends_on | REQ-002 |
| REQ-001 | refines | SPEC-0020 |

## Out of Scope

- Host interception, new governance policy, changing release bump policy, and merging the Version PR.

## Open Decisions

None.

## Routing/Gates

- Spec review: PASS
- Execution authorized: existing user instruction 開始執行 and commit/push authorization; bounded CI defect repair in the same delivery.
- Architecture: private regex correction in existing spec_contract module; no interface, ownership or state changes.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-10 | Record deterministic CI defect, repair and focused validation. |
| 2 | 2026-09-10 | Recorded implementation PASS evidence. |
