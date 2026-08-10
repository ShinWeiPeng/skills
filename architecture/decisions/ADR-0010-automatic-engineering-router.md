# ADR-0010: Automatic engineering workflow router

- Status: accepted
- Date: 2026-08-01
- Supersedes: ADR-0002

## Context and problem

ADR-0002 kept `ask-matt` user-invoked. That requires users to know an internal
engineering skill name and allowed repository presence to be confused with codebase
presence. An empty Git repository can therefore miss the greenfield flow even though
it contains neither implementation nor durable project context.

## Decision

Make `ask-matt` the model-invoked L0 entry for every software-engineering intent.
The L0 router composes deterministic intent, three-state ProjectState, risk-gate, and
capability assessments. `GuidedRouteDecision.selected_skill` owns the authoritative
handoff; the existing `RoutingDecision.next_skill` remains a compatible risk advisory.

All modifying change sets complete one grilling interview before mutation. Read-only
bug diagnosis may precede the interview. Execution stops and returns to grilling if a
new discretionary decision appears. Repository discovery remains read-only behind a
demand-owned evidence port.

## Alternatives considered

- Teach users to invoke `ask-matt`: rejected because routing is an engineering-system
  responsibility, not user vocabulary.
- Treat any Git repository as a codebase: rejected because Git metadata says nothing
  about implementation or durable project context.
- Let the model freely infer ambiguous intent or scaffolds: rejected because the
  result is neither deterministic nor auditable.

## Benefits, costs, and tradeoffs

Users receive the correct workflow from ordinary engineering language, while
three-state evidence prevents silent guesses. Costs include a broader implicit skill
trigger, new public contracts, and more mandatory interviewing before small changes.

## Risks and mitigations

- Over-routing non-engineering work: ordered hard intents and an out-of-scope screen.
- Missing skills in a fresh task: release-blocking inventory validation.
- Interview repetition: one interview is scoped to the whole change set.
- Capability loss: only `grill-me → grilling` may degrade; required wayfinder or
  tracker loss blocks.

## Compatibility and migration impact

This is an incompatible pre-1.0 behavior change targeted at `0.4.0-beta.1`. It changes
only the governed overlay; vendored upstream `mattpocock_skills` snapshots remain
unchanged.

## Validation and observable pass conditions

- Empty repositories route to `grill-me`; docs-only repositories route to
  `grill-with-docs`; source repositories use intent-specific flows.
- README-only and empty scaffolds remain indeterminate.
- All modifying paths grill before mutation, including explicit `tdd`.
- Fresh tasks automatically expose and enter the router without the user naming it.
- Normal routes show one line; degraded, blocked, and indeterminate routes show
  evidence.

## Approval

- Approver: Hugo Peng
- Approval date: 2026-08-01
- Approval reference: Codex task `019fbb64-f7fe-7e13-907b-5b6b6892b6e7`,
  explicit user message `批准 ADR-0010`
