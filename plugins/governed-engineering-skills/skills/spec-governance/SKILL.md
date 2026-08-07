---
name: spec-governance
description: Persist, reconcile, materialize, reopen, resolve, and verify the canonical repository specification for every modifying engineering change set. Model-invoked by ask-matt and delivery workflows.
---

# Spec governance

Own one canonical change-set contract from the first governed decision through
verified implementation and commit disposition.

## Public interfaces

- `spec-governance.start`: resolve an existing bundle by explicit reference,
  task/branch evidence, then unique fallback, or create
  `.codex/spec-governance/<working-id>/working.md` plus `journal.jsonl`. Ambiguity is
  `BLOCKED`.
- `spec-governance.reconcile`: classify each new statement as a domain term,
  change-set contract, ADR candidate, or open decision; preserve stable IDs; reject
  stale revision/hash writers; atomically persist the Markdown snapshot and append
  one normalized hash-linked journal event before another question; then show the
  Spec delta, affected IDs, relationships, conflicts, open decisions, and
  `PASS/BLOCKED` verdict.
- `spec-governance.materialize`: when decision-complete, write
  `specs/SPEC-####-<feature-slug>.md` using the next repository-wide four-digit
  number without waiting for `開始執行`. This spec-only write never grants product
  execution authority.
- `spec-governance.reopen`: before clarifying a possible contract change, change a
  confirmed unimplemented spec to `working` in the same ID/path and create its
  bundle. Implemented specs are immutable.
- `spec-governance.prepare-commit`: inspect whether local bundles are tracked or
  staged and require an explicit delete, keep-local, or normalized-journal archive
  disposition. It never performs the disposition or Git operation itself.
- `spec-governance.verify`: resolve the active spec, validate structure and
  REQ → AC → validation seams, and return `PASS` or `BLOCKED` before TDD or
  implementation.

Use `scripts/spec_contract.py start|status|reconcile|materialize|reopen|prepare-commit`
for the lifecycle, `validate --spec <path>` for the strict Markdown contract, and
`resolve --project-root <root> --prompt <request> --branch <branch>` for deterministic
canonical resolution.

## Reconcile loop

Before the first decision, invoke `start` or `status`. After each user answer:

1. Reload the authoritative `working.md`; reuse unchanged REQ, DEC, and AC IDs.
2. Compare it with non-empty `CONTEXT.md`, accepted ADRs, and the architecture
   manifest.
3. Reconcile using its expected revision and SHA-256. Atomically replace the complete
   human-readable Markdown snapshot, then append only normalized delta, IDs,
   relations, conflicts, open decisions, verdict, revision, and hashes to JSONL.
   Never persist raw chat or hidden reasoning.
4. Render the Spec delta, affected IDs, explicit relations, conflicts, open
   decisions, and consistency verdict.
5. When blocked, ask exactly one conclusion-changing question.
6. When complete, materialize or reconfirm the canonical spec immediately. Render
   the confirmed spec and intended non-spec diff, then wait for exact product
   execution authorization.

If the journal is missing or its chain is invalid, trust `working.md`, start a new
epoch marked `continuity: unavailable`, and continue from settled IDs. Do not turn
journal loss alone into reopened decisions.

Route domain vocabulary to `CONTEXT.md`, change-set requirements and acceptance to
the canonical spec, qualifying architectural decisions to a **proposed** ADR, and
unconfirmed content only to the working spec. During grilling, only
`.codex/spec-governance/**` and `specs/SPEC-####-*.md` lifecycle writes are allowed.
`CONTEXT.md`, ADRs, architecture artifacts, tests, generated views, implementation,
Git, and external actions still require exact `開始執行`. These outputs are one
change set; do not recursively start another interview.

## Canonical contract

Each spec contains metadata (`spec_version`, `spec_id`, `revision`, `status`,
`change_set`), Problem, Solution, User Stories, Requirements, Decisions, Acceptance
Criteria with validation methods and evidence, Relationships (`depends_on`,
`refines`, `conflicts_with`, `supersedes`), Out of Scope, Open Decisions,
Routing/Gates, and Revision History.

`confirmed` requires unique IDs, valid references, zero unresolved conflicts, zero
open decisions, and at least one AC per REQ. `implemented` additionally requires
actual PASS evidence for every AC and a passing code-review Spec axis with no missing,
incorrect, or scope-creep behavior.

A confirmed unimplemented spec reopens in place before a possible contract-changing
question. On reconfirmation, compare a normalized contract hash that excludes
lifecycle metadata and revision history. No actual contract delta restores
`confirmed` and retains the prior execution authorization; any actual delta
invalidates it and requires a new exact `開始執行`. An implemented spec never reopens;
create a related `refines` or `supersedes` change set instead.

## Resolution and delivery

Resolve in order: user-explicit canonical path, tracker canonical path, branch match,
then the repository's unique confirmed spec. Multiple candidates are `BLOCKED`; never
choose the latest. An implemented spec is not an active fallback.

The local spec is authoritative. Publish its complete snapshot to the tracker with
the local path. If publication fails after local materialization, keep the file and
report `BLOCKED: tracker publication pending`; retry publication by spec ID without
rewriting the canonical document.

At commit preparation, a tracked or staged `.codex/spec-governance/**` path is
`BLOCKED`. Even when the bundle is untracked, ask exactly one disposition question:
delete it, keep it local, or archive only the normalized journal to
`specs/history/`. Do not auto-delete, auto-archive, stage, commit, or alter ignore
policy.
