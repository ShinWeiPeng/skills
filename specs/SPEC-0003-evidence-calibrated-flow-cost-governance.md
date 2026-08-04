---
spec_version: 1
spec_id: SPEC-0003
revision: 2
status: implemented
change_set: evidence-calibrated-flow-cost-governance
---

# Evidence-calibrated flow cost governance

## Problem

Architecture-improvement workflows inspect modules, interfaces, ownership, and
dependency direction but do not consistently challenge inherited data flows or
prove execution-cost claims. A proposal can therefore preserve an unsafe or slow
flow, estimate stack or timing from incomplete call paths, and describe a design as
faster, maintainable, extensible, or real-time-ready without calibrated evidence.
The Register domain's synchronous `Execute -> Publish -> callback -> Execute`
re-entry and task-stack overflow is the motivating regression scenario.

## Solution

Add one shared evidence-calibrated Flow Review contract and apply it through the
existing architecture-improvement, proposal-clarification, modular-architecture,
and runtime-validation workflows. Evaluate every material flow through functional
admission, execution and real-time feasibility, maintainability and extensibility,
and model assurance. Distinguish estimates from calibrated measurements and
validated claims, require tiered evidence proportional to timing and resource risk,
and fail closed when a load-bearing assumption, path, platform fact, unit, budget,
or evidence window is unresolved.

## User Stories

- As a maintainer improving an existing system, I can compare the as-is flow and
  structurally different target flows using execution evidence and concrete change
  scenarios rather than preserving the existing orchestration by default.
- As a Greenfield designer, I discuss end-to-end data flow and portable cost
  estimates before fixing Modules, Ports, Events, Tasks, or Queues.
- As a real-time engineer, I receive deadline, WCET, jitter, blocking, interference,
  and end-to-end response evidence rather than average-only performance claims.
- As a firmware maintainer, I can distinguish a provisional stack estimate from a
  release-equivalent, target-calibrated stack acceptance result.
- As a plugin maintainer, I can regression-test the Flow Review contract and release
  it without adding a new skill, manifest schema, or public CLI.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The plugin MUST define one shared Flow Review contract with four ordered dimensions: functional admission, execution cost and real-time feasibility, maintainability and extensibility, and model assurance. |
