---
spec_version: 1
spec_id: SPEC-0005
revision: 2
status: implemented
change_set: function-first-architecture-description
---

# Function-first architecture description with localized diagram summaries

## Problem

The generated Architecture Description Views are technically complete but lead with
catalog-oriented detail, so a reader cannot quickly understand the system's main
functions, subfunctions, related Flows, or why protective behavior exists. Mermaid
module labels identify modules but do not explain their purpose in the reader's
preferred diagram language. The current exact Standard/Schema 2.1.0 contract has no
structured source for localized diagram summaries.

## Solution

Add an exact, backward-compatible Standard/Schema 2.2.0 contract alongside retained
2.1.0 support. Schema 2.2.0 separates `project.diagram_language` from
`documentation_language` and adds locale-keyed
`module.description.diagram_summaries`. Reorganize generated Description Views so
the root page first explains purpose, entrypoints, the L0-L2 main-function tree,
function responsibilities, related Flows, and nearby invariants/error-handling
rationale before retaining the complete technical reference. Use localized module
summaries in both flowchart nodes and sequence participants while keeping formal IDs,
Flow actions, prose, headings, and tables in the documentation language.

## User Stories

- As a new reader, I can start from the system's main functions and navigate to
  subfunctions and Flows before reading the full technical catalog.
- As a Traditional Chinese reader of an English architecture document, I can identify
  every diagram-visible module's purpose from a concise `zh-TW` summary without
  changing formal IDs or English Flow actions.
- As a maintainer of an existing 2.1 project, I can continue validating and rendering
  it without migration or output changes.
- As a governance maintainer, I can detect missing, blank, or invalid localized
  summaries instead of relying on renderer translation or fallback behavior.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The public architecture tooling MUST accept exact matching Standard/Schema 2.1.0 and 2.2.0 manifests, MUST reject mismatched or unsupported versions, and MUST preserve 2.1.0 validation and rendered output behavior. |
| REQ-002 | Schema 2.2.0 MUST support optional `project.diagram_language` and optional locale-keyed `module.description.diagram_summaries`; when `diagram_language` is specified, every diagram-visible module MUST provide a non-blank summary for that exact locale. |
| REQ-003 | The checker MUST reject missing, blank, malformed, or unknown-module localized summary data and MUST NOT permit renderer translation, locale fallback, or mixed-language substitution. |
| REQ-004 | The generated root Description View MUST present system purpose and entrypoints, an L0-L2 main-function tree, function responsibilities/children/related Flows, and adjacent invariant/error-handling rationale before the retained complete technical reference and navigation. |
| REQ-005 | L3+ modules MUST be excluded from the main-function tree but MUST remain present in the complete System diagram, applicable Flows, navigation, and technical catalogs. |
| REQ-006 | In 2.2 manifests with a diagram language, System/Parent flowchart nodes and Flow sequence participants MUST show formal English module IDs, levels where applicable, and localized purpose summaries; Flow arrows, ordered steps, headings, prose, tables, filenames, and anchors MUST remain governed by the documentation language and existing compatibility rules. |
| REQ-007 | The renderer MUST emit every Flow in manifest order, derive protective rationale only from existing manifest invariants/errors, preserve existing filenames/section anchors/Flow anchors/links/catalogs, and render both 2.1 and 2.2 deterministically byte for byte. |
| REQ-008 | Bootstrap MUST create new projects at exact Standard/Schema 2.2.0 while existing 2.1 projects remain supported and are not automatically migrated. |
| REQ-009 | Canonical tools, mirrored skill tools, schema/checker/renderer/bootstrap assets, manifest-schema and Description Views references, architecture governance rules, and `explain-code-flow` capability guidance MUST describe the dual-version behavior consistently. |
| REQ-010 | The plugin and architecture-governance manifests MUST migrate to 2.2.0 with `documentation_language: en`, `diagram_language: zh-TW`, and non-blank `zh-TW` summaries for every diagram-visible module; checked-in Description Views MUST be regenerated from the manifests. |
| REQ-011 | The change set MUST include a proposed ADR for dual-version support and language separation plus a MINOR changeset with high-risk beta release intent, without accepting the ADR, promoting a version, publishing, committing, or pushing. |
| REQ-012 | The change MUST NOT alter runtime Ports, Events, dependencies, execution units, product algorithms, or runtime behavior; algorithm screening and runtime/on-device validation are not applicable. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use structured locale-keyed summaries inside each module description rather than an external localization catalog, mixed-language purpose string, or renderer hard-coding. |
| DEC-002 | Advance Standard and Schema together to 2.2.0 and keep exact 2.1.0 support because the added display metadata is backward compatible. |
| DEC-003 | Keep `documentation_language` and `diagram_language` independent; this project uses English documentation and Traditional Chinese (`zh-TW`) diagram summaries. |
| DEC-004 | Require an exact localized summary whenever `diagram_language` is set and prohibit automatic translation or fallback. |
| DEC-005 | Apply localized summaries to both flowchart module nodes and sequence participants while leaving Flow action labels and all non-diagram content in English for this project. |
| DEC-006 | Include only L0-L2 modules in the main-function tree and retain L3+ modules in complete technical views. |
| DEC-007 | Reuse existing invariants and errors as protection rationale; do not add a separate structured `protections` model. |
| DEC-008 | Treat the change as a high-risk compatible MINOR beta intent; version promotion remains a separate authorized workflow. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003 | 2.1 fixtures still pass unchanged; valid 2.2 fixtures pass; version mismatches and missing/blank/unknown localized summaries fail closed. | Focused schema/checker unit tests covering exact versions and summary validation. | PASS — schema/checker tests cover valid 2.2, exact 2.1 compatibility, version mismatch, and missing/blank/malformed summaries. |
| AC-002 | REQ-004, REQ-005 | The root view begins with purpose/entrypoints and an L0-L2 function tree with responsibility, children, Flows, invariants, and error rationale; L3+ remains in complete views only. | Renderer fixture tests plus generated root-view inspection. | PASS — renderer contract test and manual generated-root inspection confirm the function-first order and L3+ exclusion from only the main-function tree. |
| AC-003 | REQ-006, REQ-007 | Flowcharts and sequence participants include `zh-TW` summaries; arrows and document text remain English; all Flows preserve manifest order; existing anchors/catalogs remain; repeated renders are identical for 2.1 and 2.2. | Renderer golden/contract tests, link/anchor assertions, and repeated in-memory render comparison. | PASS — renderer tests and manual Flow inspection confirm localized nodes/participants, English actions, stable order, anchors, catalogs, and deterministic output. |
| AC-004 | REQ-008, REQ-009 | Bootstrap emits 2.2 projects and all canonical/mirrored tools and governance references consistently support exact 2.1/2.2 behavior. | Bootstrap fixture tests, mirror consistency/integration tests, and text contract assertions. | PASS — bootstrap defaults to 2.2, 2.1 remains explicit-compatible, all governed tool mirrors are hash-identical, and explain-code-flow contract tests pass. |
| AC-005 | REQ-010 | Both formal manifests validate at 2.2 with complete `zh-TW` summaries, and all checked-in views match deterministic renderer output. | Architecture render checks, generated-view stale comparison, development gate, and manual inspection of root/Parent/Flow diagrams. | PASS — plugin and skill development gates report VERIFIED; generated-view stale checks and manual root/Parent/Flow inspection pass. |
| AC-006 | REQ-011 | A proposed ADR and MINOR changeset with high-risk beta intent exist; version governance passes without package/plugin version promotion or external publication. | ADR/changeset inspection, version-governance check, and git diff review. | PASS — ADR-0012 remains proposed, the MINOR/high-risk beta release intent exists, version governance passes, and no promotion or publication occurred. |
| AC-007 | REQ-012 | No runtime contract, dependency, execution, or algorithm behavior changes appear in the manifest or implementation diff. | Architecture diff review, algorithm screening, and two-axis Standards/Spec code review. | PASS — architecture diff and algorithm screening find documentation-governance-only behavior; Standards and Spec reviews both pass with 0 findings. |
| AC-008 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012 | Architecture unit tests, bootstrap fixtures, plugin integration, version governance, one development gate, and final Standards/Spec reviews all pass with no uncovered requirement or scope creep. | Complete automated validation and final traceability review. | PASS — 104 governance-skill tests, 13 explain-code-flow tests, 134 plugin tests, both development gates, integration, version, vendor, mirror, Standards, and Spec checks pass. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-002 |
| REQ-002 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-003 |
| REQ-003 | depends_on | DEC-004 |
| REQ-004 | depends_on | DEC-006 |
| REQ-005 | refines | REQ-004 |
| REQ-006 | depends_on | DEC-005 |
| REQ-007 | depends_on | DEC-007 |
| REQ-008 | depends_on | DEC-002 |
| REQ-009 | refines | REQ-001 |
| REQ-010 | depends_on | DEC-003 |
| REQ-011 | depends_on | DEC-008 |
| REQ-012 | depends_on | DEC-007 |

