---
spec_version: 1
spec_id: SPEC-0093
revision: 10
status: confirmed
change_set: fir-canopen-zero-compatibility
working_id: WORKING-SPEC-92f2066d70bd-fir-canopen-zero-compatibility
task_ref: 01a139dd-3535-7761-9d87-2e2b624ae4e8
---
# FIR CANOpen 零值初始化相容性診斷

## Problem
User reports CANOpen communication abnormal after selecting a collision FIR model.

## Solution
Repair env_sensing compatibility for FIR zero-as-knob initialization and actual knob multiplier updates. Related AM437x source remains reference-only. Device/model baseline parameters are unchanged.

## User Stories
User needs existing controller CANOpen initialization to work with a selected FIR model.

## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | In FIR mode, accept CANOpen 0x2007:00 REAL32 zero as the legacy use-knob selector command, not as numeric multiplier zero. Preserve node/object/type and controller wire behavior. |
| REQ-002 | Resolve selector positions 1..15 and position 0 as 16 by effective_multiplier = knob_minimum + (position - 1) * (knob_maximum - knob_minimum) / 15. Defaults are minimum 0.5, maximum 2.0, and derived interval 0.1. Minimum/maximum are configurable in Device Configuration; interval is automatically calculated, not independently edited. Effective FIR threshold is JSON baseline_threshold times that single positive multiplier. Resolve the current position for initialization and update FIR on actual stable knob changes while zero selects the knob. Do not reassert an unchanged position over a later effective setting; preserve applicable existing operation ordering. These endpoints map the physical knob; direct master multipliers retain their separate per-mille/direct-value semantics. |
| REQ-003 | Keep the common zero sentinel distinct from the resolved runtime multiplier across configuration staging, runtime Apply, explicit Save and boot restoration. Configuration changes alone do not Save. Positive finite explicit multipliers and original-algorithm behavior remain valid; negative/nonfinite values and nonrepresentable effective thresholds remain rejected. A failed selector read or multiplier application must retain established rollback/error behavior and never run FIR with zero. |
| REQ-004 | Implement this compatibility repair in env_sensing, with configuration, parent runtime mapping, selector-to-FIR application, directly affected regressions, authored architecture descriptions and specification references updated together. AM437x source is reference-only; no firmware flashing, unrelated transport changes, new CAN objects, or changes to the physical selector encoding are authorized by this decision; configurable FIR endpoints and derived intervals are included by the later user request. |

| REQ-005 | Master parameter integers use per-mille directly: multiplier = parameter / 1000, e.g. 1000 -> 1.0 and 1253 -> 1.253. Do not snap direct values to the knob interval. Existing master code already performs this conversion before CANOpen REAL32 transmission; retain wire representation and do not divide the received multiplier again. Zero retains the adopted knob sentinel. |
| REQ-006 | After Device Configuration selects a FIR collision model, show editable knob minimum and maximum multiplier settings, default 0.5 and 2.0, plus the automatically derived read-only 16-position interval. Hide these FIR-only settings for Original while preserving their configuration values. Reuse the existing multiplier setting control and existing effective multiplier display; do not add duplicate controls, display rows or a second per-mille input. Preserve their existing presentation and Draft/Apply/Save lifecycle. Master per-mille interpretation remains REQ-005, independently of this narrow UI addition. |

## Decisions
| ID | Decision | Source |
|---|---|---|
| DEC-001 | FIR CANOpen 0x2007:00 = 0 uses the physical knob; convert its position into the existing model multiplier mapping. This explicitly supersedes SPEC-0062 zero-rejection wording only where it prevents the adopted zero-selector compatibility. Zero is never an effective multiplier. | user-fir-zero-adopt-20261014: annotation 1 and visible answer 沿用 to Q-001@2 |

| DEC-002 | Replace the previously assumed 0.50..4.25 / 0.25 FIR knob defaults with minimum 0.5, maximum 2.0, interval 0.1. Make endpoints configurable in Device Configuration and calculate the interval automatically across the existing 16 physical positions. This refines DEC-001 mapping while retaining zero-as-knob. | user-fir-multiplier-ui-20261014: annotation 1 |
| DEC-003 | Master parameter value is per-mille multiplier: 1000=1x, 1253=1.253x. A directly supplied multiplier is not quantized to knob steps. Existing controller normalization/CAN REAL32 is retained; no second division in ENV_SENSING. | user-fir-multiplier-ui-20261014: master per-mille request and supplied examples |

