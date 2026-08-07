---
spec_version: 1
spec_id: SPEC-0010
revision: 2
status: implemented
change_set: persistent-grilling-spec-lifecycle
---

# Persistent grilling specification lifecycle

## Problem

Governed grilling currently keeps its working specification only in conversation
state and forbids every file write until the user says `開始執行`. Conversation
compaction or an omitted reconciliation can therefore lose stable decisions and
cause a previously resolved question to be asked again. The same authorization
gate also prevents a decision-complete specification from becoming visible in the
repository before product implementation begins.

## Solution

Let `spec-governance` persist a human-readable working specification and a local
machine-verifiable journal throughout grilling without product execution
authorization. Materialize a decision-complete canonical specification immediately,
while retaining the exact `開始執行` gate for product files, other governance
artifacts, Git, and external actions. Reopen a confirmed but unimplemented
specification in place when later discussion changes its contract.

## User Stories

- As a developer in a long grilling conversation, I can resume from durable stable
  decisions without being asked the same question again.
- As a reviewer, I can read the decision-complete canonical specification before
  authorizing product implementation.
- As a repository owner, I retain explicit control over product changes, Git and
  external actions even though specification lifecycle files are persisted earlier.
- As a committer, I choose whether the local working journal is deleted, retained
  locally, or archived into repository history.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Entering governed grilling MUST create or resolve one working bundle under `.codex/spec-governance/<working-id>/` without requiring `開始執行`. |
| REQ-002 | The bundle MUST contain a human-readable authoritative `working.md` and a JSONL journal containing only normalized deltas, stable IDs, relationships, conflicts, open decisions, verdicts, revisions and hashes; it MUST NOT contain hidden reasoning or full chat transcripts. |
| REQ-003 | Every answered decision MUST be reconciled and atomically persisted before another decision question is asked. Reconciliation MUST require the expected revision and snapshot hash and MUST block stale concurrent writers. |
| REQ-004 | Missing local journal history MUST NOT reopen or repeat decisions present in `working.md`; recovery MUST start a new journal epoch marked `continuity: unavailable`. |
| REQ-005 | Working-bundle resolution MUST use explicit path or working ID, available task or branch evidence, then a unique candidate. Multiple unresolved candidates MUST block and MUST NOT be selected by recency. |
| REQ-006 | A working specification MUST materialize immediately as `specs/SPEC-####-<slug>.md` when it has valid stable IDs and relations, zero conflicts, zero open decisions and at least one acceptance criterion per requirement. This governance write MUST NOT require or imply product execution authorization. |
| REQ-007 | `開始執行` MUST remain required for product source, tests, configuration, `CONTEXT.md`, ADRs, architecture manifests, generated files, Git actions and external actions. Global working agreements and every governed skill MUST expose the same narrow specification-only exception. |
| REQ-008 | A contract-affecting statement about a confirmed, unimplemented specification MUST fail closed by reopening the same SPEC ID and path as `working` before clarification. Stable IDs MUST be preserved and replaced decisions MUST be marked as superseded. |
| REQ-009 | If clarification produces no actual contract delta, the specification MAY return to its prior confirmed state without invalidating existing authorization. An actual contract delta MUST invalidate prior execution authorization and require `開始執行` again after reconfirmation. |
| REQ-010 | Implemented specifications MUST NOT reopen. Later behavior changes MUST use a new change set related with `refines` or `supersedes`. |
| REQ-011 | Before commit, governance MUST block broad or accidental staging of `.codex/spec-governance/**` and ask the user to delete the bundle, retain it locally, or archive its normalized journal under `specs/history/`. No option may make the canonical Markdown depend on the journal. |
| REQ-012 | The plugin architecture, algorithm record, Description Views, schemas, skill contracts, integration checks and release metadata MUST describe and validate the same persistent lifecycle. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use a human-readable Markdown snapshot plus a normalized hash-linked JSONL journal instead of conversation-only state, an early numbered working SPEC, or an external tracker as the authority. |
| DEC-002 | Keep working state under project-local `.codex/spec-governance/`; projects may manage ignore policy, while commit governance prevents accidental inclusion. |
| DEC-003 | Treat `working.md` as authoritative when the journal is absent and start a visibly discontinuous new journal epoch without re-interviewing settled decisions. |
| DEC-004 | Materialize a decision-complete canonical specification before product execution authorization. |
| DEC-005 | Limit the pre-authorization write exception to working bundles and canonical specification lifecycle files. |
| DEC-006 | Reopen a confirmed, unimplemented specification in place rather than allocating a new SPEC ID. |
| DEC-007 | Reopen first for an ambiguous statement that might change the contract; restore confirmed without invalidating authorization only when reconciliation proves there is no delta. |
| DEC-008 | Defer journal retention to an explicit commit-time choice instead of fixing repository retention during grilling. |
| DEC-009 | Keep the exact `開始執行` product execution gate; do not replace it with SPEC-bound authorization. |
| DEC-010 | Revise proposed ADR-0011 and ALG-0004 because this changes their existing no-write-before-authorization lifecycle rather than creating an unrelated architecture decision. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003 | A multi-round process restart reloads the same stable IDs and revision; a stale expected revision or hash is rejected without changing the snapshot. | Focused unit tests using temporary repositories and separate process-equivalent reloads. | PASS: working-bundle persistence, reload, normalized-journal and stale-writer tests. |
| AC-002 | REQ-004, REQ-005 | Deleting the journal and retaining `working.md` starts a discontinuous epoch without reopening settled decisions; ambiguous multiple bundles return BLOCKED. | Recovery and resolver unit tests. | PASS: missing/tampered journal and explicit/task/branch/unique resolver tests. |
| AC-003 | REQ-006, REQ-007 | Decision-complete materialization succeeds without `開始執行`, while attempts to modify non-spec paths remain unauthorized and product-file diffs remain empty. | Lifecycle tests, skill contract checks and Git diff fixture. | PASS: materialization and authorization-boundary contract tests plus Global AGENTS inspection. |
| AC-004 | REQ-008, REQ-009, REQ-010 | The lifecycle passes `working → confirmed → reopened working → confirmed → implemented`; implemented reopen fails and a real reopened delta requires fresh authorization. | State-transition and guided-routing tests. | PASS: reopen, no-delta retention, delta invalidation, supersedes, implemented rejection and router fail-closed tests. |
| AC-005 | REQ-011 | Commit preparation blocks staged `.codex` state and returns the three user dispositions; canonical validation passes independently for every disposition. | Commit-gate unit tests and spec validation. | PASS: staged-state and explicit-disposition tests. |
| AC-006 | REQ-012 | Focused, full, integration, version and architecture development gates pass with deterministic generated views. | Repository validation commands and generated-view comparison. | PASS: 149 plugin tests, integration validation, version check, plugin/skill validation and architecture development gate. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-001 |
| REQ-004 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-002 |
| REQ-006 | depends_on | DEC-004 |
| REQ-007 | depends_on | DEC-005 |
| REQ-008 | depends_on | DEC-006 |
| REQ-009 | depends_on | DEC-007 |
| REQ-011 | depends_on | DEC-008 |
| REQ-012 | depends_on | DEC-010 |
| AC-001 | depends_on | REQ-003 |
| AC-002 | depends_on | REQ-005 |
| AC-003 | depends_on | REQ-007 |
| AC-004 | depends_on | REQ-010 |
| AC-005 | depends_on | REQ-011 |
| AC-006 | depends_on | REQ-012 |

