# Architecture Description Views

Description Views make a valid architecture understandable without adding runtime structs, ABI, ROM, or RAM cost. The manifest is the only editable source; the renderer produces deterministic checked-in Markdown.

## Information model

- The System view shows all modules, levels, parent relationships, summary cards, Port/Event contracts, Type Ownership, State Ownership, cross-module Mapping, and navigation. This ensures unparented L3+ technical adapters remain documented.
- One Parent view is generated for each L0 and L1 module. It contains its local structure, child module cards, owned Port, Event, Type and State cards, relevant mappings, and end-to-end flows.
- Module cards explain purpose, I/O, emitted events, state, side effects, errors, invariants, source paths, entrypoints, and public symbols.
- Flow views use a Mermaid sequence diagram plus an exact ordered-step table. They describe externally meaningful movement across modules, not private algorithms.
- Schema 2.0.2 retains one generated `execution-<profile-id>.md` page per platform profile. Parent Flow sections link workloads to those pages and expose Task/Thread/ISR/Queue boundaries without equating Modules to Execution Units.
- Paths and symbols link architecture claims to their declared source files. They do not promise a line-level source anchor. Rename them in the manifest in the same change as code.

## Generated files

```text
architecture/
├─ ARCHITECTURE.md
└─ generated/
   ├─ system.md
   ├─ <l0-module>.md
   └─ <l1-module>.md
```

Every generated page begins with the legal `DO NOT EDIT` marker. Design rationale remains in manifest descriptions and ADRs.

`render_architecture.py --write` may overwrite or remove only files carrying that marker. If an expected output path contains a manual file, rendering stops. Unrecognized manual files under `generated/` are preserved and reported rather than deleted.

## Validation

`render_architecture.py --check` renders in memory and compares exact bytes. Missing, changed, or obsolete marker-owned pages are MUST stale violations. The generic checker performs this check for schema 2.0.2, so source sets, manifest, Type/State catalogs, boundary mappings, and generated documentation cannot drift silently.

## Authoring guidance

- Describe responsibilities in domain language; do not merely repeat identifiers.
- Render every Type Catalog row with referenced project types, every State Object row with storage and read/write authority, and every Boundary Mapping row with both allowed and forbidden edges.
- State data meaning, not only language types.
- State each named type's owner, declaration, visibility, semantic kind, consumers, field roles, and mutation authority.
- State when an event is emitted and what state has already committed.
- Record immediate command rejection separately from accepted-work failure.
- Include error handling outcomes, not just error names.
- Prefer a few end-to-end flows owned by L0/L1. Keep L2 implementation details in module cards and code.
