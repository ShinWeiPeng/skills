---
spec_version: 1
spec_id: SPEC-0018
revision: 8
status: implemented
change_set: module-contract-validation-ladder
---

# Module contract validation ladder

## Problem

The governed engineering workflow emphasizes TDD and separates host checks from
on-device evidence, but it does not expose one explicit, ordered validation ladder
covering module contracts, production-code SIL, reusable Adapter contract suites,
target-compiled PIL, real-hardware HIL, and final system/soak acceptance. As a
result, a staged validation statement can still defer target feasibility and
integration risks until a large change set reaches hardware.

## Solution

Add an independent, model-invoked `verification-ladder` skill that coordinates a
governed validation method starting from an explicit Module Contract and progressing
through SIL, Adapter Contract Test, PIL, HIL, and System/Soak Test. Keep TDD as an
implementation technique within applicable host-side work, not as the complete
validation strategy. Keep `validate-on-device` as the bounded execution and evidence
engine used by device-dependent PIL, HIL, and System/Soak scenarios after Validation
Enablement; it is not an additional rung and does not own host SIL or contract tests.
Required layers are selected from the claims and affected contracts, not merely from
the fact that a repository targets an embedded system. Host evidence remains valid
for host-observable semantics, but cannot satisfy target timing, scheduler, hardware,
or long-duration integration claims.

Persist project-specific bindings in `validation/verification-ladder.yaml`. Reference
governed architecture IDs and `validation/on-device.yaml` scenarios instead of
duplicating architecture or runtime-profile definitions.

## User Stories

- As an embedded developer, I want every module to have behavioral, state,
  ordering, failure/reset, capacity, timing, throughput, and memory contracts.
- As a maintainer, I want SIL to execute production Processing code with replaceable
  hardware adapters rather than a simplified duplicate model.
- As a driver author, I want Fake, Replay/Simulator, and target hardware adapters to
  run the same demand-owned Port contract suite.
- As a firmware developer, I want PIL evidence to answer whether the target
  processor meets timing, queue, stack, and scheduling constraints.
- As a release owner, I want HIL and bounded soak tests to prove real peripherals,
  protocols, recovery, compatibility, and long-duration stability.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Each affected module MUST define input data and units, output, state transitions, call ordering, error/reset behavior, maximum batch, and applicable throughput, latency, and RAM/resource limits before implementation acceptance. |
