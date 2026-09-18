# ADR-0015: Test and validation storage boundaries

- Status: proposed
- Owner: governance_workflow_domain
- Specification: SPEC-0028 revision 20
- Approval: pending; no exception or human approval is asserted.

## Boundary design

| Boundary / parent | Responsibility | Interface / dependency |
|---|---|---|
| governance_workflow_domain / guided_workflow_router | Whole-project layout and test dependency decisions | Explicit policy, inventory and analyzer evidence to diagnostics |
| verification_ladder_domain / governance_workflow_domain | Run metadata validation and fixed acceptance references | Immutable manifest validation; no device actions |
| architecture_governance_cli / root | Compose layout inventory and language evidence | Existing public CLI; per-rule coverage |
| project_validation_composition / root | Wire validation assessment to routing and delivery | Existing injected assessor |
| validate-on-device adapters / governance_workflow_domain | Exclusive run allocation and atomic finalization | Filesystem effects, never infer PASS from storage success |

## Type and state ownership

No new public named Python classes. Versioned dictionary wire records remain validated
at their owning boundary; paths and open file handles are adapter-local.

| Record/state | Owner | Lifetime and mutation authority | Consumers |
|---|---|---|---|
| Layout policy, role and owner records | governance_workflow_domain | Authored immutable input per assessment | Architecture and validation gates |
| Inventory and diagnostics | governance_workflow_domain | Assessment-local, deterministic output | CLI and delivery |
| Run manifest | verification_ladder_domain | Running until terminal publication; no terminal mutation | Evidence consumers |
| Run directory and finalization lock | Filesystem adapter | Exclusive create, adapter-only writes, crash remains incomplete | Run writer |
| Test fixtures and mocks | Owning test target | Readonly shared inputs, per-case mutable setup/cleanup | Same target or declared shared capability |

## Method and tradeoffs

Fixed tests/, validation/ and artifacts/ roots provide one responsibility per path.
Full inventory intentionally includes ignored files; Git policy is independent.
Explicit inputs distinguish fixtures/templates from generated output. Unknown roles,
owners and required analyzer capabilities block, rather than silently pass.
Existing canonical generated architecture views retain their generator-owned location.

Every run uses exclusive allocation and immutable terminal publication. Historical
artifacts migrate with original path and content hash, without invented run metadata.
No automatic cleanup or external project migration is included.

## Traceability and validation

REQ-001/005/006/009/011 -> AC-001: dependency and isolation fixtures.
REQ-002/004/007/012 -> AC-002: concurrent allocation, crash, overwrite/hash tests.
REQ-003/008/013 -> AC-003/005: full-scope negative fixtures and missing capability.
REQ-010/014 -> AC-004/006/007: self-migration, integration, assembly, review.
Host-only tests cannot establish device, timing or physical PASS.
