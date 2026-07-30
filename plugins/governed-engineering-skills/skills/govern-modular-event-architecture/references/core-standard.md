# Core modular architecture standard

## Rule levels

- **MUST:** Blocking invariant. Deviation requires an accepted ADR.
- **SHOULD:** Default practice. Deviation requires an explanation in the architecture document or proposal.
- **MAY:** Optional technique selected according to project constraints.

## Levels

| Level | Required responsibility | Allowed role |
|---|---|---|
| L0 | Compose the system and coordinate L1 domains | `composition`, `orchestration` |
| L1 | Own a functional domain and coordinate its L2 components | `domain` |
| L2 | Implement an independently testable functional component | `component` |
| L3+ | Implement OS, hardware, storage, network, framework, or shared technical capabilities | `adapter`, `technical` |

Levels are semantic, not mandatory empty folders. Omit a level that has no responsibility. Use feature-first organization in L0-L2 and technical organization in L3+.

L0 owns composition, orchestration, and sibling mapping; it MUST NOT own a child domain's mutable runtime. L1 owns a functional domain, its public contracts, invariants, and domain runtime. L2 owns independently testable components and private algorithm state. L3+ owns external-technology representations and bindings.

## Dependency rules

1. L1 modules MUST name an L0 parent. L2 modules MUST name an L1 parent.
2. L0-L2 siblings MUST NOT depend directly on one another. Their parent coordinates public input ports and output events.
3. L0 orchestration depends on L1 public contracts. L1 depends on child L2 public contracts.
4. A composition module MAY reference concrete adapters only to construct and wire the system.
5. A functional module MUST NOT reference an L3+ implementation or expose framework-specific types.
6. A demand-side L0-L2 module owns each port needed from hardware, OS, storage, network, time, or another external technology. An L3+ adapter implements that port.
7. L3+ adapters MAY depend on the public contracts they implement and on declared technical modules. Dependency cycles are forbidden.
8. Private pure calculations and module-internal helpers do not require ports.

## Named-type ownership

1. Every governed production named type MUST have exactly one semantic owner Module and one source declaration in the schema 2.0.2 Type Catalog.
2. Classify logical source sets before inventorying structs, unions, enums, classes, typedefs, aliases, interfaces, protocols, DTOs, schemas, and named function-pointer types. Fully catalog only `production`; keep `generated-production` behind a declared L3+ generator boundary.
3. Classify every field as domain identity/value, contract control, policy, configuration, runtime state, adapter binding, framework handle, wire/storage representation, or metadata.
4. L0-L2 public types MUST NOT expose adapter bindings, framework handles, wire representations, or storage representations.
5. Runtime-state and private-helper types MUST remain private to their owner. Only the owner mutates owner-mutable state.
6. A type containing both a domain reference and an adapter/framework field MUST be either a private L3+ adapter binding or a private L0 composition mapping.
7. Type consumers and referenced project types MUST follow the same declared dependency and Port direction rules as code.
8. Renaming, aliasing, or moving fields is not evidence that responsibilities were separated.

Before changing a named type, produce a Type Ownership Matrix containing the owner, level, declaration, semantic kind, visibility, lifetime, mutability, mutation authority, consumers, field roles, and ABI/wire/storage consequences. An unresolved row is blocking.

Never move, copy, redeclare, or hand-edit generated declarations to make ownership appear compliant. Keep generated production generator-owned and fix violations at the consumer, Port, adapter, or generator template.

Choose the owner from the semantics expressed, invariant authority, lifecycle control, mutation authority, and command/query/event/Port contract role. File location, number of consumers, current globals, conversion avoidance, or a checker PASS are not ownership evidence. A parent-owned shared DTO MUST NOT appear in a child's public API merely because siblings need similar data.

## Contract and mapping rules

1. Directly pass a producer-owned contract only when the consumer may legally depend on that owner and the contract already expresses the consumer's required semantics.
2. When direct use creates a sibling or child-to-parent dependency, each side owns its own semantic contract and their parent performs explicit mapping.
3. A parent-private mapping type may exist only inside composition or orchestration and MUST NOT become a child public parameter, field, or return type.
4. Primitive and external standard types do not require wrapper DTOs merely because they cross modules.
5. DTOs contain only contract semantics; private runtime, adapter handles, and framework objects are forbidden.

## Runtime-state ownership

1. Every mutable runtime object has exactly one semantic owner and appears in `state_objects`.
2. The definition and complete private runtime type reside in the owner's private implementation.
3. Non-owners MUST NOT obtain state through globals, `extern`, pointers, struct fields, getters, or address passing.
4. Queries return semantic values or immutable snapshots, never private-state pointers.
5. Commands ask the owner to mutate state and do not transfer mutable authority.
6. An opaque handle is legal only when external code cannot dereference it and all operations remain owner APIs.
7. Moving a forbidden access into an L0 wrapper does not separate the boundary.

Before source edits, produce a State Object Ownership Matrix with definition, type, owner, lifetime, mutability, read/write authority, linkage/storage, public leakage, and pointer escape. Inventory mutable file-scope, static-storage, thread-local, `extern`, and address-passed objects.

## Authoring-first prohibition

Architecture is designed before implementation. Do not write structs, getters, shared headers, globals, or wrappers and then change module labels or manifests until a checker passes. A pre-code Boundary Design Table, Type Ownership Matrix, State Object Ownership Matrix, dependency-edge list, and parent mapping must validate first; unresolved ownership or mapping is `BLOCKED`.

## Project workflow

## Logical and execution architecture

Modules describe responsibility and dependency direction. Execution Units describe when and where work runs. The relationship is many-to-many: a Module may participate in multiple ISR, Task, Thread, Event Loop, or Worker contexts, and one Execution Unit may run stages from multiple Modules. A one-Module/one-Task mapping is never inferred.

Schema 2.0.2 retains the schema 1.2 requirement for human-confirmed platform profiles before accepting execution, cache, branch, SIMD, or compiler decisions. See `execution-efficiency.md`.

### New projects

In Plan mode, confirm system flows, modules, parents, public ports, events, delivery semantics, failure behavior, and validation before bootstrapping governance files. Include an architecture-adoption ADR and keep it proposed until the user approves it.

### Existing projects

Describe the actual structure first. Store known MUST violations in `architecture/baseline.yaml`. New code and touched scope must comply immediately. A baseline entry suppresses only the exact rule and location; it cannot hide a new violation.

### Every architecture-affecting change

1. Read the manifest, architecture document, accepted ADRs, and baseline.
2. State the architecture impact before editing.
3. Update manifest, documentation, ADRs, source, and tests as one change.
4. Run the generic checker and applicable language analyzers.
5. Preserve evidence for every acceptance criterion.

## Description and navigation

Schema 2.0.2 retains the schema 1.1 documentation requirements. Every module, port, event, and named type MUST carry the structured description and implementation links defined by the manifest schema. L0/L1 owners define end-to-end flows; private L2 algorithms do not become artificial flows.

The manifest remains the single source. Generate System and Parent views after every architecture change and reject stale checked-in output. This is documentation metadata only: do not add a runtime description struct or expose it through the product ABI unless a separate product requirement explicitly asks for one.
