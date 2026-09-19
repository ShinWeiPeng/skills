# ALG-0001: AST boundary analysis

## Metadata

- Status: proposed
- Owner module: `governance_engine`
- Product feature: C/C++ architecture evidence classification
- Flow IDs: `validate-architecture`
- Related ADRs: `ADR-0003`
- Source paths: `scripts/ast_analyzer.py`, `scripts/c_analyzer.py`
- Test and benchmark paths: `tests/test_architecture.py`
- Supersedes: none

## Problem and observable success

Build declaration, reference, state-access, and pointer-escape evidence from the actual C/C++ program. Success means every governed translation unit parses, every governed header is covered, and violations are classified deterministically; missing evidence is never reported as PASS.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are a schema 2.1.0 manifest, explicit logical source sets, project root, complete production `compile_commands.json`, target triple, and governed source files. Output is a stable diagnostic list plus AST coverage and catalog-only generated-state evidence.

## Constraints and quantitative acceptance thresholds

All governed translation units must be present and parse without error. Every governed header must be reachable from at least one successful translation unit. Any capability, database, coverage, or parse gap produces `CAST001`–`CAST003` and exit code 2.

## Candidate methods and comparative evidence

- Lexical scanning is fast and useful for forbidden markers, but cannot resolve typedefs, macros, canonical declarations, or semantic reads and writes.
- Compiler AST traversal resolves source semantics and build flags but requires a complete compilation database.
- Whole-program points-to analysis is more precise but is not portable or bounded enough for this Skill.

## Selected method and reasons for rejecting alternatives

Use pinned libclang AST traversal as the required source of ownership evidence. Retain lexical scans only for supplemental configurable markers. Use conservative local pointer analysis so uncertain mutable address escape is rejected instead of silently accepted.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. Load libclang and the declared compilation database.
2. Normalize each path and require exactly one source-set match; reject overlaps, missing classifications, traversal, and development/build entries in the production database.
3. Parse each unit with the declared target and recorded build arguments.
4. Canonicalize declarations and map their source paths to modules.
5. Traverse includes, type references, variable definitions, reference expressions, assignments, address-of operations, calls, and member dereferences.
6. Compare production edges and accesses with complete catalogs.
7. Treat generated-production declarations as generator-owned L3+ boundary evidence; emit mutable globals as catalog-only state and reject non-owner access or functional-contract leakage.
8. Emit stable diagnostics sorted by rule and location.
9. If any required evidence or classification is missing or ambiguous, return `BLOCKED`.

## Parameters, calibration, versioning, and compatibility

The implementation pins `libclang==18.1.1`. Earlier schema input is not migrated or reinterpreted; projects opt in by pinning 2.1.0 and supplying human-confirmed source sets, catalogs, AST configuration, and applicable RTOS timing inputs.

## Time and space complexity and resource budgets

Traversal is linear in source-path classification plus the total AST cursor count and catalog lookups. Translation units are processed sequentially to keep diagnostics deterministic and memory bounded.

## Errors, degradation, fallback, and forbidden behavior

There is no ownership-PASS fallback to lexical analysis. Missing libclang, database entries, headers, target configuration, source classification, or successful parses is blocking. It is forbidden to infer an owner, authority, source intent, or mapping from current placement, and forbidden to move or redeclare generated source to satisfy catalogs.

## Validation cases and evidence

Unit fixtures cover typedef and forward-declaration references, macro-expanded access, private-state reads/writes, address escape, getter laundering, public leakage, legal mapping, legal opaque handles, primitive transfer, and missing capability or coverage. Regression commands are recorded in `tests/validation-evidence.md`.

## Risks and monitoring

Conservative pointer classification can produce false positives for complex aliasing. Such cases require clearer owner APIs or an accepted human-approved ADR; the analyzer must not silently weaken the rule.

## Human approval

Pending.