| DEC-004 | Display knob minimum/maximum only when the selected collision model is FIR, using defaults 0.5 and 2.0. These fields configure the knob mapping; preserve the user's separately specified direct master per-mille multiplier meaning and existing positive-value contract. | user-fir-ui-conditional-20261014: annotation 1 explicitly names knob minimum/maximum and FIR-only visibility; user-fir-multiplier-ui-20261014 direct master examples |

| DEC-005 | Reuse the existing multiplier input and existing effective multiplier display. Supersede the duplicate-field portions of the prior UI layout recommendation. New UI additions are only FIR-specific knob minimum/maximum and derived read-only interval; the master numeric meaning and zero-as-knob requirements remain. | user-fir-ui-reuse-20261014: annotation 1 and annotation 2 both state 不需要，原本就有了 |

| DEC-006 | Reuse the existing effective multiplier display; do not add another read-only multiplier field or duplicate result row. This separately records annotation 2 while DEC-005 retains the overall narrowed UI scope and annotation 1 setting reuse. | user-fir-ui-reuse-20261014: annotation 2 states 不需要，原本就有了 |

| DEC-007 | User confirms and authorizes execution of the accumulated FIR zero-as-knob repair, configurable 0.5..2.0 knob endpoints and narrow UI placement: existing Collision model group, min/max row before summaries, read-only step helper, existing input/effective display reused. This execution message also confirms the last presented placement recommendation. | user-start-spec0093-20261014: visible exact instruction 開始執行 |

## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-003 | FIR configuration accepts zero as selector and CANOpen stages it without 0x06090030; original zero and positive multiplier cases remain valid, negative and nonfinite cases reject. | Configuration validation and production CanopenConfigurationSession / OD callback contract regressions. | Pending |
| AC-002 | REQ-002, REQ-003 | All 16 default positions map to 0.50..2.00 by 0.10, with hardware position 0 representing the final position; custom endpoints include both bounds and derived interval (max-min)/15. A fixture baseline B yields threshold B times multiplier, never zero. Actual stable position changes update FIR; unchanged polls do not overwrite a later setting. | SensorPipelineApplication FIR inference/selector production-seam regressions and initialization/runtime mapping tests. | Pending |
| AC-003 | REQ-003 | FIR zero staging/Apply/explicit Save/boot restoration keeps selector semantics and computes a positive runtime threshold. Switching or restart rollback does not leak a partial setting; explicit positive and original semantics regressions pass. | FirmwareSystemRuntime/configuration storage and reset lifecycle tests. | Pending |
| AC-004 | REQ-001, REQ-002, REQ-003 | On identified matching firmware, unchanged controller zero initialization completes with SDO acknowledgement, NMT Operational and configured PDO reception; reset has no Remote VIB Initial Fail at 0x2007. Confirm current and changed knob positions affect FIR threshold in the same run. | Bounded independent CAN log plus controller TCP monitor and device threshold evidence; image identity required. Existing failed captures establish the diagnostic baseline only. | Pending |
| AC-005 | REQ-004 | Scoped code/test diff, authored-design rendering, planned design/full pinned C++ AST gates, directly affected host regressions and ESP32-S3 build pass. No AM437x edits or generated-manifest hand edits. | Single project architecture_cli.py, native test runners, scoped diff check and PlatformIO build; release/physical claims reported separately. | Pending |

| AC-006 | REQ-005 | Master 1000 and 1253 yield effective multipliers 1.000 and 1.253 and corresponding FIR thresholds, without knob-step rounding or double normalization. Zero enters selector semantics. | Captured REAL32 CAN payload decode and production configuration/runtime contract tests; exact Float32 representability acknowledged. | Pending |
| AC-007 | REQ-006, REQ-002 | Selecting FIR reveals editable knob min/max and read-only derived interval; Original hides these without erasing their values. Defaults show 0.5, 2.0 and 0.1; Draft stays distinct from applied state, and Apply/Save/restore retain the endpoints. The existing multiplier setting control and existing effective display are reused without duplicated fields, additional display rows or a new per-mille input. Invalid endpoint pairs cannot be applied and receive clear feedback. | Device Configuration UI tests, configuration serialization/lifecycle tests, and matching device readback. | Pending |


