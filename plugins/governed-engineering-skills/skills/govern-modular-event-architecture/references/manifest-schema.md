# Architecture manifest schema

## Schema 2.0.2 cumulative contract

Pin `standard_version: "2.0.2"` and `schema_version: "2.0.2"`. Schema 2.0.2 retains every requirement from 1.0 through 2.0.1 and adds explicit logical source classification and generated-production boundaries.

The checker accepts only schema 2.0.2 manifests. It does not migrate or infer source intent from earlier input.

Schema 2.0.2 retains stable `id` values on Flow steps plus these top-level lists:

```yaml
workloads: []
execution_profiles: []
execution_units: []
execution_mappings: []
execution_channels: []
data_access_profiles: []
microarchitecture_profiles: []
platform_variants: []
```

Workloads reference one Flow and its stable step IDs, declare `timing_class`, `activation`, semantic `data`, and quantitative `budgets`. Hard-real-time workloads additionally require `tier1_analysis` entries for working set, memory traffic, branch predictability, SIMD dependencies, parallelism, and blocking bounds.

Execution Profiles use `legacy-review`, `proposed`, `accepted`, or `superseded`. Accepted profiles require confirmed platform, CPU, runtime, compiler, cache topology, scheduler capabilities, and non-AI human approval metadata. Execution Units, Mappings, and Channels belong to one profile. Every Channel declares capacity, ordering, copy policy, timeout, and overload behavior.

Data Access Profiles declare element size, layout, active working set, stride, reuse, alignment, sharing, cache target, candidates, and optimization tier. Microarchitecture Profiles declare branches, SIMD eligibility, compiler, vectorization report, PGO, LTO, and tier. Tier 2 records require a portable baseline and benchmark.

Platform Variants bind profile-owned Unit/Data/Microarchitecture IDs and fixed parameters. A release variant may reference only an accepted profile.

`architecture/manifest.yaml` is the machine-readable and human-description source of truth. Schema 2.0.2 generates navigation, Type Ownership, State Ownership, and Mapping documents from it; do not maintain duplicate descriptions in generated Markdown.

## Version policy

- Only schema 2.0.2 input is supported.
- Standard and schema versions advance together.
- An earlier project requires a new human-owned source-set and as-is inventory. Never infer source intent, type/state ownership, authority, or mapping and never silently generate a 2.0.2 manifest.
- Internal validation layers preserve 1.0 through 2.0.1 rules but are not public schema entry points.

## Top level

```yaml
standard_version: "2.0.2"
schema_version: "2.0.2"
project:
  name: "example"
  documentation_language: "zh-TW"
source_sets:
  - id: "formal-program"
    classification: "production"
    include: ["src/**"]
    exclude: ["src/generated/**"]
    purpose: "Govern maintained product source."
    provenance: "Human-maintained repository source."
  - id: "generated-adapter"
    classification: "generated-production"
    include: ["src/generated/**"]
    exclude: []
    purpose: "Compile generator-owned adapter source without catalog migration."
    provenance: "Vendor generator output."
    generator: "vendor-generator 1.0"
    owner: "technology_adapter"
modules: []
ports: []
events: []
types: []
type_exclusions: []
state_objects: []
boundary_mappings: []
flows: []
adr_exceptions: []
c_analyzer:
  ast:
    status: "required"
    rationale: "Governed C translation units require complete AST evidence."
    compilation_database: "compile_commands.json"
    target_triple: "arm-none-eabi"
```

## Logical source sets

Every formal declaration path must match exactly one source set after `exclude` patterns are applied. Overlap, missing classification, absolute paths, and parent traversal are configuration-blocking. Never infer classification from path names or generated-file comments.

- `production` receives complete Module, Type, State, dependency, and AST governance.
- `generated-production` requires generator provenance and an L3+ owner. Mutable globals become catalog-only evidence; direct access outside the owner and leakage through L0-L2 contracts are blocking.
- `development`, `derived-documentation`, and `build-output` cannot back formal Modules, Types, State, entrypoints, public symbols, or production compilation-database entries.

Schema 2.0.1 input is rejected. There is no automatic migration because source intent cannot be inferred safely.

`documentation_language` controls generated fixed labels. `zh-TW` and English language tags are supported.

## Module description

Schema 2.0.2 retains the 1.1 module description contract. Each module requires `implementation_status: planned|implemented`, `paths`, `entrypoints`, `public_symbols`, and this explicit description shape:

```yaml
description:
  purpose: "What this module owns"
  input_ports: []
  output_ports: []
  emitted_events: []
  owned_state: []
  side_effects: []
  errors: []
  invariants: []
```

All lists must exist even when empty. References must resolve to objects owned by the module where ownership applies. Paths are project-relative and cannot traverse above the project.

Each entrypoint and public symbol declares `path`, `symbol`, and `kind`. Implemented module files and C/C++ symbols are MUST requirements. Missing planned files or symbols are SHOULD warnings. An unsupported language receives an explicit unverified-symbol warning.

Implemented modules cannot contain blank or `TODO` placeholders.

## Named Type Catalog

Every named project type under governed source paths requires one `types` entry. This includes structs, unions, enums, classes, typedefs, aliases, named function-pointer types, interfaces, protocols, DTOs, and schemas.

