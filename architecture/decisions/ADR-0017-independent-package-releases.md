# ADR-0017: Independent packages in one skills repository

- Status: proposed for review in SPEC-0064 implementation PR
- Source: SPEC-0064 DEC-004 and DEC-005
- Refines: ADR-0013 and ADR-0014

The existing engineering source is relocated beneath governed-engineering-skills. Repository and package roots are explicit; immutable artifact paths, plugin identities, tag format and marketplace-release remain compatible. Source inventory selects tracked package paths from the Git root and normalizes them to artifact logical paths.

Each package owns version metadata, release intent, changesets, Version PR and generated publication branch. The repository CI helper is development tooling, outside installed production Skill sources. It coordinates package-owned commands and stages only a declared package root. Generated publication uses a separate Git index, inspected expected base and force-with-lease; the source checkout and index remain intact.

Path selection determines checks, not release identity. Existing tags are validated by package version and production fingerprint, so unrelated commits do not invalidate releases. Identical artifacts are no-ops; same-version different content is rejected. A tag and a publication ref are separate recoverable steps.

Alternatives: a common version couples unrelated packages; a shared consumer branch requires merging last-released artifacts and serializing publishers. Independent branches preserve the engineering consumer contract. No architectural MUST-rule exception is introduced.

Validation: temporary real Git repositories, isolated publication lease tests, clean tracked checkout rehearsal, package contracts and architecture gate. Approval remains with the human reviewer; this record does not invent an approval signature.

## Root entrypoint cleanup

SPEC-0064 DEC-009 records the maintainer's explicit decision that old root paths are unnecessary. Installation, assembly and validation use the engineering package entrypoints directly; the five root aliases are removed. Package launcher argument/exit-code contracts and the complete release checks remain required. This updates the source-tree entrypoint placement described by ADR-0014 without changing the generated marketplace identity or its consumer path.
