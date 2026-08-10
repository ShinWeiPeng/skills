# ADR-0012: Schema 2.2 localized, function-first Description Views

- Status: proposed
- Date: 2026-08-05
- Supersedes: none

## Context and problem

Schema 2.1.0 generates complete Architecture Description Views, but the root page
leads with technical catalogs and Mermaid nodes expose only module IDs and levels.
Readers cannot quickly discover the system's main functions, related Flows, or the
protection rationale already present in module invariants and errors. A renderer
cannot safely translate English `description.purpose` text without introducing
non-determinism and an unverifiable fallback policy.

## Proposed decision

Add an exact Standard/Schema 2.2.0 pair while retaining exact 2.1.0 support.
Schema 2.2.0 adds optional `project.diagram_language` and locale-keyed
`module.description.diagram_summaries`. When a diagram language is selected, every
diagram-visible module must provide a non-empty value for that exact locale.
Renderers never translate, fall back, or mix languages.

For 2.2 projects, put system purpose and entrypoints, an L0-L2 main-function tree,
and per-function responsibility, children, related Flows, invariants, and error
handling before the complete technical reference. L3+ modules remain in the complete
System diagram, applicable Flows, and catalogs. Flowchart nodes and sequence
participants show formal module IDs plus localized summaries; actions, prose,
tables, filenames, and anchors remain controlled by `documentation_language`.

Bootstrap new projects at 2.2.0. Existing 2.1.0 projects keep their validation and
byte-for-byte rendered behavior and are not automatically migrated.

## Alternatives considered

- A separate localization catalog keeps 2.1.0 unchanged but creates a second source
  that can drift from module IDs.
- Combining languages in `description.purpose` avoids a field but pollutes prose and
  requires delimiter parsing.
- Hard-coded renderer translations couple generic tooling to particular projects.
- Translating only relationship labels does not explain module purpose.

## Benefits, costs, and risks

The proposal makes the first architecture page function-oriented and gives every
diagram a validated Traditional Chinese orientation layer without changing formal
English contracts. Costs include a dual-version checker, renderer and bootstrap
updates, localized summary maintenance, and a compatible MINOR prerelease. The main
risk is incomplete localization; exact-locale validation fails closed before
rendering.

## Compatibility and migration impact

The change is compatible for existing 2.1.0 projects and adds a new 2.2.0 contract.
Standard and Schema versions must match exactly. No runtime Port, Event, dependency,
Type, State, execution, scheduling, or product algorithm behavior changes.

## Validation and observable pass conditions

- Existing 2.1.0 fixtures validate and render byte for byte as before.
- Valid 2.2.0 manifests pass; mismatched versions and missing, blank, or malformed
  localized summaries fail closed.
- 2.2 flowcharts and sequence participants contain exact locale summaries while
  Flow actions and English documentation remain unchanged.
- L0-L2 functions lead the root guide; L3+ stays in complete technical views.
- Bootstrap defaults unspecified versions to 2.2.0.
- Repeated renders are deterministic and checked-in views pass stale comparison.

## Approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
