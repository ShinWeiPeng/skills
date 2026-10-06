# ADR-0008: Validate archive links without materializing them

- **Status:** accepted
- **Date:** 2026-08-01

## Context

ADR-0007 required archive extraction to reject every symbolic-link and
hard-link entry. The lock-pinned official Linux `esp-clang-libs
20.1.1_20250829` artifact has the expected SHA-256 but contains the safe alias
`esp-clang/lib/libLLVM.so -> libLLVM.so.20.1`. Rejecting that entry blocks the
official provider on every supported Linux and Python combination even though
the locked `libclang.so.20.1.1` is a regular file and the installer does not
need to create the alias.

## Decision

Replace ADR-0007's blanket archive-link rejection with validation without
materialization:

- Every member name remains subject to absolute-path, separator, traversal, and
  resolved-destination containment checks.
- A symbolic-link or hard-link target must be non-empty, POSIX-relative, use no
  backslashes, and contain no parent-traversal component.
- A link entry that passes validation is skipped. The installer never creates a
  filesystem symbolic link or hard link.
- An unsafe link target and every unsupported special entry remain fail-closed
  `CAST002` failures.

All archive, library, receipt, provider, binding, and capability hashes and
checks from ADR-0007 remain unchanged.

## Alternatives considered

- Reject every link: preserves the original rule but makes the pinned official
  Linux artifact unusable.
- Materialize validated links: preserves archive aliases but creates
  unnecessary filesystem link semantics and a larger extraction attack surface.
- Skip links without validating targets: links remain inert, but suspicious
  archive metadata would no longer fail closed.

## Benefits, costs, and tradeoffs

The official Linux provider installs while archive links remain incapable of
changing the extracted filesystem. The added target validation is intentionally
stricter than general tar semantics and may reject an otherwise-contained alias
that uses `..`; supporting such an artifact would require a separately reviewed
normalization rule.

## Risks and mitigations

- Link-based writes are prevented because no link is materialized.
- Absolute, backslash, and parent-traversal targets are rejected before any
  regular member is written.
- Regular member writes retain resolved-destination containment checks.
- The pinned archive and library SHA-256 values still prevent artifact
  substitution.

## Compatibility and migration impact

This changes only explicit toolchain installation on archives containing safe
links. Cache format, receipt schema, lock schema, public CLI, verification,
provider identity, and existing valid caches are unchanged.

## Validation

- Prove safe symbolic-link and hard-link entries pass `install()` but are not
  materialized.
- Prove unsafe symbolic-link and hard-link targets remain `CAST002`.
- Preserve member traversal and resolved-containment regression tests.
- Verify the official Linux artifact hash and link target.
- Run unit, integration, Changesets, version-governance, architecture
  development, and architecture release gates.
- Require the GitHub Actions Windows/Linux and Python 3.11-3.13 matrix to pass.

## Supersession

When accepted, this ADR supersedes only ADR-0007's requirement to reject every
archive link entry. All other ADR-0007 decisions remain in force.

## Approval

- **Approver:** human project owner
- **Approval date:** 2026-08-01
- **Approval reference:** Codex task explicit approval: `批准 ADR-0008`
