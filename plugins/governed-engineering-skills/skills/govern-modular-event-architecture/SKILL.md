---
name: govern-modular-event-architecture
description: "Govern cross-language modular event architecture, production-source boundaries, named-type and runtime-state ownership, product algorithms, and hard/soft real-time scheduling analysis. Use when Codex creates, reviews, explains, improves, or refactors architecture or algorithms; changes structs, classes, enums, unions, typedefs, DTOs, schemas, runtime state, configuration, ports, events, callbacks, adapters, module boundaries, data flow, execution units, Tasks, priorities, activation rates, core allocation, generated production sources, or architecture views; or checks conformance. Enforce schema 2.1.0 classification, authoring-first L0-L3+ responsibilities, pre-code boundary/type/state/scheduling gates, Type Catalogs, dependency inversion, contracts, fail-closed C/C++ AST evidence, Algorithm Design Records, Description Views, ADR-controlled exceptions, and validation. Invoke explicitly with $govern-modular-event-architecture."
---

# Govern Modular Event Architecture

Apply a language-independent modular architecture whose behavior can be read by people and checked by tools.

## Select the workflow

1. Inspect the repository before asking questions. Look for `AGENTS.md`, `architecture/manifest.yaml`, `architecture/ARCHITECTURE.md`, ADRs, baselines, build files, source paths, and tests.
2. For a new project whose design is not already confirmed, clarify product features and algorithm screening before finalizing the system flows, L0-L3+ modules, parents, ports, events, delivery semantics, quality constraints, and validation in Plan mode before creating files. If Plan mode or its structured choice tool is unavailable, ask the user to switch modes and stop. A previously confirmed plan plus an explicit implementation request satisfies this checkpoint.
3. For an existing project, map the current architecture, every named type, runtime state object, composition root, and every L1/L2 product feature and algorithm first. Derive ownership from actual reads, writes, side effects, lifetime, consumers, and external-technology use. Remediate every discovered violation by default. Use a temporary baseline only when a non-AI developer explicitly defers that exact rule/location with rationale, approval reference, captured revision, review date, and removal condition. Never rewrite the manifest or use an empty baseline to make incomplete adoption appear compliant.
4. For an architecture proposal, invoke `$clarify-improvement-proposals` and remain in Plan mode. If the current mode is not Plan or the structured choice tool is unavailable, tell the user to switch with `/plan` or `Shift+Tab`, then stop. Do not provide a preliminary architecture unless the user explicitly requests one.
5. For confirmed implementation in an execution-capable mode, pass the pre-code gate below before editing source. Then update the manifest catalogs, documentation, ADRs, code, and tests together. Run the checker and applicable language analyzers and report evidence.

Do not let implicit invocation bypass clarification, mode checkpoints, approval requirements, or repository instructions.

## Load the required references

- Read [references/core-standard.md](references/core-standard.md) before defining levels, modules, dependency direction, or migration policy.
- Read [references/event-contract.md](references/event-contract.md) before defining ports, callbacks, commands, queries, events, ordering, fan-out, or retries.
- Read [references/manifest-schema.md](references/manifest-schema.md) before creating or changing `architecture/manifest.yaml` or a baseline.
- Read [references/description-views.md](references/description-views.md) before defining module descriptions, flows, code links, generated System views, or Parent views.
- Read [references/adr-policy.md](references/adr-policy.md) before proposing or applying a MUST-rule exception.
- Read [references/algorithm-design.md](references/algorithm-design.md) before screening product features, selecting or changing an algorithm, defining algorithm acceptance criteria, or inventorying an existing project's algorithms.
- Read [references/c-analyzer.md](references/c-analyzer.md) when C/C++ sources, headers, includes, or framework leakage are in scope.
- Read [references/runtime-validation.md](references/runtime-validation.md) when physical devices, OS scheduling/resource traces, test-only runtime control, Serial/TCP capture, or high-frequency statistics are in scope.
- Read [references/execution-efficiency.md](references/execution-efficiency.md) before defining Tasks, Threads, ISR/Event Loop/Worker allocation, Queue capacity, priority, affinity, data layout, cache/branch/SIMD behavior, compiler optimization, or platform performance budgets.
- Read [references/realtime-scheduling-analysis.md](references/realtime-scheduling-analysis.md) before defining or changing hard/soft real-time Task count, activation rate, priority, core allocation, Queue/notification timing, synchronization blocking, scheduler method, or deadline/SLO acceptance.
- Read [references/flow-cost-review.md](references/flow-cost-review.md) before retaining or changing an end-to-end Flow, callback topology, execution context, Queue, data movement, resource model, real-time claim, or maintainability/extensibility recommendation.

## Enforce the standard

