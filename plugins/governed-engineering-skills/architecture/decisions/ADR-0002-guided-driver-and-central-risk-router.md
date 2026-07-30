# ADR-0002: Guided Driver and central risk router

- Status: proposed
- Date: 2026-07-29

## Context and problem

`ask-matt` is user-invoked and promises orientation rather than execution. Multiple engineering entry skills also need the same risk rules, but copying those rules would drift and making `ask-matt` implicit would change its human-controlled invocation contract.

## Decision

Keep `ask-matt` user-invoked as the L0 Guided Driver. Place ordered hard-trigger classification in the model-invoked `engineering-risk-routing` L1 domain. The L0 parent coordinates delivery and governance domains and carries `RoutingDecision` and `GateResult` evidence between them.

## Alternatives considered

- Make `ask-matt` model-invoked: rejected because it removes the explicit human navigation boundary.
- Copy risk tables into every entry skill: rejected because independent copies cannot be kept trustworthy.
- One-shot orchestration: rejected because it would execute human-only skills without their checkpoints.

## Benefits, costs, and tradeoffs

One rule owner prevents silent divergence and preserves user control. The cost is an additional routing contract and explicit handoff metadata at each governed entry.

## Risks and mitigations

- Router unavailable: return `BLOCKED`; do not fall back to an ungoverned path.
- Rule error: validate deterministic fixtures and keep the algorithm record proposed until human review.
- Sibling dependency leakage: L0 owns orchestration; L1 domains do not own each other's contracts.

## Compatibility and migration impact

The original promoted skills remain vendored snapshots. Integration overlays exist only inside this Codex plugin; the upstream Claude plugin is unchanged.

## Validation and observable pass conditions

- All routing fixtures produce the exact expected class, gates, status, and resume target.
- `ask-matt` remains non-implicit.
- Direct R2/R3 mutation entries are `BLOCKED` before governance PASS.

## Approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
