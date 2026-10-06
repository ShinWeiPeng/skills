# ADR-0002: Schema 2.0 complete named-type governance

- Status: proposed
- Date: 2026-07-24
- Approver: pending
- Approval reference: pending

## Context

Schema 1.2 can validate declared module paths and C/C++ include edges, but a manifest can incorrectly classify a hardware-facing file as an L1 domain file and still pass. It also cannot prove that a struct keeps domain identity, runtime state, policy, and adapter binding in their owning layers.

## Decision

- Accept only standard and schema `2.0.0` as public manifest input.
- Retain every schema 1.0 logical, 1.1 description, and 1.2 execution-efficiency requirement through internal validation layers.
- Require a complete catalog for every self-owned named type under governed source paths.
- Require field-level semantic roles, one owning Module, declared visibility, lifetime, mutability, mutation authority, and consumers.
- Permit vendor/generated exclusions only inside L3+ modules and forbid excluded types from L0-L2 public contracts.
- Require C/C++ functional-boundary markers and scan all L0-L2 source for external-technology leakage.
- Provide no automatic 1.x migration because type ownership cannot be inferred safely.

## Consequences

- Existing 1.x manifests are rejected until a human produces a complete 2.0 inventory.
- Manifests and generated views become larger because named types are explicit.
- C/C++ projects gain blocking source/catalog completeness and technology-boundary diagnostics.
- Other languages retain the same Type Ownership Gate but report source completeness as not automatically verified until a language analyzer exists.

## Validation

- Unit fixtures preserve representative 1.0, 1.1, and 1.2 failures under schema 2.0.
- A synthetic mixed `IoEndpointDescriptor` plus GPIO use in an L1 source must fail.
- A split domain identity and private L3+ binding must pass.
- Bootstrap output must contain only schema 2.0 tools and no migration command.