| REQ-002 | SIL MUST execute the production Processing implementation on the host while replacing only hardware/external dependencies with Fake or Replay Adapters; a simplified duplicate Processing model MUST NOT satisfy SIL. |
| REQ-003 | SIL MUST use project-selected rates, data and time semantics, representative and boundary batch sizes, conservation/backlog assertions, injected dependency failure/timeout/gap/reset, and accelerated or paced duration scenarios where applicable. Project examples such as 2K/4K/8K, 8/24/40/127/256, pairing, and 600 seconds MUST NOT become universal defaults. |
| REQ-004 | Every implementation of the same external Port MUST run the same demand-owned Adapter contract suite, including lifecycle order, count semantics, sample format/time units, timeout/overflow/reset, failure reporting, and bounded blocking behavior. |
| REQ-005 | PIL MUST compile and run the production functional code on the project-confirmed target platform with fixed test vectors independent of real sensors or other physical inputs. It MAY establish controlled execution demand, operation cost, percentile/maximum time, pacing, batch time, and stack/Queue high-water inputs, but MUST NOT alone satisfy a production latency or deadline claim that depends on core mapping, scheduler behavior, interrupts, peripheral traffic, synchronization, or competing workloads. Platform-specific metrics such as cycles per sample or PairReady are examples selected only when the project contract defines them. |
| REQ-006 | HIL MUST use the real target composition, production core/execution-unit mapping, scheduler, interrupts, competing Tasks/workloads, sensor, bus, FIFO, transport, and applicable PC-side software paths to validate production latency/deadline behavior, arrival patterns, bus latency, clock drift, protocol compatibility, logging interference, restart, disconnect, and recovery behavior. |
| REQ-007 | System/Soak acceptance MUST cover project-selected rates and combinations for bounded long runs, logging A/B, offline/rejoin, unchanged external clients, and forbidden watchdog, unexpected reset, unexplained loss, or queue overwrite events. |
| REQ-008 | Every layer MUST define scope, inputs, metrics, PASS/FAIL/BLOCKED thresholds, evidence artifact, stop condition, and the next permitted layer; a lower layer MUST NOT claim evidence reserved for a higher layer. |
| REQ-009 | The workflow MUST preserve existing TDD, architecture governance, validation enablement, release-equivalence, and permission boundaries while making the layered strategy explicit. |
| REQ-010 | An independent `verification-ladder` skill MUST own layer selection, entry/exit criteria, evidence non-substitution, and cross-layer coordination; host SIL/contract checks MUST remain with native project test tools, while target/device PIL, HIL, and System/Soak execution MUST delegate to `validate-on-device`. |
| REQ-011 | The skill MUST resolve the target platform and applicable timing/resource model from repository evidence and governed grilling; it MUST NOT assume ESP32 or any other processor, RTOS, scheduler, toolchain, or hardware topology. Required human confirmation from architecture governance MUST be preserved. |
| REQ-012 | An embedded-system repository MUST NOT by itself invalidate host evidence or force every device layer. Each evidence claim MUST identify the lowest sufficient layer. Controlled target execution-demand evidence MAY pass at PIL; production timing or deadline claims affected by core allocation, scheduler, interrupts, synchronization, peripheral traffic, or workload interference MUST remain BLOCKED until HIL passes; system-stability claims MUST remain BLOCKED until selected System/Soak evidence passes. |
| REQ-013 | For hard/soft real-time claims, PIL measurements MUST be treated as inputs to the governed scheduling analysis, and HIL MUST validate the selected production execution profile and its interference assumptions; neither layer alone substitutes for the required analysis and final runtime acceptance. |
| REQ-014 | Each project MUST define a verification matrix that maps governed architecture references, affected contract dimensions, execution/environment changes, and evidence claims to additive required ladder layers, project-specific criteria, and explicit non-applicability rationale. Unmapped or uncertain claims MUST be BLOCKED rather than silently assigned no layer. |
| REQ-015 | Trigger ownership MUST be hybrid: `verification-ladder` defines the stable cross-project taxonomy, additive hard triggers, evidence-authority boundaries, and fail-closed behavior; each project matrix defines actual architecture IDs, platform/runtime facts, thresholds, scenarios, evidence locations, and any explicit non-applicability rationale. |
| REQ-016 | The authoritative project matrix MUST be stored at `validation/verification-ladder.yaml`, schema-validated and version-controlled. It MUST reference stable IDs from the architecture manifest and scenario/profile identifiers from `validation/on-device.yaml` without duplicating their owned definitions, and stale or missing references MUST be BLOCKED. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Create an independent `verification-ladder` skill as the authoritative coordinator, preserving TDD and `validate-on-device` as specialized child workflows. |
| DEC-002 | Separate controlled target execution demand from production timing: PIL supplies controlled target cost/resource evidence, while HIL is mandatory for timing/deadline acceptance when real core mapping, scheduling, interrupts, peripherals, synchronization, or competing workloads affect the claim. |
| DEC-003 | Use a project verification matrix rather than forcing the complete ladder for every change or allowing ad hoc per-turn selection. |
| DEC-004 | Adopt hybrid trigger ownership: universal risk/contract categories and non-substitution rules belong to `verification-ladder`; project-specific bindings and acceptance values belong to the project matrix. |
| DEC-005 | Store the authoritative project matrix in `validation/verification-ladder.yaml`, with references to architecture and on-device validation artifacts. |

## Discussion Context

### DISC-001: Validation workflow ownership

