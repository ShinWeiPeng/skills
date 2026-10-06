---
name: coding-standards
description: Apply shared coding rules to module, memory, boundary, error and data-flow changes using each project's platform and resource constraints. Invoke before code changes and during review; leave execution authorization and architecture workflows with their existing owners.
---

# Coding standards

Use one shared, versioned set of rules across projects. Determine applicability
from the project's actual platform, resource budgets and execution paths, rather
than a global preference for MCU or PC development.

## Before design or code changes

1. Read [applicability](references/applicability.md) and
   [versioning](references/rule-versioning.md). Reconcile the project's recorded
   rule version; keep unresolved facts explicit and block only dependent choices.
2. Read the applicable topic files below. Record rule IDs and reasons for
   applicable, not-applicable or unresolved results in the project's design data.
   Populate the manifest's `coding_rules` and `implementation_design` extensions;
   require the architecture design gate before confirmation. A legacy manifest's
   readability does not exempt it from this adoption step.
3. Present the module/interface and affected flow designs through architecture
   governance before SPEC confirmation: concrete methods, copies, capacities,
   ownership, completion, failure and shutdown. Do not defer those choices until
   debugging. The existing SPEC/execution authorization remains in force.
4. Implement against the same rule version and approved design. Reopen actual
   requirement changes through the SPEC owner; an implementation convenience is
   not permission to change a contract.
5. Review actual callers, source and runtime evidence against the designs using
   the [verification map](references/verification/rule-verification-map.md).
   Report unsupported or missing evidence explicitly.

## Rule topics

- [Module boundaries and public interfaces](rules/module-boundaries.md)
- [Named types and mutable state](rules/type-and-state-ownership.md)
- [Allocation, capacity and resource lifetime](rules/memory-management.md)
- [Boundary validation](rules/boundary-validation.md)
- [Abnormal events, persistent state and recovery](rules/error-handling.md)
- [Data flow, aggregation, backpressure and completion](rules/data-flow.md)
- [Platform optimization and instrumentation](rules/execution-and-platform.md)

Only rule ID, strength, applicable conditions and program requirement belong in
these files. Rules do not prescribe agent steps, document generation or tools.
MUST is required when applicable; SHOULD deviations need a reason; MAY does not
waive a MUST. Architecture exceptions and temporary baseline policy remain with
architecture governance, including human approval and zero temporary debt at release.

ADR format and lifecycle belong to the plugin's shared references/adr directory,
not this Skill. Domain modeling and architecture governance retain their separate
professional responsibilities.

## OS and execution environment

Apply the seven conditional OS rules in `rules/os-execution.md` from catalog version 2. OS facts come from the platform design; the execution design owns Task mappings, channels, synchronization, resources, timing and lifecycle. Read the architecture-owned platform/execution formats and OS phase checks before confirming design. Keep unknown facts explicit; reconcile a changed catalog before implementation.
