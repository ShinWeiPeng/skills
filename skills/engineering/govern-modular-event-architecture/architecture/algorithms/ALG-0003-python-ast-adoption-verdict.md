# ALG-0003: Python AST source conformance and adoption verdict

## Metadata

- Status: proposed
- Owner module: `governance_engine`
- Product feature: Host-side source conformance and adoption readiness
- Flow IDs: `validate-architecture`
- Related ADRs: `ADR-0006`
- Source paths: `scripts/python_analyzer.py`, `scripts/governance_adoption.py`, `scripts/architecture_cli.py`
- Test and benchmark paths: `tests/test_governance_cli.py`
- Supersedes: none

## Problem and observable success

Prove that governed Python declarations, runtime state, imports, public symbols,
and composition roots match the manifest, then combine that evidence with exact
temporary-debt policy without treating inspection or an empty baseline as PASS.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are schema 2.1.0 manifest/adoption/baseline files and UTF-8 production
Python source. Outputs are stable diagnostics, analyzer coverage, gate exit
classification, and deterministic Markdown/JSON.

## Constraints and quantitative acceptance thresholds

Every governed production Python file parses. Every discovered class and
mutable module runtime object has one matching owner. Every declared Python
symbol and release composition root exists. Release baseline count equals zero.

## Candidate methods and comparative evidence

Text scanning cannot reliably distinguish scopes. Python's standard `ast`
module is deterministic and target-independent. Runtime introspection executes
project code and is forbidden for static governance.

## Selected method and reasons for rejecting alternatives

Use stdlib AST with path-to-module ownership and bidirectional catalog
reconciliation. Unsupported languages, parse failure, ambiguous ownership, or
missing analyzer configuration are `BLOCKED`.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. Resolve governed Python files and select the unique most-specific owner.
2. Parse classes, mutable module assignments, imports, public symbols, and roots.
3. Reconcile discovered and declared Type/State rows in both directions.
4. Validate cross-module imports against declared dependency edges.
5. Apply only exact valid temporary deferrals during development.
6. Reject every temporary baseline entry during release.
7. Compute `BLOCKED` for evidence gaps, `FAIL` for active MUST violations,
   `DEFERRED` for approved debt, and `VERIFIED` only with no active blocker.

## Parameters, calibration, versioning, and compatibility

The contract is schema 2.1.0. Legacy command compatibility is not provided.

## Time and space complexity and resource budgets

Traversal is linear in Python AST nodes plus catalog rows and uses stable path
ordering.

## Errors, degradation, fallback, and forbidden behavior

There is no lexical or runtime-import fallback to PASS. Codex cannot invent
deferral approval or accept ADR/Algorithm records.

## Validation cases and evidence

Fixtures cover types, state, symbols, roots, imports, analyzer configuration,
baseline approval/growth/expiration/staleness/release-zero, deterministic
reports, bootstrap, and generated-artifact tampering.

## Risks and monitoring

Dynamic imports and runtime metaprogramming may require a future approved
analyzer extension. Until supported, affected evidence remains `BLOCKED`.

## Human approval

Pending.
