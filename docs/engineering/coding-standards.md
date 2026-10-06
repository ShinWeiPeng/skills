Availability:

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/coding-standards)

# Coding standards

Shared coding rules stay in one maintained set of topic files, while each project
uses its own CPU, OS, compiler, memory budget and execution constraints to decide
which clauses apply. A PC label does not remove limits; an MCU label does not
automatically prohibit heap allocation.

## Designs before implementation

Before confirmation, you see the module's public contracts and concrete data-flow
method: copies, buffers, capacity, ownership, completion, errors and shutdown.
After implementation, review compares the real code with those choices. Unknown
facts and unsupported checks remain visible rather than becoming assumed passes.

## Where it fits

This is a model-invoked step before implementation and during review, routed by
[ask-matt](https://aihero.dev/skills-ask-matt). It provides coding clauses to
[architecture governance](https://aihero.dev/skills-govern-modular-event-architecture),
which owns design records and checks. Domain modeling keeps terminology; ADR
format and lifecycle are shared plugin documents.

## OS and execution environment

Apply the seven conditional OS rules in `rules/os-execution.md` from catalog version 2. OS facts come from the platform design; the execution design owns Task mappings, channels, synchronization, resources, timing and lifecycle. Read the architecture-owned platform/execution formats and OS phase checks before confirming design. Keep unknown facts explicit; reconcile a changed catalog before implementation.
