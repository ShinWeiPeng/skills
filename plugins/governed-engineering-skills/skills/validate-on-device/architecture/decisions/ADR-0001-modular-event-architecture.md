# ADR-0001: Adopt modular event architecture

- Status: proposed
- Date: 2026-07-22
- Approver: pending
- Approval reference: pending

## Context

validate-on-device needs explicit module boundaries, data flow, event behavior, and machine-checkable dependency rules.

## Decision

Adopt the pinned modular event architecture described by `architecture/manifest.yaml`.

## Alternatives considered

- Documentation-only governance.
- Framework-specific layering.
- Unconstrained per-change architecture decisions.

## Benefits, costs, and tradeoffs

The standard improves traceability, testing, and replaceability. It adds manifest, adapter, validation, and migration maintenance.

## Risks and mitigations

Avoid over-abstraction by requiring ports only at module and external-technology boundaries.

## Compatibility and migration

For existing projects, preserve exact known violations in a baseline and prevent new violations.

## Validation

Run the project checker and applicable language analyzers. All MUST diagnostics must be resolved, baselined as pre-existing, or covered by a user-approved ADR.

