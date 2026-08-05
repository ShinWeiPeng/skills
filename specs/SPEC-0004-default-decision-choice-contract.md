---
spec_version: 1
spec_id: SPEC-0004
revision: 2
status: implemented
change_set: default-decision-choice-contract
---

# Default decision choice contract

## Problem

Governed engineering skills do not apply one consistent interaction contract when
they ask a user to make a design or specification decision. Some workflows use a
structured choice tool in Plan mode, while `clarify-improvement-proposals` and
`govern-modular-event-architecture` explicitly stop when that tool is unavailable.
As a result, Default mode may omit meaningful options or require a mode switch even
though the same decision can be presented safely as numbered text.

## Solution

Define one shared Decision Question Contract inherited by every governed engineering
workflow. Each design or specification decision is asked one at a time with two or
three meaningful, mutually exclusive authored options, complete context and
tradeoffs, and an evidence-backed recommendation when available. Prefer the
structured choice tool, but use semantically equivalent numbered text when the tool
is unavailable. Preserve free-form answers and keep repository execution
authorization and native permission dialogs outside this presentation contract.

## User Stories

- As a user working in Default mode, I receive concrete options instead of being
  told to switch modes solely because choice buttons are unavailable.
- As a user making an engineering decision, I understand each option's observable
  result, benefits, disadvantages, risks, costs, constraints, and downstream impact.
- As a user whose preferred answer was not anticipated, I can provide a free-form or
  combined answer without being forced into an incomplete list.
- As a plugin maintainer, I can detect conflicting skill instructions and verify
  that authorization boundaries remain unchanged.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Every governed engineering question that asks the user to choose a design or specification outcome MUST present exactly two or three meaningful, mutually exclusive authored options. |
| REQ-002 | Before presenting options, the workflow MUST explain the current situation, why the decision is needed, and what later behavior or work it affects. Every option MUST state its observable result, main benefits, disadvantages and risks, costs or constraints, downstream consequences, and suitable and unsuitable conditions. |
| REQ-003 | The workflow MUST recommend an option only when evidence supports it and MUST explain the reason; otherwise it MUST remain neutral and state the missing evidence. |
| REQ-004 | The workflow MUST prefer an available structured choice tool and MUST fall back to semantically equivalent numbered text when it is unavailable. Missing structured UI alone MUST NOT stop the workflow or require a switch to Plan mode. |
| REQ-005 | The workflow MUST ask one decision question at a time, reconcile the answer before asking the next question, and accept free-form, combined, or premise-correcting answers. Tool-provided free-form UI does not count as an authored option. |
| REQ-006 | The exact `開始執行` repository authorization and native system permission dialogs MUST retain their existing behavior and remain outside the Decision Question Contract. |
| REQ-007 | The plugin architecture manifest, generated Description Views, contract tests, integration metadata, and release metadata MUST describe and validate the behavior consistently without changing a public CLI, JSON Schema, routing result, manifest schema, runtime architecture, or installed skill inventory. |
| REQ-008 | The compatible behavior addition MUST include a minor changeset and beta release intent in the existing `0.5.0` prerelease group without directly promoting or publishing a release. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Apply the contract to all governed engineering design and specification decisions, not only architecture choices or grilling sessions. |
| DEC-002 | Use structured choices when available and numbered text as the mandatory fallback. |
| DEC-003 | Preserve free-form answers rather than restricting the user to the authored options. |
| DEC-004 | Ask one decision at a time, even when a structured tool can batch multiple questions. |
| DEC-005 | Exclude exact execution authorization and native permission dialogs from the new presentation contract. |
| DEC-006 | Make `ask-matt` the shared entry contract, reinforce it in interactive interview skills, and remove contradictory stop rules from proposal and architecture workflows. |
| DEC-007 | Record the behavior as a compatible minor beta change; no ADR or Algorithm Design Record is required because no architecture boundary, runtime flow, public data contract, or product algorithm changes. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003 | The shared entry and interview skills require two or three options, complete decision context and tradeoffs, and evidence-backed recommendation behavior. | Focused skill-contract tests and text inspection. | PASS — five Decision Question Contract tests verify the shared entry, interview wrappers, complete option analysis, and plugin entry metadata. |
| AC-002 | REQ-004 | Proposal and architecture workflows use structured choices when available and numbered text otherwise, with no tool-absence stop or forced Plan-mode switch. | Focused regression tests scanning public skill contracts. | PASS — the focused regression rejects the former Markdown/Plan stop instructions and verifies numbered-text fallback in both workflows. |
| AC-003 | REQ-005 | Interactive workflows ask one decision at a time and explicitly accept free-form, combined, and premise-correcting answers. | Focused skill-contract tests. | PASS — shared and wrapper contracts require one-at-a-time decisions and preserve free-form, combined, and premise-correcting responses. |
| AC-004 | REQ-006 | Existing exact `開始執行` authorization and native permission behavior remain present and are explicitly excluded from the new contract. | Contract assertions and diff review. | PASS — contract assertions preserve `開始執行`, exclude native permission prompts, and diff review found no authorization implementation change. |
| AC-005 | REQ-007 | Manifest and generated views are current and deterministic; guided routing, plugin integration, architecture development gate, and version governance pass without new public schema or skill inventory. | Automated test suites, render check, architecture gate, and diff inspection. | PASS — 134 plugin tests passed; integration reports 28 skills with consistent metadata and no user paths; the development gate reports `PASS: VERIFIED`; vendor and version checks pass; generated views match the manifest. |
| AC-006 | REQ-008 | A minor changeset and beta intent validate inside the current prerelease group without a package-version edit or external publication. | Version-governance check and next-version inspection. | PASS — version governance passes, predicts `0.5.0-beta.5`, and package/plugin versions remain `0.5.0-beta.4` pending the Version workflow. |
| AC-007 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008 | Standards and Spec reviews find no uncovered requirement, conflicting instruction, incorrect behavior, or scope creep. | Two-axis code review after implementation. | PASS — Standards and Spec axes each report zero findings; Spec traceability has no uncovered REQ, unverified AC, scope creep, or incorrect behavior. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | refines | REQ-001 |
| REQ-003 | refines | REQ-001 |
| REQ-004 | depends_on | DEC-002 |
| REQ-005 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-004 |
| REQ-006 | depends_on | DEC-005 |
| REQ-007 | depends_on | DEC-006 |
| REQ-008 | depends_on | DEC-007 |

