# ADR-0011: Canonical repository change-set specification

- Status: proposed
- Date: 2026-08-02
- Supersedes: none

## Context and problem

The greenfield interview was intentionally conversation-only, tracker publication
does not guarantee durable repository context, and implementation and review do not
share one requirement-to-evidence contract. Conversation compaction can therefore
lose stable decisions before materialization, causing repeated questions even within
one task. Later tasks can also select the wrong change set or review against a
tracker snapshot rather than repository truth.

## Proposed decision

Make `specs/SPEC-####-<slug>.md` the canonical contract for each repository-modifying
change set. `spec_governance_domain` owns a project-local working bundle under
`.codex/spec-governance/`, with a human-readable Markdown snapshot and normalized
hash-linked journal. Reconciliation persists the bundle before the next decision
question. A decision-complete working contract materializes immediately as a
canonical specification without authorizing product implementation.

Retain exact `開始執行` authorization for product files, other governance artifacts,
Git, and external actions. A confirmed but unimplemented specification may reopen in
place when later discussion changes its contract; an implemented specification is
immutable and later behavior uses a related change set.

The tracker stores a complete snapshot and canonical local path but is not
authoritative. Implemented specifications are excluded from active fallback and
retain requirement, acceptance, validation, review, and scope evidence.

## Alternatives considered

- Expand `to-spec`: rejected because interviewing, consistency, persistence,
  publication, and implementation gates would collapse into one shallow interface.
- Make the tracker canonical: rejected because offline repository routing would lack
  durable knowledge.
- Use one project `PRD.md`: rejected because independent change sets would share
  identity and conflict scope.
- Re-interview every task: rejected because a confirmed contract should eliminate
  already-settled decisions.
- Add a graph database: rejected because stable IDs and explicit relation tables are
  sufficient for the required traceability.
- Keep conversation-only working state: rejected because compaction or an omitted
  reconciliation can lose settled decisions before materialization.
- Allocate a numbered canonical specification at the start of grilling: rejected
  because parallel branches or worktrees can allocate the same repository number.
- Use an external tracker as working authority: rejected because offline work,
  permissions, and tracker availability would control local grilling continuity.

## Benefits, costs, and risks

The proposal makes within-task and cross-task routing deterministic and ties
implementation evidence to stable requirements. Costs are synchronous local file
writes per answered decision, owner-private working state, stricter modification
gates, schema and router changes, and additional release validation. The main risks
are ambiguous working-spec selection and journal discontinuity; resolution fails
closed on ambiguity, while a missing local journal explicitly starts a discontinuous
epoch from the authoritative Markdown snapshot.

## Compatibility and migration impact

This is an incompatible pre-1.0 public behavior change targeted at the next MINOR
release. Existing confirmed and implemented specifications remain valid. Existing
conversation-only interviews have no automatic migration; a later recovery workflow
may reconstruct them from task history. Pinned upstream snapshots remain unchanged.

## Validation and observable pass conditions

- Working Markdown and its local journal persist during grilling without product
  execution authorization.
- A decision-complete canonical repository spec exists before product execution
  authorization, while all non-spec mutations remain gated.
- A contract-affecting follow-up reopens the same confirmed SPEC before clarification
  and blocks implementation until it is confirmed again.
- A confirmed spec changes an implementation-absent repository from context absent
  to context present.
- Later tasks verify and resume the resolved confirmed spec without grilling only
  when the caller supplies explicit resume evidence and no new decision or conflict
  exists; resolution alone proves durable context.
- Multiple candidates block; implemented specs are not active fallback.
- Every confirmed requirement has an acceptance criterion; every implemented
  acceptance criterion has PASS evidence and a passing Spec review.
- Tracker publication failure preserves the local canonical document.
- Commit preparation asks how to dispose of or archive local journal state and never
  stages `.codex/spec-governance/**` implicitly.

## Approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