- **Situation:** TDD currently owns host red/green mechanics, `validate-on-device` owns bounded physical/native evidence, and architecture references already mention Fake Port and reusable Adapter contract suites. No single skill owns the full Module Contract → SIL → Adapter Contract → PIL → HIL → Soak progression.
- **Question:** Which skill boundary should own and coordinate the validation ladder?
- **Options and tradeoffs:** An independent skill centralizes the ladder and avoids broadening TDD or `validate-on-device`, at the cost of one promoted skill and integration work; broadening `validate-on-device` would mix host and device concerns; distributing the ladder would duplicate coordination policy.
- **User answer:** `採用獨立的 verification-ladder 技能。`
- **Explicit rationale:** Pending.
- **Resulting impact:** REQ-009, REQ-010, DEC-001, AC-006, and the promoted skill, routing, documentation, architecture, distribution, and test scope.

### DISC-002: Layer applicability policy

- **Situation:** The ladder can require every rung for every change, or select only the layers needed to prove the affected contracts while preserving non-substitution rules. This affects cost, stopping conditions, and whether a documentation-only or host-only change is unnecessarily blocked on hardware.
- **Question:** Must every engineering change run all ladder layers, or should the skill derive required layers from risk and affected contracts?
- **Options and tradeoffs:** Requiring every layer for every change maximizes uniformity but wastes hardware capacity and blocks host-only changes; claim-driven selection keeps validation proportional but requires explicit non-substitution rules; allowing ad hoc omission is cheapest but recreates the original ambiguity.
- **User answer:** Adopt the project verification matrix. Embedded projects must still allow PC tests for claims those tests can prove, and the target comes from the project-specific grilling outcome rather than being fixed to ESP32.
- **Explicit rationale:** Pending.
- **Resulting impact:** REQ-003, REQ-005, REQ-008, REQ-010, REQ-011, REQ-012, REQ-014, DEC-003, layer entry/exit policy, and AC-001.

### DISC-003: PIL versus HIL timing authority

- **Situation:** The phrase "calculation time" conflated controlled execution demand on the real processor with end-to-end production latency under the selected core mapping and interference environment.
- **Question:** Can PIL alone satisfy a calculation-time claim, or must production timing affected by core scheduling reach HIL?
- **Options and tradeoffs:** PIL-only timing is fast and isolates processing cost but omits real scheduler/peripheral interference; HIL-only timing reflects the integrated system but makes isolated regressions harder to diagnose; using PIL as a controlled baseline and HIL as final production timing acceptance preserves both attribution and realism.
- **User answer:** Production calculation time is core-related and must reach HIL.
- **Explicit rationale:** Core allocation and interference affect the observed calculation time.
- **Resulting impact:** REQ-005, REQ-006, REQ-012, REQ-013, DEC-002, AC-004, and AC-005.

### DISC-004: Trigger taxonomy ownership

- **Situation:** A project matrix still needs deterministic inputs. Trigger categories could be entirely fixed by the skill, entirely authored per project, or split between a stable cross-project taxonomy and project-specific mappings/thresholds.
- **Question:** Which part of trigger planning is universal and which part is project-owned?
- **Options and tradeoffs:** A fully fixed skill table is consistent but overgeneralizes platforms; a fully custom project table is flexible but can omit important risk classes; a hybrid uses stable contract/risk categories plus project-owned architecture IDs, thresholds, scenarios, and layer mappings, adding modest setup cost while remaining deterministic and portable.
- **User answer:** Adopt the hybrid model.
- **Explicit rationale:** Pending.
- **Resulting impact:** REQ-014, REQ-015, DEC-004, AC-009, AC-010, matrix schema, trigger evaluation, and behavioral contract tests.

### DISC-005: Project matrix persistence

