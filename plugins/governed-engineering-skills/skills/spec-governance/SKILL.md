---
name: spec-governance
description: Reconcile, materialize, resolve, and verify the canonical repository specification for every modifying engineering change set. Model-invoked by ask-matt and delivery workflows.
---

# Spec governance

Own one canonical change-set contract from discussion through verified implementation.

## Public interfaces

- `spec-governance.reconcile`: classify each new statement as a domain term,
  change-set contract, ADR candidate, or open decision; preserve stable IDs and show
  the Spec delta, affected IDs, relationships, conflicts, open decisions, and
  `PASS/BLOCKED` verdict after every answer.
- `spec-governance.materialize`: only after the user explicitly says
  `開始執行`, write `specs/SPEC-####-<feature-slug>.md` using the next repository-wide
  four-digit number. Never write repository files while the spec is merely working.
- `spec-governance.verify`: resolve the active spec, validate structure and
  REQ → AC → validation seams, and return `PASS` or `BLOCKED` before TDD or
  implementation.

Use `scripts/spec_contract.py validate --spec <path>` for the strict Markdown
contract and `resolve --project-root <root> --prompt <request> --branch <branch>` for
deterministic active-spec resolution.

## Reconcile loop

After each user answer:

1. Update the in-conversation working spec and reuse unchanged REQ, DEC, and AC IDs.
2. Compare it with non-empty `CONTEXT.md`, accepted ADRs, and the architecture
   manifest.
3. Render the Spec delta, affected IDs, explicit relations, conflicts, open
   decisions, and consistency verdict.
4. When blocked, ask exactly one conclusion-changing question.
5. When complete, render the full proposed spec and intended repository diff, then
   wait for exact authorization.

Route domain vocabulary to `CONTEXT.md`, change-set requirements and acceptance to the
canonical spec, qualifying architectural decisions to a **proposed** ADR, and
unconfirmed content only to the working spec. These outputs, tests, generated views,
and implementation are one change set; do not recursively start another interview.

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

## Resolution and delivery

Resolve in order: user-explicit canonical path, tracker canonical path, branch match,
then the repository's unique confirmed spec. Multiple candidates are `BLOCKED`; never
choose the latest. An implemented spec is not an active fallback.

The local spec is authoritative. Publish its complete snapshot to the tracker with
the local path. If publication fails after local materialization, keep the file and
report `BLOCKED: tracker publication pending`; retry publication by spec ID without
rewriting the canonical document.