| REQ-002 | Every material cost model MUST report one of `estimated`, `calibrated`, `validated`, or `BLOCKED` and MUST record predicted and observed values when available, prediction error, scenario coverage, uncovered risks, reserve source, evidence references, build composition, and platform/toolchain assumptions. |
| REQ-003 | Existing-project reviews MUST reconstruct an evidence-backed as-is Flow and production-equivalent baseline before recommending a target; Greenfield reviews MUST discuss end-to-end Flow and portable cost candidates before finalizing Modules, Ports, Events, Tasks, Queues, or platform-specific execution decisions. |
| REQ-004 | A Flow-affecting proposal MUST compare at least two structurally different candidates after functional admission, use constraint filtering followed by Pareto comparison, and MUST NOT treat external compatibility as a requirement to preserve internal orchestration. A local change with no Flow impact MAY report `N/A` only with a specific reason. |
| REQ-005 | Tiered evidence MUST apply: every Flow receives a static cost model; hard/soft real-time Flows require the existing scheduling study and quantitative runtime acceptance; best-effort Flows require a benchmark when budgets, high frequency or bursts, large payload or fan-out, new execution hops or synchronization, unbounded resources, constrained platform resources, or material model uncertainty can change the recommendation. |
| REQ-006 | Stack models MUST bind target, ABI, RTOS/framework version, compiler, optimization, LTO, logging, and API units; cover the maximum legal call chain, callback re-entry, recursion, indirect calls, library/error paths, large locals, TLS, and applicable interrupt overhead; and MUST combine static analysis with target high-water/canary evidence over declared worst-case scenarios. |
| REQ-007 | Stack and execution claims MUST remain `BLOCKED` when units, load-bearing paths, build equivalence, prediction error, reserve source, runtime trigger, observation window, interference, or scenario coverage is incomplete. High-water evidence MUST NOT claim coverage of paths that did not execute, and average-only timing evidence MUST NOT support a real-time PASS. |
| REQ-008 | Maintainability and extensibility comparisons MUST use concrete change scenarios such as adding a source, subscriber, adapter, processing stage, or platform variant and MUST identify affected Modules, interfaces, mappings, Flows, tests, execution profiles, and deployment artifacts in terms of locality and leverage. |
| REQ-009 | `improve-codebase-architecture` reports MUST show as-is/target flow diagrams, critical path, model status and confidence, predicted/observed error, scenario gaps, resource headroom, change-scenario impact, and Pareto tradeoffs; `clarify-improvement-proposals` MUST distinguish estimates, measurements, calibrated results, validated claims, and blocked claims. |
| REQ-010 | `govern-modular-event-architecture` MUST place Flow Review and model assurance before its existing Module/Port/Event and execution authoring decisions while reusing, rather than duplicating, existing execution-efficiency, real-time scheduling, algorithm, and validate-on-device rules. |
| REQ-011 | The plugin architecture manifest, generated Description Views, skill metadata, vendor lock, algorithm inventory, and a proposed `ALG-0005` MUST describe the new governance consistently without adding a skill, architecture schema field, public CLI, Module, Port, Event, Type, State object, or execution profile. |
| REQ-012 | The change MUST include a minor plugin changeset and high-risk beta release intent within the existing `0.5.0` prerelease group, leaving feature-branch package versions unchanged and targeting the automated `0.5.0-beta.4` Version workflow result. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Extend the existing `improve-codebase-architecture`, `clarify-improvement-proposals`, and `govern-modular-event-architecture` skills; do not create a data-flow skill. |
| DEC-002 | Put detailed reusable rules in `govern-modular-event-architecture/references/flow-cost-review.md` and keep the three SKILL.md files concise and imperative. |
| DEC-003 | Treat correctness as admission, hard constraints as filters, and the remaining execution/evolution tradeoffs as a Pareto comparison; do not publish a universal weighted score. |
| DEC-004 | Do not invent universal resource margins, benchmark thresholds, deadlines, or SLOs; every budget and reserve has a product, standard, platform, baseline, or human-confirmed source. |
| DEC-005 | Permit logical architecture discussion while platform facts are unknown, but keep platform performance winners and real-time verdicts `BLOCKED`. |
| DEC-006 | Use the Register-domain re-entry and stack-overflow pattern as a portable regression fixture, not as firmware-specific product policy. |
| DEC-007 | Record the observable heuristic and evidence-selection method in proposed `ALG-0005`; Codex MUST NOT mark it accepted. |
| DEC-008 | Update the existing `governance_workflow_domain` and `governed-change-set-lifecycle` descriptions and steps without changing architectural boundaries. |
| DEC-009 | Classify the behavior addition as a minor changeset and high-risk beta increment inside the current prerelease group. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003, REQ-004 | The shared contract and all three entry skills require the four dimensions, existing/Greenfield behavior, structural alternatives, model verdicts, and external/internal compatibility distinction. | Skill-contract unit tests and focused text review. | PASS — the shared reference and all three entry skills pass the focused contract suite, and the Spec-axis review found no uncovered requirement. |
| AC-002 | REQ-005, REQ-006, REQ-007 | Contract tests reject unit ambiguity, hidden re-entry, uncovered error paths, build mismatch, missing reserve source, prediction overrun, and average-only real-time evidence; they require benchmark escalation for declared best-effort risks. | Focused regression fixtures in the plugin test suite. | PASS — eight normative fail-closed fixtures, including `MISSING-RESERVE-SOURCE`, are asserted as `BLOCKED`; the focused red/green test and complete suite pass. |
| AC-003 | REQ-008, REQ-009 | The architecture HTML-report contract requires critical-path/model evidence, resource headroom, change-scenario comparison, and Pareto tradeoffs for every Flow-affecting candidate. | Report-contract unit tests and manual template inspection. | PASS — the report contract includes model status, confidence basis, predicted/observed error, coverage, headroom, change-scenario matrix, and Pareto comparison; its contract test passes. |
| AC-004 | REQ-010, REQ-011 | Manifest and Algorithm inventory describe Flow Review using existing ownership; generated pages are deterministic and no new public schema, CLI, Module, Port, Event, Type, State, or execution profile appears. | Architecture design/development gates, generated-view comparison, and Git diff inspection. | PASS — design, development, and release gates exit 0; repeated render hashes are identical; diff inspection confirms only the existing workflow description/step and proposed `ALG-0005` were added. |
| AC-005 | REQ-011 | Vendor-lock integrated hashes and agents metadata match the changed skill artifacts. | Vendor synchronization check and integration validation. | PASS — all 28 pinned snapshots match `vendor-lock.json`, and 28-skill integration validation passes. |
| AC-006 | REQ-012 | Pending minor changeset and high-risk beta intent validate without changing package/plugin versions on the feature branch, and the version tool predicts `0.5.0-beta.4`. | Version-governance check and isolated next-version assertion. | PASS — formal metadata remains `0.5.0-beta.3`, version governance passes, and the isolated assertion returns `0.5.0-beta.4`. |
| AC-007 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012 | Complete unit, integration, vendor, version, architecture, renderer, spec, and diff-hygiene checks pass. | Recorded commands, exit codes, and minimal raw output in the implementation handoff. | PASS — 129 tests, integration, vendor, version, architecture, deterministic renderer, spec, and diff-hygiene checks pass; installed-cache hashes match source and fresh Register, Greenfield, and real-time tasks return the required fail-closed behavior. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-001 | depends_on | DEC-002 |
| REQ-003 | depends_on | DEC-005 |
| REQ-004 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-004 |
| REQ-006 | depends_on | DEC-004 |
| REQ-008 | depends_on | DEC-003 |
| REQ-010 | depends_on | DEC-001 |
| REQ-011 | depends_on | DEC-007 |
| REQ-011 | depends_on | DEC-008 |
| REQ-012 | depends_on | DEC-009 |

