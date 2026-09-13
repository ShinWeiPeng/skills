# ADR-0004: Formal source sets and generated-production boundaries

- Status: superseded by ADR-0005
- Date: 2026-07-25
- Approver: pending
- Approval reference: pending

## Context

Schema 2.0.1 cataloged every declaration under module paths. Generated object-dictionary state, GPT development artifacts, derived documentation, and build outputs could therefore be mistaken for maintained product source or moved into formal source to make a catalog appear complete.

## Decision

- Accept only schema 2.0.2 for this decision's historical scope; ADR-0005 advances the current contract to 2.1.0.
- Require explicit logical source sets without renaming or moving physical directories.
- Fully govern only `production`.
- Parse `generated-production` as a declared L3+ generator boundary and report its mutable globals as catalog-only evidence.
- Reject development, derived-documentation, and build-output paths from formal declarations and the production compilation database.
- Forbid copying, moving, redeclaring, or hand-editing generated output as remediation.
- Provide no automatic 2.0.1 migration because source intent cannot be inferred.

## Alternatives considered

- Module paths plus exclusions cannot safely classify mixed handwritten and generated files.
- Automatic marker or folder-name detection is not fail-closed.
- Physically reorganizing every project creates unnecessary build and history churn.

## Consequences

Projects must supply human-confirmed path globs. Generated production remains compilable but is not expanded into the formal Type or State Catalog. Existing 2.0.1 manifests are rejected until explicitly classified.

## Validation

Schema, AST, catalog, overlap, traversal, compilation-database, leakage, and no-move fixtures must pass. The deterministic renderer and skill checker must remain clean.

## Approval

Pending human approval. Codex must not mark this ADR accepted.
