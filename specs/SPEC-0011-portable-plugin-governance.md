---
spec_version: 1
spec_id: SPEC-0011
revision: 1
status: implemented
change_set: portable-plugin-governance
---

# Portable plugin governance

## Problem

SPEC-0010 originally required a user-global `AGENTS.md` to repeat the plugin's
authorization boundary. That file is machine-local, is not installed with the
plugin, and therefore cannot make behavior portable to another computer.

## Solution

Keep the complete authorization and specification-lifecycle contract inside the
plugin manifest and bundled skills. Disable the current machine's global
`AGENTS.md` recoverably and forbid governed workflows from requiring or modifying a
user-global policy file.

## User Stories

- As a developer installing the plugin on another computer, I receive the same
  grilling and authorization behavior without copying machine-local instructions.
- As the current user, I can restore the former global file if unrelated personal
  rules are needed later.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The installed plugin MUST fully define the working-bundle, canonical-spec and product-authorization boundaries in bundled contracts. |
| REQ-002 | Governed workflows MUST NOT require, create, edit or depend on a user-global `AGENTS.md` to enforce those boundaries. |
| REQ-003 | The current global `AGENTS.md` MUST be disabled without overwriting an existing backup and MUST remain recoverable. |
| REQ-004 | Plugin validation and contract tests MUST prove the portable policy is present after installation. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Treat plugin-bundled contracts as the only portable governance authority. |
| DEC-002 | Rename the current global file to `AGENTS.md.disabled` instead of permanently deleting it. |
| DEC-003 | Preserve SPEC-0010 as implemented history and record this portability correction as a related change set. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-004 | Plugin manifest, `ask-matt` and the shared decision contract state both authorization layers and explicitly reject a user-global dependency. | Contract tests and plugin validation. | PASS: bundled contract assertions and plugin validation. |
| AC-002 | REQ-003 | `C:\Users\hugo_peng\.codex\AGENTS.md` is absent while `AGENTS.md.disabled` exists, with no overwrite. | Read-only filesystem inspection after the guarded rename. | PASS: active path false; disabled path true. |
| AC-003 | REQ-001, REQ-004 | Existing persistent lifecycle behavior remains green after the portability correction. | Focused and integration regression validation. | PASS: focused contract suite and integration validator. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| SPEC-0011 | refines | SPEC-0010 |
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-002 |
| REQ-004 | depends_on | DEC-003 |

## Out of Scope

- Deleting the recoverable `AGENTS.md.disabled` backup.
- Creating or modifying global policy files on other computers.
- Changing unrelated project-local `AGENTS.md` files.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user chose plugin self-containment and recoverable global
  disablement.
- Spec reconciliation: PASS — the change refines implemented SPEC-0010 without
  reopening it.
- Architecture impact: none — ownership and runtime interfaces are unchanged.
- Spec review: PASS — bundled policy, filesystem state and validation evidence
  satisfy every requirement without scope creep.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-07 | Recorded and implemented portable plugin governance. |
