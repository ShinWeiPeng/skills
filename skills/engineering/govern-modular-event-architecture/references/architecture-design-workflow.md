# Architecture design workflow

Read the [coding standards](../../coding-standards/SKILL.md) before design.

## Rule levels

Use the strength definitions in coding-standards and the architecture exception policy.

## Authoring-first prohibition

Architecture is designed before implementation. Do not write structs, getters, shared headers, globals, or wrappers and then change module labels or manifests until a checker passes. A pre-code Boundary Design Table, Type Ownership Matrix, State Object Ownership Matrix, dependency-edge list, and parent mapping must validate first; unresolved ownership or mapping is `BLOCKED`.

## Logical and execution architecture

Modules describe responsibility and dependency direction. Execution Units describe when and where work runs. The relationship is many-to-many: a Module may participate in multiple ISR, Task, Thread, Event Loop, or Worker contexts, and one Execution Unit may run stages from multiple Modules. A one-Module/one-Task mapping is never inferred.

Schemas 2.1.0 and 2.2.0 retain the schema 1.2 requirement for human-confirmed platform profiles before accepting execution, cache, branch, SIMD, or compiler decisions. Every hard/soft real-time workload additionally requires a scheduler-compatible design study and generated report. Timing class triggers the study; RTOS use alone does not. See `execution-design-workflow.md` and `realtime-scheduling-analysis.md`.

### New projects

In Plan mode, confirm system flows, modules, parents, public ports, events, delivery semantics, failure behavior, and validation before bootstrapping governance files. Include an architecture-adoption ADR and keep it proposed until the user approves it.

### Existing projects

Describe the actual structure first, then remediate every discovered MUST violation by default. A non-AI developer may temporarily defer one exact rule/location in `architecture/baseline.yaml` only with rationale, approval reference, captured revision, review date, and removal condition. New code and touched scope comply immediately; baseline growth is forbidden and Release requires zero temporary entries. A durable exception requires an accepted ADR.

### Every architecture-affecting change

1. Read the manifest, architecture document, accepted ADRs, and baseline.
2. State the architecture impact before editing.
3. Update manifest, documentation, ADRs, source, and tests as one change.
4. Run the generic checker and applicable language analyzers.
5. Preserve evidence for every acceptance criterion.

## Description and navigation

Schemas 2.1.0 and 2.2.0 retain the schema 1.1 documentation requirements. Every module, port, event, and named type MUST carry the structured description and implementation links defined by the manifest schema. Schema 2.2.0 additionally supports independently localized diagram summaries and function-first root navigation. L0/L1 owners define end-to-end flows; private L2 algorithms do not become artificial flows.

The manifest remains the single source. Generate System and Parent views after every architecture change and reject stale checked-in output. This is documentation metadata only: do not add a runtime description struct or expose it through the product ABI unless a separate product requirement explicitly asks for one.

## Named-type ownership review


Before changing a named type, produce a Type Ownership Matrix containing the owner, level, declaration, semantic kind, visibility, lifetime, mutability, mutation authority, consumers, field roles, and ABI/wire/storage consequences. An unresolved row is blocking.

Never move, copy, redeclare, or hand-edit generated declarations to make ownership appear compliant. Keep generated production generator-owned and fix violations at the consumer, Port, adapter, or generator template.

Choose the owner from the semantics expressed, invariant authority, lifecycle control, mutation authority, and command/query/event/Port contract role. File location, number of consumers, current globals, conversion avoidance, or a checker PASS are not ownership evidence. Apply TYPE-006 for parent-owned DTOs in child public contracts.

## Runtime-state ownership review


Before source edits, produce a State Object Ownership Matrix with definition, type, owner, lifetime, mutability, read/write authority, linkage/storage, public leakage, and pointer escape. Inventory mutable file-scope, static-storage, thread-local, `extern`, and address-passed objects.

## Inventory before editing

2. Classify logical source sets before inventorying structs, unions, enums, classes, typedefs, aliases, interfaces, protocols, DTOs, schemas, and named function-pointer types. Fully catalog only `production`; keep `generated-production` behind a declared L3+ generator boundary.
3. Classify every field as domain identity/value, contract control, policy, configuration, runtime state, adapter binding, framework handle, wire/storage representation, or metadata.
8. Renaming, aliasing, or moving fields is not evidence that responsibilities were separated.