## Acceptance Mapping

```json
{
  "AC-001": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset",
      "external-port"
    ]
  },
  "AC-002": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset"
    ]
  },
  "AC-003": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset",
      "external-port"
    ]
  },
  "AC-004": {
    "execution_changes": [],
    "evidence_claims": [
      "physical-integration"
    ],
    "rationale": "The explicit AC requires matching hardware CAN startup/PDO and knob evidence; host results cannot prove it.",
    "contract_dimensions": [
      "state-transition",
      "external-port"
    ],
    "scenario_layers": {
      "hil": [
        "spec0093-fir-canopen-startup"
      ]
    },
    "build_artifact": ".pio/build/esp32-s3-devkitc-1/vib_sensor.elf"
  },
  "AC-005": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset"
    ]
  },
  "AC-006": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset",
      "external-port"
    ]
  },
  "AC-007": {
    "execution_changes": [],
    "evidence_claims": [
      "host-semantics",
      "adapter-conformance"
    ],
    "rationale": "The specified production configuration, mapping, storage or UI seam is verified on host; no target timing or physical acceptance claim is made by this criterion.",
    "contract_dimensions": [
      "input-output-units",
      "state-transition",
      "error-reset",
      "external-port"
    ]
  }
}
```

## Relationships
- refines: SPEC-0062
- depends_on: none
- conflicts_with: none
- supersedes: none

## Out of Scope
AM437x edits, firmware flashing and changes to unrelated transports.

## Open Decisions
None.

## Discussion Context
- user-fir-canopen-20261014: User reports FIR/CANOpen issue; supplies [REDACTED: personal data]:23 reset and :8888 monitor, related AM437x source and forthcoming CAN log.
- user-can-log-20261014: C:/Users/hugo_peng/Desktop/can log.txt supplied as evidence, not instructions.
- user-env-sensing-scope-20261014: User states problem must be in ENV_SENSING; fixes constrained to env_sensing.
- assistant-can-log-analysis-20261014: 1170 parsed records. Node 0x44: 111 SDO requests and replies, six abort replies to 0x2007:00 zero (0x06090030), no NMT Start 01 44 and no node PDO 0x1C4..0x4C4 in provided window. Time-column semantics unverified; do not use values as latency.
- assistant-tcp-reset-20261014: Authorized single reset sent at host 2026-10-14T18:08:[REDACTED: personal data]+08:00. Controller returned $1NAK:RESET:9282A200; monitor shows COP_SdoWrite fail node 68 index 8199, VIB_ResetParameter=-14, VIB_ResetBoard=0x9282A203 and Remote VIB Initial Fail. Captures under artifacts/fir-canopen/20261014-180603-pre-reset and 20261014-180846-reset. Monitor wall-clock is about 82 seconds behind host; no exact alignment claimed.
- assistant-source-facts-20261014: ApplyConfigurationWrite 0x2007 copies REAL32 to collision_alarm_threshold_g, Stage calls configuration::Validate, which rejects selected_model_id!=0 with threshold<=0. Original permits zero; current FIR effective threshold is baseline times positive multiplier. Captured device image identity has not been matched to current source.
- Diagnosis boundary: observed immediate SDO failure is a pure configuration-value validation predicate. Reset is the stimulus; no counter, queue, timing or event-order hypothesis is needed to explain the rejection. Do not attribute bus-off, CPU starvation or transport loss to these captures.


### DISC-001: FIR 零值沿用旋鈕
- **Situation:** Node 0x44 initialization writes zero to 0x2007:00; supplied CAN log records six 0x06090030 aborts and actual TCP reset returns Remote VIB Initial Fail.
- **Question:** FIR 模式收到 CANOpen 0x2007:00 = 0 時，是否應沿用「使用旋鈕」語意，將旋鈕位置轉換為模型倍率？
- **Options and tradeoffs:** Persisted open text question; adoption restores legacy zero command compatibility and requires positive runtime resolution and FIR selector updates rather than treating zero as a valid numeric multiplier.
- **User answer:** 沿用
- **Explicit rationale:** None separately stated by the user. Annotation 1 selects the use-knob/model-multiplier phrase.
- **Resulting impact:** DEC-001, REQ-001..004 and AC-001..005. Repair stays in env_sensing. Replace model-mode zero rejection only for the adopted selector behavior; preserve zero-versus-effective-multiplier distinction. No execution grant is inferred from this answer.
- **Source:** user-fir-zero-adopt-20261014; annotation 1; Q-001 version 2.

