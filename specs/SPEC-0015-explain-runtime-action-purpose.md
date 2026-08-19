---
spec_version: 1
spec_id: SPEC-0015
revision: 3
status: implemented
change_set: explain-runtime-action-purpose
---

# Explain runtime action purpose

## Problem

During an active `validate-on-device` scenario, the reporting contract permits only
the current action, completion signal, and timeout. This keeps interaction concise,
but it can leave the user unable to tell why a command is necessary, how its output
will be used, or which failure the action is intended to prevent. Restating the
command's immediate mechanism, such as “check UID/GID,” does not supply that
higher-level reason.

## Solution

Add `action purpose` to the minimal during-operation reporting contract. Require one
concise explanation of the downstream decision, configuration, evidence claim, or
risk that the current action supports. The purpose must not merely paraphrase the
action. Keep the pre-test brief single-shot and retain the existing current action,
completion signal, timeout, safety, evidence, and verdict boundaries.

## User Stories

- As a user asked to run a bounded command, I understand why the information is
  needed before deciding whether and how to proceed.
- As a user supplying command output, I understand how the result will affect the
  next configuration or validation decision.
- As a plugin maintainer, I can detect regressions that omit the purpose or replace
  it with a circular restatement of the action.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | During every guided or Codex-operated runtime action, `validate-on-device` MUST present exactly the minimal fields `執行目的`, `目前動作`, `完成訊號`, and `逾時`. |
| REQ-002 | `執行目的` MUST explain the higher-level downstream use of the action's result and the relevant failure, uncertainty, or unsafe workaround it prevents; it MUST NOT merely paraphrase the command or observation. |
| REQ-003 | The added purpose MUST remain concise and MUST NOT repeat the complete pre-test brief, criteria table, expected flow, or risk section on each operation turn. |
| REQ-004 | Existing safety approval, bounded execution, user-output, evidence-authority, and PASS/FAIL/BLOCKED verdict contracts MUST remain unchanged. |
| REQ-005 | The authoritative skill, user-facing reporting reference, focused contract tests, and promoted human-facing docs page MUST describe the behavior consistently. |
| REQ-006 | The change MUST include repository-required release metadata for a compatible user-visible skill behavior change, without publishing or performing external release actions. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Scope the change to `validate-on-device`; do not create a global execution-message contract for unrelated engineering skills. |
| DEC-002 | Add `執行目的` as the first field in the existing minimal during-operation block. |
| DEC-003 | Define a valid purpose by its downstream use and prevented failure or uncertainty, not by the command's immediate mechanism. |
| DEC-004 | Preserve the one-time pre-test brief and all existing execution, safety, evidence, and verdict semantics. |
| DEC-005 | Validate the behavior through contract-text assertions and representative good/bad examples rather than adding runtime rendering code that the skill does not currently own. |
| DEC-006 | Treat the behavior change as compatible and include the release metadata required by the repository's current version-governance policy; do not publish it in this change set. |

## Discussion Context

### DISC-001: Required explanation depth

- **Situation:** The existing runtime message names the command and expected output but does not explain why the information is needed.
- **Question:** What additional context should the operation message provide?
- **Options and tradeoffs:** Restating the immediate check is shorter but circular; explaining the downstream use and prevented failure adds one concise line and makes the action intelligible.
- **User answer:** `也想了解在上一層的原因，為什麼需要確認這些東西`
- **Explicit rationale:** The purpose should explain why the checked values matter to the service, such as configuring mounted-directory ownership so PostgreSQL can start safely.
- **Resulting impact:** REQ-001, REQ-002, DEC-002, DEC-003, AC-001, AC-002.

### DISC-002: Confirmed wording direction