## Out of Scope

- Requiring structured choice buttons in a host that does not expose them.
- Changing the exact repository execution authorization phrase or approval boundary.
- Adding a second confirmation before a native system permission dialog.
- Applying the contract to non-engineering conversations outside this plugin.
- Changing routing algorithms, architecture schema, runtime behavior, or product code.
- Publishing a tag, pull request, marketplace update, or remote release.
- Repairing unrelated pre-existing test failures.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — scope, fallback, free-form handling, cadence, and authorization
  exclusions are confirmed.
- Spec verification: PASS — revisions 1 and 2 have complete REQ-to-AC
  traceability with no conflict, open decision, or scope creep.
- Architecture authoring: Not applicable to runtime boundaries; the existing
  `automatic_engineering_router` module description and generated views will be
  updated and checked as documentation-governance evidence.
- Algorithm screening: Not applicable — this is a prompt presentation contract and
  does not alter a product result or algorithm.
- TDD: PASS — five focused contract tests recorded RED before the shared contract
  and metadata changes, then GREEN; the complete plugin suite passed 134 tests.
- Code review Standards axis: PASS — zero documented-standard violations or
  actionable baseline smells.
- Code review Spec axis: PASS — zero uncovered requirements, unverified acceptance
  criteria, scope creep, conflicting behavior, or incorrect implementation.
- Spec review: PASS — the final SpecTraceabilityAssessment reports no uncovered
  REQ IDs, partial requirements, unverified AC IDs, or scope creep.
- Runtime validation: Not applicable.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-05 | Materialized the authorized Default decision choice contract. |
| 2 | 2026-08-05 | Recorded passing implementation, integration, architecture, version, vendor, TDD, and two-axis review evidence; marked the change set implemented. |