- Treat `MUST` as blocking, `SHOULD` as a recorded warning, and `MAY` as optional.
- Permit a MUST exception only through an accepted ADR with a non-AI approver and an approval reference. Codex may draft an ADR but MUST NOT approve it.
- Keep the project pinned to explicit standard and schema versions.
- Require schema `2.1.0`. Reject earlier manifests; do not migrate or infer source classifications, owners, authorities, mappings, or real-time timing bounds.
- Require exactly one release `composition_roots` entry and verify its path and symbol with the applicable language analyzer.
- Treat `architecture_cli.py` as the only public governance CLI. Checker, renderer, bootstrap, and language-analyzer scripts are internal modules and direct legacy invocation is unsupported.
- For governed C/C++, require `clang==20.1.5` bindings plus the project
  toolchain lock's official Espressif libclang provider. Never load native
  libclang from the Python package, `PATH`, or an unrecorded location.
- Separate tool-host OS/Python compatibility metadata from governed-project Execution Profiles. Execution Profiles describe the target whose behavior is being assured.
- Distinguish discovery, remediation, approved deferral, verified evidence, blocked capability, and failure. An empty baseline is not completion evidence.
- Default to remediation for discovered legacy debt. Development may tolerate only exact, unexpired, non-AI-approved temporary deferrals; Release requires a zero-entry temporary baseline. Durable exceptions require an accepted ADR.
- Require explicit logical source sets. Fully govern only `production`; treat `generated-production` as a generator-owned L3+ boundary; exclude `development`, `derived-documentation`, and `build-output` from formal catalogs.
- Never copy, move, redeclare, or hand-edit generated source to satisfy a catalog. Correct the classification, consumer boundary, generator template, or owning adapter instead.
- Inventory every governed named type before editing code. For each type and field, record its owner, semantic role, declaration, visibility, lifetime, mutability, mutation authority, consumers, and ABI/wire/storage impact.
- Treat an unresolved Type Ownership Matrix as blocking. Renaming a type, adding a typedef alias, or moving fields does not prove architectural separation.
- Require one semantic owner per named type. Keep runtime state owner-private. Keep adapter bindings and framework handles in private L3+ types or private L0 composition mappings.
- Reject L0-L2 public contracts that expose adapter bindings, framework handles, wire representations, or storage representations.
- Require demand-side ownership of ports at cross-module and external-technology boundaries. Do not force ports around private pure functions.
- Require parent orchestration for L0-L2 sibling communication. Keep concrete adapters in the composition root.
- Require a single output port per functional module; place subscriber fan-out outside the module.
- Require commands to distinguish immediate rejection from accepted work that later succeeds or fails. Permit side-effect-free queries to return synchronously.
- Keep test and runtime evidence adapters at L3+. Require demand-owned observability/test ports and test-only composition wiring; never ship a test command parser merely to simplify validation.
- Screen every product feature for algorithm impact. Require a complete `ALG-####` record for triggered features and a specific `not applicable` reason for non-triggered features.
- Keep logical Modules separate from runtime Execution Units. Confirm the platform with a human, classify Flow workloads, and govern the inherited execution-profile rules before claiming execution efficiency.
- Evaluate every material Flow through functional admission, execution and
  real-time feasibility, maintainability/extensibility change scenarios, and
  model assurance. Preserve external compatibility independently from internal
  orchestration. Do not select a platform performance winner from an
  `estimated` model.
- For every hard/soft real-time workload, require at least two structurally different scheduling candidates, scheduler-compatible provisional analysis, a generated human-readable Markdown study report, and explicit non-AI selection before source edits. Use RMA/RTA only for the supported RM fixed-priority model. Hard deadline misses fail; soft misses require a quantified SLO plan and non-AI risk acceptance, then final SLO evidence.
- Require Tier 1 cost analysis for hard-real-time workloads. Treat layout, tiling, branch, SIMD, PGO, LTO, scheduling, and load-balancing choices as algorithm-bearing.
- Keep private L2 algorithm steps out of top-level Flow descriptions. Link Algorithm Design Records to their owning L1/L2 module and applicable Flow IDs.
- Require human approval metadata before an algorithm record becomes `accepted`; Codex may draft a record but MUST NOT approve it.
- When an algorithm changes public I/O, state, events, errors, side effects, timing, resource contracts, module boundaries, or dependency direction, update the manifest, Description Views, ADRs when applicable, code, and tests together.

## Pass the architecture authoring gate before source edits

For every architecture-affecting change, complete this sequence in order:

1. State the responsibility and observable behavior.
2. Complete the evidence-calibrated Flow Review. For an existing project,
   reconstruct the as-is Flow and production-equivalent baseline. For
   Greenfield, define end-to-end Flow and a portable estimate before fixing
   Modules, Ports, Events, Tasks, or Queues. Compare at least two structurally
   different candidates for a Flow-affecting decision.
3. Resolve platform/toolchain semantics, budgets, benchmark triggers,
   prediction error, reserve sources, and the model-assurance verdict. Logical
   design may continue without platform facts, but platform performance and
   real-time decisions remain `BLOCKED`.