## Out of Scope

- Modifying, flashing, resetting, or validating the env-sensing firmware or a
  physical device.
- Resolving the Register-domain product architecture in this plugin change.
- Adding a generic cost-model numeric schema or a new architecture analyzer.
- Adding a new scheduling-analysis method beyond the existing supported method.
- Publishing a tag, pull request, marketplace update, or remote release.
- Selecting universal stack margins, utilization thresholds, deadlines, or SLOs.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user confirmed existing and Greenfield coverage, tiered
  performance evidence, real-time treatment, evolution scenarios, and model
  calibration behavior.
- Spec verification: PASS — revision 1 passed complete REQ-to-AC traceability
  before implementation; revision 2 passes implemented-state validation.
- Clarify improvement proposal: PASS — behavior, interfaces, evidence classes,
  risks, compatibility, validation, and release intent are decision-complete.
- Architecture authoring gate: PASS — design, development, and release phases
  verify the existing-module and Flow-description changes.
- TDD: PASS — the focused contract test recorded RED before the shared contract
  and again for the missing-reserve review finding; all 129 tests now pass.
- Code review Standards axis: PASS — no documented-standard violation or
  actionable Fowler smell.
- Code review Spec axis: PASS — no uncovered requirement, unverified acceptance
  criterion, scope creep, or incorrect behavior remains after the reserve-source
  fixture correction.
- Spec review: PASS — every requirement and acceptance criterion has direct
  implementation and validation evidence.
- Runtime validation: Not applicable to the plugin host; target-project runtime
  evidence remains routed through `validate-on-device`.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-04 | Materialized the authorized evidence-calibrated Flow cost governance contract. |
| 2 | 2026-08-04 | Recorded passing implementation, two-axis review, local reinstall, fresh-task scenarios, and complete validation evidence; marked the change set implemented. |