- **Situation:** The selected hybrid model requires a versioned project-owned artifact for platform bindings, thresholds, scenarios, and trigger mappings. It could be stored in a dedicated validation file, embedded in the architecture manifest, or repeated in each change-set specification.
- **Question:** Where should the authoritative project verification matrix be stored?
- **Options and tradeoffs:** A dedicated validation file has a clear machine-checkable owner and can reference architecture/runtime artifacts, at the cost of a new schema; embedding it in the architecture manifest couples validation policy to architecture schema; repeating it in each change-set spec avoids a new project file but loses a durable project matrix and duplicates rules.
- **User answer:** Adopt `validation/verification-ladder.yaml`.
- **Explicit rationale:** Pending.
- **Resulting impact:** REQ-014, REQ-015, REQ-016, DEC-005, AC-009, AC-010, AC-011, matrix path and schema, architecture/profile references, tooling, project bootstrap, and validation evidence.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-008 | A realistic embedded change is rejected as incomplete unless each module contract and each selected layer has explicit thresholds, evidence, stop conditions, and non-substitution rules. | Behavioral skill-contract scenarios and manual instruction review. | PASS: matrix validation tests and manual skill review confirm explicit layer contracts and evidence-authority boundaries. |
| AC-002 | REQ-002, REQ-003 | The workflow selects production Processing code plus Fake/Replay Adapters for SIL and rejects a duplicate simplified Processing model as SIL evidence. | Positive and negative skill-contract scenarios. | PASS: skill contract requires production functional code and rejects a simplified duplicate as SIL. |
| AC-003 | REQ-004 | Fake, Replay/Simulator, and target adapters for one Port are assigned the same demand-owned suite and lifecycle/semantic/failure/blocking contract. | Skill-contract scenarios and development-gate schema tests. | PASS: demand-owned shared Adapter Contract suite and required lifecycle, semantic, failure, and blocking checks are documented and contract-tested. |
| AC-004 | REQ-005, REQ-013 | Controlled target execution-demand and resource inputs require target-compiled PIL evidence and cannot be passed by PC TDD/SIL, while PIL alone is rejected for production core/scheduler-dependent latency or deadline acceptance. | Positive and cross-layer substitution-rejection scenarios. | PASS: authority tests require PIL for controlled target cost and HIL for production timing; PIL-only production timing is BLOCKED. |
| AC-005 | REQ-006, REQ-007, REQ-012, REQ-013 | Production timing affected by core mapping or interference, physical hardware behavior, and release stability require bounded HIL and applicable System/Soak evidence with the production execution profile, unchanged external compatibility paths, and explicit forbidden events. | Profile/evidence contract tests and instruction review. | PASS: layer instructions and taxonomy require HIL for integrated timing/physical claims and System/Soak for stability, with bounded runs and forbidden events. |
| AC-006 | REQ-009, REQ-010 | The independent owner integrates with existing TDD, architecture, runtime validation, release, plugin distribution, and documentation contracts without duplicating detailed policy; device-dependent execution is delegated to `validate-on-device`. | Repository validation, architecture gate, distribution validation, and two-axis review. | PASS: 192 plugin tests, release architecture gate, distribution validation, and Standards/Spec review passed. |
| AC-007 | REQ-003, REQ-005, REQ-011 | Platform, pacing, batch, timing, and resource criteria are derived from the confirmed project contract; test scenarios reject hard-coded ESP32 or project-example defaults when the selected platform differs. | Cross-platform positive and negative behavioral skill-contract scenarios. | PASS: cross-platform fixture passes with Linux-specific bindings and the skill contains no universal ESP32 or example-rate defaults. |
| AC-008 | REQ-008, REQ-012 | Host tests remain admissible for host-observable claims in embedded projects, but attempts to use them as target timing, scheduler, physical-hardware, or soak evidence are rejected as BLOCKED. | Evidence-claim substitution matrix tests. | PASS: host-only planning passes while production-timing evidence without HIL returns BLOCKED. |
| AC-009 | REQ-014 | A project matrix deterministically produces additive required layers from architecture references, contract dimensions, execution/environment changes, and evidence claims; an unmapped or uncertain claim returns BLOCKED with the missing mapping. | Matrix-schema and positive/negative trigger-evaluation contract tests. | PASS: public CLI tests verify ordered additive planning and deterministic BLOCKED results for unknown or unmapped triggers. |
| AC-010 | REQ-015 | Cross-project taxonomy and evidence-authority rules remain stable across two different platform fixtures while each fixture supplies different architecture bindings, thresholds, and scenarios without changing the skill. | Cross-project behavioral fixtures and schema validation. | PASS: host/target and Linux fixtures share one taxonomy while resolving different project-owned bindings. |
| AC-011 | REQ-016 | A valid `validation/verification-ladder.yaml` resolves architecture and on-device scenario references; missing, stale, duplicated, or mismatched references produce deterministic BLOCKED results. | Matrix schema, reference-resolution, stale-reference, and duplicate-ownership tests. | PASS: 13 dedicated tests cover valid resolution plus stale, missing, duplicate, mismatched, malformed, and nested-unknown inputs. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| AC-001 | depends_on | REQ-001 |
| AC-001 | depends_on | REQ-008 |
| AC-002 | depends_on | REQ-002 |
| AC-002 | depends_on | REQ-003 |
| AC-003 | depends_on | REQ-004 |
| AC-004 | depends_on | REQ-005 |
| AC-005 | depends_on | REQ-006 |
| AC-005 | depends_on | REQ-007 |
| AC-006 | depends_on | REQ-009 |
| AC-006 | depends_on | REQ-010 |
| REQ-010 | depends_on | DEC-001 |
| AC-007 | depends_on | REQ-003 |
| AC-007 | depends_on | REQ-005 |
| AC-007 | depends_on | REQ-011 |
| AC-008 | depends_on | REQ-008 |
| AC-008 | depends_on | REQ-012 |
| REQ-013 | depends_on | DEC-002 |
| AC-004 | depends_on | REQ-013 |
| AC-005 | depends_on | REQ-012 |
| AC-005 | depends_on | REQ-013 |
| REQ-014 | depends_on | DEC-003 |
| AC-009 | depends_on | REQ-014 |
| REQ-015 | depends_on | DEC-004 |
| AC-010 | depends_on | REQ-015 |
| REQ-016 | depends_on | DEC-005 |
| AC-011 | depends_on | REQ-016 |

