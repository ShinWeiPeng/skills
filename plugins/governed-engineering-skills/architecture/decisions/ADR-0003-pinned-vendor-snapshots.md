# ADR-0003: Pinned vendored skill snapshots

- Status: proposed
- Date: 2026-07-29

## Context and problem

The plugin combines promoted Matt Pocock skills with locally maintained governance skills. Blind refreshes could erase integration gates, while absolute local source paths would make the plugin non-portable.

## Decision

Pin the Matt source to commit `2ab9580`. Record source and integrated SHA-256 values in `vendor-lock.json`. Permit deterministic refresh of unmodified snapshots; stop with `BLOCKED` when a source change intersects an integration overlay. Require source roots as explicit refresh arguments and never store user-specific absolute paths.

## Alternatives considered

- Symlink installed skills: rejected because plugin packaging can discard or dereference links unpredictably.
- Blind copy on update: rejected because it can silently remove governance gates.
- Maintain unrelated forks per skill: rejected because it multiplies release and review surfaces.

## Benefits, costs, and tradeoffs

The installed plugin is self-contained and drift is detectable. Updating overlaid skills requires a deliberate review and lock refresh.

## Risks and mitigations

- Stale snapshots: expose `vendor_sync.py --check` and an explicit refresh command.
- Accidental local artifacts: exclude Python caches, prior evidence, and user-specific paths.
- Source attribution ambiguity: keep source kind, relative source path, and pinned commit in the lock.

## Compatibility and migration impact

No upstream manifest or package metadata changes. This first version is local and Codex-only.

## Validation and observable pass conditions

- Every locked integrated hash matches the installed directory.
- Overlay source drift returns exit code `2` and names the skills requiring review.
- HackMD and other non-engineering personal skills are absent.

## Approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
