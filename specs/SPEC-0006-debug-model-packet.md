---
spec_version: 1
spec_id: SPEC-0006
revision: 1
status: confirmed
change_set: debug-model-packet
---

# Debug Model Packet

## Problem

Complex debugging discussions can reproduce a failure without establishing a
shared calculation model. Flowcharts alone hide counter units, reset conditions,
accounting identities, and the exact event where observed behavior diverges from
the intended meaning.

## Solution

Add a risk-triggered Debug Model Packet to `diagnosing-bugs` between minimisation
and hypothesis generation. Require counter/state contracts, reconciliation,
worked traces, visibly marked error paths, and a user-confirmed understanding
gate before root-cause or repair discussion.

## User Stories

- As a debugger, I can trace each counter and state transition from evidence.
- As a collaborator, I can identify the first unclear or divergent event before
  evaluating causes and repairs.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Model-alignment bugs MUST produce a Debug Model Packet after reproduction and before hypotheses; simple stateless bugs MAY skip it only with an explicit reason. |
| REQ-002 | The packet MUST distinguish confirmed evidence, inference, and items still to verify. |
| REQ-003 | The packet MUST contain decision flow, applicable actor sequence, counter/state contracts, conservation or reconciliation, a minimal event trace, and the first semantic divergence. |
| REQ-004 | The decision flow MUST visibly and textually mark the observed error path, evaluated branch values, `FIRST DIVERGENCE`, final symptom evidence, and inferred paths. |
| REQ-005 | The workflow MUST stop for user confirmation of the computation model before ranking root causes or comparing repairs. |
| REQ-006 | The promoted documentation and release metadata MUST remain synchronized with the skill behavior. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Keep the phase trigger risk-based rather than mandatory for every bug. |
| DEC-002 | Keep exact arithmetic in tables and traces; Mermaid diagrams cannot replace it. |
| DEC-003 | Treat user confirmation as agreement with the computation model only, not with a cause or repair. |
| DEC-004 | Use textual path labels in addition to color so error semantics survive monochrome rendering and copying. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-005 | Phase 2.5 follows minimisation, precedes hypotheses, and blocks premature diagnosis until confirmation. | Skill contract tests. | Pending implementation verification. |
| AC-002 | REQ-002, REQ-003 | The reference contains every evidence, diagram, contract, equation, and trace requirement. | Skill contract tests and content inspection. | Pending implementation verification. |
| AC-003 | REQ-004 | Error-path styling and text labels distinguish confirmed and inferred paths and bind the symptom to evidence. | Skill contract tests. | Pending implementation verification. |
| AC-004 | REQ-006 | Promoted documentation describes the packet and understanding gate. | Documentation contract test. | Pending implementation verification. |
| AC-005 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 | Focused tests, complete plugin tests, skill validation, version governance, and diff hygiene pass. | Recorded local commands and exit codes. | Pending implementation verification. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-002 |
| REQ-005 | depends_on | DEC-003 |
| REQ-004 | depends_on | DEC-004 |

## Out of Scope

- Changing product debugging code or SamplePairer behavior.
- Declaring a root cause or selecting a repair for a specific bug.
- Requiring sequence diagrams for stateless single-actor failures.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — the user confirmed the packet workflow and error-path labels.
- Spec verification: pending strict contract validation.
- Architecture impact: N/A — skill instructions and documentation change without
  Module, Port, Event, Type, State, dependency, execution, or product-algorithm
  changes.
- TDD: PASS — contract tests were written with the behavior and pass locally.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-05 | Materialized the authorized Debug Model Packet contract. |