## Out of Scope

- Implementing project-specific Processing code, drivers, firmware, or PC software.
- Fixing either failed embedded refactor discussed in the linked retrospective.
- Treating example rates, batch sizes, or durations as universal defaults when a
  target project's contract selects different values.
- Releasing or publishing the governed engineering plugin in this change set.

## Open Decisions

None.

## Routing/Gates

- Engineering risk routing: modifying architecture/workflow change; clarification and modular architecture gates required.
- Grilling: PASS; OD-001 through OD-004 are resolved by DEC-001 through DEC-005.
- Skill Creator: active for skill design.
- Clarify Improvement Proposals: resumes after decisions are complete.
- Govern Modular Event Architecture: required before product edits.
- TDD and runtime validation: execution gates to be specified after ownership is selected.
- Spec review: PASS.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 0 | 2026-09-04 | Captured the requested module-contract and layered execution-environment validation method; opened ownership decision. |
| 1 | 2026-09-04 | Selected an independent `verification-ladder` owner and placed `validate-on-device` as the execution/evidence engine for device-dependent PIL, HIL, and System/Soak scenarios. |
| 2 | 2026-09-04 | Clarified that host tests remain valid in embedded projects, prohibited only cross-layer evidence substitution, and made platform, pacing, and resource criteria project-specific rather than ESP32-specific. |
| 3 | 2026-09-04 | Split controlled PIL execution-demand evidence from HIL production timing authority; required HIL when core scheduling or real interference affects latency/deadline claims. |
| 4 | 2026-09-04 | Selected a project verification matrix for layer applicability and opened the trigger-taxonomy ownership decision. |
| 5 | 2026-09-04 | Selected hybrid trigger ownership and opened the project-matrix persistence decision. |
| 6 | 2026-09-04 | Selected `validation/verification-ladder.yaml` as the authoritative project matrix and completed the decision interview. |
| 8 | 2026-09-04 | Recorded implementation PASS evidence after Standards and Spec review. |