- **Situation:** A candidate purpose connected UID/GID discovery to Linux bind-mount permissions, startup failure, and avoiding overly broad permissions.
- **Question:** Does that higher-level explanation match the desired behavior?
- **Options and tradeoffs:** Keep the concise higher-level explanation or retain the existing mechanism-only message.
- **User answer:** `這是我想要的`
- **Explicit rationale:** The candidate explicitly connected the action to its downstream configuration and operational risk.
- **Resulting impact:** DEC-001, DEC-003, DEC-004 and the acceptance boundary for all requirements.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-003 | Both authoritative runtime-reporting contracts require the four ordered fields and still prohibit repeating the full brief during operation. | Focused text-contract test plus manual rendered-example inspection. | PASS — the focused test verifies all four labels in order and the reference retains the one-time brief boundary; the representative Markdown example was inspected. |
| AC-002 | REQ-002 | The contract defines purpose as downstream use plus prevented failure/uncertainty and rejects a circular restatement. | Focused positive and negative contract assertions over the skill/reference text. | PASS — RED first proved the contract absent; GREEN verifies downstream use, prevented failure/uncertainty/unsafe workaround, anti-paraphrase wording, and representative good/bad content in both authoritative contracts. |
| AC-003 | REQ-004 | Existing safety, bounded execution, evidence authority, and verdict wording remains present and no permission or authorization boundary changes. | Existing `validate-on-device` test suite plus structured diff review. | PASS — all 68 `validate-on-device` tests pass and final diff review confirms the safety, bounded execution, evidence, permission, and verdict boundaries are unchanged. |
| AC-004 | REQ-005 | `SKILL.md`, `references/user-facing-reporting.md`, focused tests, and `docs/engineering/validate-on-device.md` consistently explain the new field and rationale. | File inventory check, focused tests, and documentation checklist from `.agents/writing-docs.md`. | PASS — the four required paths are synchronized, the focused test passes, and Standards review reports zero documentation violations or smells. |
| AC-005 | REQ-006 | Required compatible-change release metadata validates without package publication or remote mutation. | Repository version-governance validation and Git diff inspection. | PASS — 24 version-governance tests and repository version check pass; a minor changeset plus matching release intent predicts `0.9.0`, and no publication or remote mutation occurred. |
| AC-006 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 | Standards and Spec reviews find no omitted requirement, conflicting instruction, incorrect behavior, or scope creep. | Two-axis code review after implementation. | PASS — Standards reports zero findings; Spec traceability reports no uncovered REQs, unverified ACs, incorrect behavior, or scope creep. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-002 |
| REQ-002 | depends_on | DEC-003 |
| REQ-003 | depends_on | DEC-004 |
| REQ-004 | depends_on | DEC-004 |
| REQ-005 | depends_on | DEC-005 |
| REQ-006 | depends_on | DEC-006 |

## Out of Scope

- Changing runtime actions, commands, timeouts, completion conditions, or evidence
  collection behavior.
- Changing profile schemas or requiring new scenario metadata.
- Adding the four-field contract to unrelated engineering skills.
- Changing native permission prompts or exact repository execution authorization.
- Publishing a package, tag, pull request, Marketplace update, or remote release.
- Treating an explanatory purpose as evidence or allowing it to affect the runner
  verdict.

## Open Decisions

None.

## Routing/Gates

- Improvement proposal: PASS — repository evidence and prior conversation confirm
  the problem, target skill, desired explanation depth, and compatibility boundary.
- Grilling: PASS — prior user confirmation selects a higher-level purpose that
  explains downstream use and prevented failure; no unresolved design decision
  remains.
- Spec verification: PASS — canonical structure and REQ-to-AC traceability validate with no uncovered requirement or acceptance criterion.
- Architecture authoring: Not applicable — no module, dependency, Port, Event,
  callback, data-flow, execution-context, schema, or generated Description View
  contract changes.
- Algorithm screening: Not applicable — this is presentation text and does not
  select a data-dependent method or change observable product computation.
- Runtime validation: Not applicable — the change affects instructions and docs,
  not device or operating-system behavior.
- TDD: PASS — the focused contract test recorded RED before the behavior text changed, then GREEN; the complete 68-test skill suite passes.
- Standards review: PASS — zero documented-standard violations and zero baseline smells.
- Spec review: PASS — zero uncovered REQs, unverified ACs, incorrect behavior, or scope creep.
- Distribution validation: PASS — the 274-file Plugin candidate assembles at formal version `0.8.2`; assembly validation, distribution validation, and version governance all pass.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-19 | Confirmed the proposal scope and acceptance contract from repository evidence and user feedback. |
| 3 | 2026-08-19 | Recorded implementation, TDD, distribution, version-governance, and two-axis review PASS evidence; marked the change set implemented. |