## Out of Scope

- Automatically translating manifest text or providing locale fallback.
- Localizing formal module IDs, Flow action labels, headings, prose, or tables.
- Adding structured protection records beyond existing invariants and errors.
- Migrating third-party or unrelated governed projects from 2.1 to 2.2.
- Changing runtime modules, Ports, Events, dependencies, execution profiles, source
  ownership, scheduling, product algorithms, or device behavior.
- Accepting the proposed ADR, promoting a plugin version, publishing a release,
  committing, pushing, or opening a pull request.
- Repairing unrelated pre-existing failures.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the referenced Codex task confirmed localization source, language
  boundary, exact-version compatibility, navigation order, Flow coverage, release
  intent, and validation scope.
- Spec verification: PASS — the canonical specification validates with complete
  requirement, decision, acceptance, and relationship traceability.
- Architecture authoring: PASS for planned impact — responsibility and observable
  behavior are documentation-governance only; existing runtime Flows, boundaries,
  Types, State, dependency edges, parent mappings, scheduling, and source ownership
  remain unchanged. The manifest design gate will run before final implementation
  validation.
- Flow review: PASS — no end-to-end runtime Flow or execution path changes; the
  renderer displays existing manifest Flows in their declared order.
- Algorithm screening: Not applicable — the change selects and presents existing
  architecture metadata and does not alter a product result or algorithm.
- Type Ownership Matrix: Unchanged — no named production type or field changes.
- State Object Ownership Matrix: Unchanged — no runtime state changes.
- Boundary Design Table: Unchanged — no Port, Event, mapping, or dependency changes.
- Runtime validation: Not applicable — no runtime or device behavior changes.
- TDD: Required at schema/checker/renderer/bootstrap compatibility seams.
- Code review Standards axis: PASS — 0 documented-standard violations and 0
  actionable baseline smells.
- Code review Spec axis: PASS — 0 uncovered requirements, acceptance gaps, scope
  creep findings, or incorrect implementations.
- Spec review: PASS — all acceptance criteria contain PASS evidence and the
  implemented change set remains within SPEC-0005.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-05 | Materialized the authorized function-first Description Views and localized diagram summary plan from Codex task `019fcfa5-d489-7f70-8ec4-583d4f23f7ea`. |
| 2 | 2026-08-05 | Recorded completed implementation, automated validation, architecture gates, and two-axis review evidence. |