### Proposed implementation coverage
- configuration::Validate admits the selector sentinel while FIR EffectiveThreshold retains its positive-multiplier invariant.
- CanopenConfigurationSession stages the common setting and existing parent configuration paths resolve the physical position; handle model threshold-only paths so zero enters selector mode correctly.
- SensorPipelineApplication applies actual selector changes to the selected FIR multiplier, preserving source generation and existing reset/rollback boundaries.
- Keep original-to-model neutral-conversion behavior outside this narrow compatibility repair unless it incorrectly rewrites an already adopted saved FIR zero selector; make that distinction explicit in regressions.
- Update authored architecture sources and references to SPEC-0062 zero-only rules; preserve unrelated accepted decisions and existing schema/generator ownership.
- Device acceptance requires matching firmware identity and complete CAN startup/PDO evidence. The user authorized diagnosis/reset, not flashing a repaired image.

### DISC-002: 可設定旋鈕範圍與 master 千分比
- **Situation:** User refines the FIR multiplier mapping and asks how Device Configuration UI should be designed. This is the same compatibility change set; implementation remains unstarted.
- **Question:** User asks: device configure UI該如何設計?
- **Options and tradeoffs:** UI sketch is candidate only. Per-mille integer entry can mirror master settings with a read-only times-value preview; editable endpoints and derived interval keep the physical range clear. Whether these bounds also constrain direct values remains unresolved.
- **User answer:** FIR碰撞模型倍率預設最小0.5、最大2、間隔0.1。可以在device configure增加最小、最大的設定，間格自動換換。還有mater參數設定值的表示直接當作倍率，使用千分比。1000就是1倍、1253就是1.253倍。device configure UI該如何設計?
- **Explicit rationale:** No separate rationale was supplied. The example 1253 means 1.253 without rounding to a 0.1 knob step.
- **Resulting impact:** DEC-002/003, revised REQ-002/004 and AC-002; add REQ-005/006 and AC-006/007. Preserve zero-as-knob and existing physical selector encoding; initial fixed range is superseded. Need one bounds-scope decision before final UI policy.
- **Source:** user-fir-multiplier-ui-20261014, annotation 1 and current master/UI request.

### UI discovery and ambiguity ledger
- Confirmed: 4-bit physical selector, 16 positions; position 0 is logical position 16. Default interval (2.0-0.5)/15=0.1.
- Confirmed: AM437x currently divides stored master threshold integer by 1000, then writes REAL32 at the existing 0x2007:00. ENV_SENSING receives the normalized value; do not divide twice.
- Confirmed: current web form already uses Collision model, common numeric setting and Draft/Apply/Save; imported-model summary uses the raw setting. Zero-selector summary must use actual resolved runtime multiplier/threshold.
- Candidate: FIR card with use-knob toggle / direct per-mille integer field (step 1), adjacent times-value preview, editable min/max in times, computed read-only interval and separate actual effective multiplier/threshold. This is not an adopted final layout.
- Open: bounds applicability to direct master/Web multiplier and resulting out-of-range treatment. Ask bounds applicability first; do not silently clamp, quantize or fabricate an adopted rejection policy.
- Scope: ENV_SENSING configuration/runtime/UI and corresponding spec/architecture/verification; related master source remains reference-only. No program execution/flash grant in this user request.

### DISC-003: FIR 才顯示旋鈕範圍
- **Situation:** During UI discovery, user supplies the intended conditional layout instead of leaving the field placement unspecified.
- **Question:** Latest annotation clarifies the prior request for Device Configuration UI design.
- **Options and tradeoffs:** Use the existing Collision model section; show the FIR-specific knob range only for a selected FIR model, leaving Original's controls unchanged. The proposed per-mille entry with times preview is still a layout recommendation.
- **User answer:** 我的想法是當device configure 碰撞模型選擇FIR後，再顯示旋鈕最小、最大的設定選項。預設就是0.5、2.0
- **Explicit rationale:** No separate rationale supplied.
- **Resulting impact:** DEC-004 and refined REQ-006/AC-007. The explicit knob-labelled range resolves the proposed endpoint applicability: map knob positions; retain separate direct master meaning and existing positive-value acceptance. No silent clamp or step rounding is introduced for direct master settings. UI proposal/implementation remain distinct.
- **Source:** user-fir-ui-conditional-20261014, annotation 1; preceding per-mille requirement remains carried forward.

