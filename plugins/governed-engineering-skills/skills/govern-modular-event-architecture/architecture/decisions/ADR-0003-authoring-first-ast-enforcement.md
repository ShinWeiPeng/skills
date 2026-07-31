# ADR-0003: Authoring-first architecture and AST enforcement

- Status: proposed
- Date: 2026-07-24
- Approver: pending
- Approval reference: pending

## Context

A source checker can report PASS while an architecture is semantically wrong when the manifest was written after the implementation, runtime ownership is hidden behind pointers or getters, or lexical analysis cannot resolve real declarations and references. Schema 2.0.0 governs named types but does not require an explicit pre-code interaction model or fail-closed AST evidence for C/C++.

## Decision

- Accept only manifests explicitly pinned to standard and schema `2.0.1`.
- Retain all requirements from versions 1.0 through 2.0.0 without reinterpreting 2.0.0 input.
- Require a fixed authoring order and a pre-code gate containing boundary, type-ownership, state-ownership, dependency, and mapping decisions.
- Determine semantic ownership from meaning, invariants, lifecycle, mutation authority, and contract role—not file location, reuse count, or conversion avoidance.
- Require C/C++ enforcement through pinned libclang, a complete compilation database, an explicit target, and complete governed translation-unit coverage.
- Treat absent or incomplete AST evidence as `BLOCKED` with exit code 2. Lexical scans remain supplemental evidence only.
- Provide no automatic migration because owner, authority, and mapping cannot be inferred safely.

## Consequences

- Architecture changes require more design evidence before source editing begins.
- C/C++ projects must maintain an accurate compilation database and install the pinned analyzer dependency.
- State access, pointer escape, and type-reference violations become blocking even when includes alone appear legal.
- Primitive or external standard values may still cross boundaries directly; duplicate DTOs are required only when direct use would create an illegal dependency or mix semantics.

## Validation

- Forward tests must show that a fresh author creates the pre-code tables and refuses unresolved ownership.
- Fixtures must reject parent/sibling private-state access, getter laundering, illegal project-type references, incomplete AST capability, and parse or coverage gaps.
- Fixtures must accept legal parent mapping, opaque owner-operated handles, and primitive or standard-type transfer.

