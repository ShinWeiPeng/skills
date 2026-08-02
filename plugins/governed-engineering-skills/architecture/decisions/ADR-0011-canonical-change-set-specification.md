# ADR-0011: Canonical repository change-set specification

- Status: proposed
- Date: 2026-08-02
- Supersedes: none

## Context and problem

The greenfield interview is intentionally stateless, tracker publication does not
guarantee durable repository context, and implementation and review do not share one
requirement-to-evidence contract. Later tasks can therefore repeat interviews, select
the wrong change set, or review against a tracker snapshot rather than repository
truth.

## Proposed decision

Make `specs/SPEC-####-<slug>.md` the canonical contract for each repository-modifying
change set. Add `spec_governance_domain` with reconcile, materialize, and verify
interfaces. Discussion remains an in-conversation working specification until the
user explicitly authorizes mutation. A confirmed local specification becomes durable
project context and is verified in later tasks before TDD or implementation.

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

## Benefits, costs, and risks

The proposal makes cross-task routing deterministic and ties implementation evidence
to stable requirements. Costs are a new skill, stricter modification gates, schema
and router changes, and additional release validation. The main risk is ambiguous
spec selection; the ordered resolver fails closed and asks for one explicit choice.

## Compatibility and migration impact

This is an incompatible pre-1.0 public behavior change targeted at
`0.5.0-beta.1`. Empty formal-context files become ambiguous. Non-empty legacy context
remains present and is normalized only when it first participates in a change set.
Pinned upstream snapshots remain unchanged.

## Validation and observable pass conditions

- No repository spec exists before explicit authorization.
- A confirmed spec changes an implementation-absent repository from context absent
  to context present.
- Later tasks verify the resolved confirmed spec and resume without grilling when no
  new decision or conflict exists.
- Multiple candidates block; implemented specs are not active fallback.
- Every confirmed requirement has an acceptance criterion; every implemented
  acceptance criterion has PASS evidence and a passing Spec review.
- Tracker publication failure preserves the local canonical document.

## Approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