4. Select the L0-L3+ module owner.
5. Define commands, queries, events, and external Ports.
6. Assign one semantic owner to every public contract.
7. Produce the Type Ownership Matrix.
8. Produce the State Object Ownership Matrix.
9. List actual and intended dependency edges.
10. Define parent mapping and orchestration.
11. For hard/soft real-time work, complete the scheduling study and obtain human selection of a provisional-PASS candidate; a soft-only `SOFT_RISK` additionally requires an SLO plan and human risk acceptance.
12. Validate the planned manifest without source-completeness checks.
13. Edit source only after the design result is `PASS`.

The Boundary Design Table MUST contain Interaction, Producer, Consumer, Parent, Producer contract, Consumer contract, Mapping owner, State accessed, Allowed edges, and Forbidden edges. The Type Ownership Matrix MUST also record referenced project types and ABI, wire, and storage impact. The State Object Ownership Matrix MUST inventory mutable file-scope/static/thread-local objects, extern objects, and objects whose addresses cross module boundaries.

Any unresolved owner, illegal dependency, missing authority, mapping, source classification, or real-time schedulability input makes the gate `BLOCKED`. Do not first create a struct, getter, shared header, global, Task, or copied generated declaration and then rewrite the manifest to justify it. Use `python scripts\architecture_cli.py gate --phase design --manifest architecture\manifest.yaml`; source completeness is deferred until implementation, but source-set membership and all declared design relationships are blocking.

Any unresolved load-bearing Flow unit, callback/indirect path, build
composition, platform fact, timing/resource budget, interference source,
scenario coverage, prediction overrun, or reserve source also makes the
applicable execution/model claim `BLOCKED`. Static analysis and runtime
measurement cross-check one another; neither alone validates unexecuted or
unresolved paths. Physical and OS-native calibration routes through
`$validate-on-device`, followed by a separate release-equivalent
non-regression check.

## Initialize a project

After decisions are confirmed, prepare a YAML spec with the same complete top-level shape as `architecture/manifest.yaml`, then run:

```powershell
python scripts\architecture_cli.py bootstrap `
  --project-root <project-root> `
  --spec <confirmed-spec.yaml>
```

Resolve a project-specified or available Python 3 runtime first and confirm it can import the pinned requirements. If no suitable runtime exists, report `BLOCKED` with remediation instead of substituting a user-specific absolute path.

The bootstrapper refuses to overwrite governance files. Review every generated document before treating it as accepted. Every new project includes an architecture-adoption ADR with `proposed` status; it remains proposed until the user explicitly approves it.

For a C/C++ project, bootstrap also writes
`architecture/toolchain-lock.yaml`. Provision its native provider explicitly;
ordinary gates remain offline:

```powershell
python tools\architecture\architecture_cli.py toolchain install `
  --lock architecture\toolchain-lock.yaml
python tools\architecture\architecture_cli.py toolchain verify `
  --lock architecture\toolchain-lock.yaml
```

Python-only projects receive the provider-capable CLI modules but no toolchain
lock and require no native libclang installation.

New projects use schema `2.1.0`. Schema 2.1.0 retains all 1.0 through 2.0.2 requirements and adds workload-driven real-time scheduling studies. The manifest is the only editable source for Architecture Description Views and generated scheduling reports; generated Markdown is never edited by hand.

## Render description views

For a schema 2.1.0 project, regenerate checked-in views after every manifest change:

```powershell
python tools\architecture\architecture_cli.py render `
  --manifest architecture\manifest.yaml `
  --adoption architecture\adoption.yaml `
  --baseline architecture\baseline.yaml
```

Use `--check` in validation. The generic checker performs the same exact in-memory stale comparison. Earlier projects require human-owned source sets, architecture, type inventory, state inventory, boundary design, and applicable real-time timing inputs before creating a new 2.1.0 manifest; this skill provides no migration command.

## Validate a project

Prefer the project-local checker copied by the bootstrapper:

```powershell
python tools\architecture\architecture_cli.py gate `
  --phase development `
  --manifest architecture\manifest.yaml `
  --adoption architecture\adoption.yaml `
  --baseline architecture\baseline.yaml `
  --format text
```

The single CLI dispatches every applicable language analyzer. For Python it requires complete stdlib AST coverage of types, runtime state, imports, declared symbols, and composition roots. For C/C++, install the pinned requirements, explicitly install/verify the locked provider, configure a complete compilation database and target triple, and govern every translation unit. Libclang AST evidence is mandatory; lexical scanning is supplemental and cannot prove ownership PASS. Provider, native-library, binding-version, or Xtensa backend failures are `CAST001`; invalid lock, platform, cache, or receipt configuration is `CAST002`; compilation-database coverage and real translation-unit parse failures remain `CAST003`. Exit code `0` is pass, `1` is a source/design MUST violation, and `2` is `BLOCKED` because capability, configuration, coverage, or parsing evidence is incomplete.

Report the exact command, exit code, minimal raw output, and `PASS`, `FAIL`, or `BLOCKED`. Do not declare completion while a required validation is not `PASS`.

After static architecture checks pass, use `$validate-on-device` for required runtime evidence. The target project manually selects its native provider and declared fallback. Do not treat application logs as OS scheduler proof when native traces are selected, and do not treat a successful build as physical-device evidence.