## Out of Scope

- Backfilling the original firmware conversation into a target-project working spec.
- Modifying product repositories other than creating their governed spec lifecycle
  artifacts when that workflow is later invoked.
- Committing, pushing, opening a pull request, publishing a plugin release or
  choosing the commit-time journal disposition in advance.
- Storing raw chat transcripts, chain-of-thought, credentials or personal data in
  the journal.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user selected persistent Markdown plus journal, immediate
  canonical materialization, same-SPEC reopen, fail-closed clarification and the
  two-layer authorization policy.
- Spec reconciliation: PASS — stable requirements, decisions, acceptance criteria
  and relations have no conflicts or open decisions.
- Architecture impact: `spec_governance_domain` gains owner-private persistent
  working state; reconcile becomes a command, and start/reopen/commit-preparation
  ports extend `governed-change-set-lifecycle`.
- Algorithm impact: ALG-0004 remains the owner because working-spec reconciliation,
  stable-ID preservation, recovery and lifecycle selection are one deterministic
  algorithm.
- Flow-cost review: estimated PASS — human-paced bounded Markdown/JSONL writes add
  local filesystem I/O but no runtime Task, Queue, deadline or product performance
  claim. Conversation-only state and external authority were rejected for
  recoverability or ownership reasons.
- Spec verification: PASS — all requirements have acceptance criteria and all
  references resolve.
- Spec review: PASS — every REQ-001 through REQ-012 is implemented by inspected
  source, policy, schema, architecture, generated-view, test or release evidence;
  no missing behavior or scope creep was found.
- Implementation authorization: PASS — the user supplied exact `開始執行`.
- ADR approval: not applicable for implementation status — ADR-0011 remains
  proposed and will be revised without self-approval.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-06 | Materialized the authorized persistent grilling specification lifecycle. |
| 2 | 2026-08-07 | Recorded implementation, validation and Spec-review PASS evidence. |