```yaml
types:
  - id: "io-endpoint-binding"
    owner: "gpio_adapter"
    language: "c"
    declaration:
      path: "src/gpio/io_binding.h"
      symbol: "IoEndpointBinding"
      kind: "struct"
    visibility: "private"
    semantic_kind: "adapter-binding"
    description: "Map a demand-owned endpoint ID to one GPIO channel."
    lifetime: "Static process lifetime."
    mutability: "immutable"
    mutation_authority: []
    consumers: ["gpio_adapter"]
    references: ["io-endpoint-id"]
    fields:
      - name: "endpoint_id"
        type: "IoEndpointId"
        role: "domain-identity"
        meaning: "Demand-owned logical endpoint identity."
      - name: "channel"
        type: "uint16_t"
        role: "adapter-binding"
        meaning: "Concrete GPIO channel."
```

Record kinds declare `fields`; enums declare ordered `values`; aliases declare `target`; function pointers declare `signature.returns` and `signature.parameters`. Runtime state and private helpers remain private. L0-L2 public types cannot contain adapter bindings, framework handles, wire representations, or storage representations. A domain reference may coexist with an adapter/framework field only in a private L3+ adapter binding or private L0 composition mapping.

Vendor and generated declarations may be excluded only through an L3+ entry:

```yaml
type_exclusions:
  - path: "vendor/stm32/**"
    owner: "gpio_adapter"
    classification: "vendor"
    source: "STM32 firmware library 3.5.0"
    reason: "Externally maintained declarations are wrapped by adapter-private code."
```

Excluded types must not leak into L0-L2 public contracts.

`references` is required, including when empty. It lists every referenced project Type Catalog ID; primitive and external standard types are omitted. The referenced owner must be reachable through a legal declared dependency and Port direction.

## State Object Ownership Matrix

Every mutable file-scope, static-storage, thread-local, or `extern` object and every object whose address crosses a module boundary requires one entry:

```yaml
state_objects:
  - id: "domain-runtime"
    owner: "domain_module"
    language: "c"
    declaration:
      path: "src/domain/runtime.c"
      symbol: "g_Runtime"
      storage: "file-static"
    type: "DomainRuntime"
    type_ref: "domain-runtime-type"
    visibility: "private"
    lifetime: "Process lifetime."
    mutability: "owner-mutable"
    read_authority: ["domain_module"]
    write_authority: ["domain_module"]
```

Use `file-static`, `external-linkage`, or `thread-local` for storage. Each corresponding module `description.owned_state` row includes `ref` to this ID. Private state cannot grant authority to another module or use C/C++ external linkage.

## Boundary Design Table

Each cross-module behavior is recorded before source editing:

```yaml
boundary_mappings:
  - id: "measurement-to-control"
    interaction: "Convert a producer result into a consumer command."
    producer: "measurement_domain"
    consumer: "control_domain"
    parent: "application"
    producer_contract: "measurement-result"
    consumer_contract: "control-command"
    mapping_owner: "application"
    state_objects: []
    allowed_edges: ["application->measurement_domain", "application->control_domain"]
    forbidden_edges: ["measurement_domain->control_domain", "control_domain->measurement_domain"]
```

When direct contract use is legal, producer and consumer contract IDs may be the same and no conversion type is required. Distinct sibling-owned contracts require their shared parent as mapping owner. Parent-owned mapping types stay private and never appear in child public APIs.

## Port description

Every port retains `id`, `owner`, `direction`, `kind`, `contract`, and `implemented_by`, and adds:

```yaml
description:
  purpose: "Why the port exists"
  data: "Semantic meaning of the exchanged data"
  timing: "sync" # or async
  immediate_rejections:
    - code: "busy"
      condition: "The module already has accepted work"
symbols:
  - "ExampleInputPort"
```

Every named symbol must appear in the owner module's `public_symbols`.

## Event description

Every event retains its owner, output port, delivery semantics, envelope, lifecycle, and conditional idempotency requirements, and adds:

```yaml
description:
  purpose: "What consumers learn"
  emitted_when: "The state commit has completed"
  payload_fields:
    - name: "value"
      type: "float"
      meaning: "Validated reading in degrees Celsius"
  intended_consumers:
    - "consumer_module"
```

## End-to-end flow

Only L0 and L1 modules own flows. Each flow requires an ID, owner, description, trigger, contiguous uniquely ordered steps, success result, and structured error branches. Step module, port, and event references must exist.

Each error branch contains `condition`, either a defined `event` or a stable `code`, and `handling`. Public commands and events not referenced by any flow generate SHOULD warnings. Do not model private L2 algorithm steps as top-level flows.

## ADR exceptions

```yaml
adr_exceptions:
  - rule_id: "DEP002"
    scope: "src/legacy"
    adr: "decisions/ADR-0007-legacy-dependency.md"
    status: "accepted"
    approved_by: "user-name"
    approval_reference: "Codex task or review reference"
```

The checker rejects an accepted exception approved by `GPT`, `Codex`, `AI`, or another obvious model identity.

## Baseline

The baseline schema version must match the manifest. It contains exact known violations as `(rule_id, location)` pairs. Do not add a baseline entry for new or touched code. In CI, pass the target branch baseline as `--previous-baseline`; rule `BAS004` blocks growth while allowing entries to be removed.

## Inherited requirements

The sections above use the current 2.0.2 shape. All rules from 1.0 through 2.0.1 remain blocking. Version 2.0.2 adds formal-source classification and generated boundaries and removes no inherited governance.