### UI layout proposal for review
- Keep the current Collision model selector and collision detection enable controls.
- When FIR is selected: display knob minimum [0.5] x, knob maximum [2.0] x, and read-only interval [0.1] x with the (max-min)/15 formula. Original hides this block and does not reset values.
- Reuse the existing multiplier setting control and its presentation. Do not add a per-mille input or another multiplier entry. Master conversion remains REQ-005 and zero still uses the existing shared field.
- Reuse the existing effective multiplier display and model summary. Do not create an additional read-only multiplier field or duplicate result row. Existing display must continue to represent the actual resolved runtime multiplier for zero selector.
- Preserve Apply (runtime) and Save (persistence), and validate finite positive minimum below maximum. Show direct input precision separately from computed knob interval; do not snap master 1253 to 1.2/1.3.
- Prior ledger entry on bounds scope is resolved by explicit knob labels plus the carried direct master requirement. The layout remains proposed; the source/spec/architecture/verification change set has not been executed.

### DISC-004: 沿用既有倍率設定與生效顯示
- **Situation:** User reviews the UI table and identifies two proposed rows as existing functionality, so they must not be treated as new UI work.
- **Question:** Annotation review of 倍率設定（千分比） and 目前生效倍率.
- **Options and tradeoffs:** Reuse current controls and display; remove duplicate-field recommendations while retaining the adopted FIR-only knob range fields and automatic interval.
- **User answer:** Annotation 1 on 倍率設定（千分比）: 不需要，原本就有了. Annotation 2 on 目前生效倍率: 不需要，原本就有了.
- **Explicit rationale:** User explicitly states both already exist.
- **Resulting impact:** DEC-005 supersedes the duplicate portions of the prior UI candidate. Refine REQ-006 and AC-007. Newly added UI scope is only knob minimum, maximum and derived interval shown for FIR. Reuse rather than remove existing controls; preserve master per-mille and zero-selector runtime repair.
- **Source:** user-fir-ui-reuse-20261014, annotation 1 and annotation 2.
## Execution confirmation

The current visible user message is exactly 開始執行, source user-start-spec0093-20261014. It confirms the preceding complete scope and UI placement. Acceptance selectors below are derived from the existing AC validation methods and add no behavior or acceptance threshold. No flashing or AM437x modification is included. Source identifiers are caller-attested references to this conversation; desktop hook trust/loading/firing remains unverified.

## Routing/Gates
Decision adopted; product execution not granted. Current router retains spec-governance and reports BLOCKED project validation: layout invocation timed out at 120 seconds. Diagnosis/specification persistence may continue; required architecture/validation gates must pass before product delivery. Manual owner persistence is used; desktop hook trust/loading/firing unverified.

## Revision History
- Revision 9: record current explicit execution/placement confirmation and derive acceptance selectors from unchanged AC methods for materialization/admission; reuse the same actual current user authorization for this preparation.
- Revision 8: give the two independently sourced annotation corrections distinct decision bindings; behavior and UI scope unchanged.
- Revision 7: record both UI reuse annotations, remove duplicate control/display proposal, and narrow new UI work to FIR knob endpoints and derived interval.
- Revision 6: normalize the empty Open Decisions field; proposed UI review and execution status remain outside semantic decisions.
- Revision 5: adopt FIR-only knob endpoint visibility and defaults, preserve direct master semantics, and present complete UI layout proposal; no product source written.
- Revision 4: adopt configurable 0.5..2.0 FIR knob defaults with automatic interval and direct master per-mille semantics; persist UI candidate and unresolved bounds applicability.
- Revision 3: adopt user answer 沿用, resolve Q-001@2, add zero-selector/FIR runtime/verification scope; product authority not inferred.
- Revision 1: save reported issue, user scope, supplied CAN evidence, actual TCP reset reproduction and source/spec discrepancy.

## Current Specification

See Problem, Solution, Requirements and Acceptance Criteria above.

## Decision History

See Decisions, Discussion Context and the sourced Discussion History below.

## Pending Discussion

None.

## Completeness Gaps

None.

