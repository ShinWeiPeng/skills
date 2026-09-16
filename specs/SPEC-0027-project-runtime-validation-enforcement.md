---
spec_version: 1
spec_id: SPEC-0027
revision: 4
status: implemented
change_set: project-runtime-validation-enforcement
---

# 專案硬體驗證要求與驗收關卡強制銜接

## Problem

The installed 0.14.0 guided router passes the current prompt to classify_risk.classify without project runtime policy or current acceptance claims. In task 01a0a8d3-46dd-7991-8159-5b4ab18281ac, the execution prompt was 開始執行 and the reported required_gates were tdd and code-review. The firmware project's architecture/adoption.yaml declares runtime_validation.applicability: required. SPEC-0055 nevertheless records host PASS for criteria involving physical configuration, while explicitly stating that device validation was not performed. This establishes a routing input and acceptance-evidence gap, not proof that every embedded change needs HIL.

## Solution

Integrate fresh project validation context, additive gate selection, and evidence-authority checks into the existing governed workflow. Update skill instructions and executable enforcement together. A reload must re-evaluate project requirements rather than only reread SKILL.md. Preserve the distinction between routing success, implementation progress, runtime acceptance, and release acceptance.

## User Stories

- As a user, I can say reload skills or continue without losing the project's required validation gates.
- As a reviewer, I can see why a layer is required and why missing hardware evidence prevents acceptance.
- As a maintainer, I can test this behavior entirely with host fixtures without operating the firmware project.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Scope changes only the governed engineering skill source, contracts, tests, documentation and derived architecture/distribution artifacts. Do not modify env_sensing or SPEC-0055, flash devices, install or publish the plugin. |
| REQ-002 | At task entry, resume, explicit skill reload, and acceptance, resolve current task/SPEC context and read applicable architecture/adoption.yaml, architecture/manifest.yaml, validation/verification-ladder.yaml and validation/on-device.yaml. Record paths, content hashes, selected skill version and presence/validity states. Missing files must remain distinguishable from explicit non-applicability. |
| REQ-003 | Compute required gates as an additive union of universal rules, project policy and affected SPEC/contract claims. Prompt keywords may add gates but must not remove project obligations. Short commands inherit the resolved change-set context. Ambiguous or contradictory references block dependent acceptance; read-only investigation remains available. |
| REQ-004 | runtime_validation: required mandates an applicability assessment. The existing verification-ladder owner selects the lowest sufficient layers using project mappings. Physical integration and production timing require HIL when applicable. Do not force every embedded change through every layer. A host-only decision needs a traceable project-specific rationale; absent required mappings or unknown claims produce BLOCKED. |
| REQ-005 | Persist a validation plan bound to SPEC revision/hash and relevant project/policy hashes. Map each AC to affected contract, rule IDs, required layers, scenario IDs, evidence requirements and non-applicability rationale. Bind evidence to the relevant build/profile/scenario where required. Reload invalidates derived verdicts when relevant inputs change, while retaining historical evidence and settled user decisions. Unchanged reload does not create a new authorization requirement. |
| REQ-006 | Keep planning readiness, implementation checks, runtime acceptance and release acceptance distinct. Before relevant product edits require valid planning and existing enablement prerequisites. Missing final runtime evidence alone must not prevent authorized work needed to produce that evidence. Missing capability or device permission never becomes an exemption or automatic flash authorization. |
| REQ-007 | Before recording AC PASS, marking implemented, or reporting overall acceptance, run a shared evidence-authority assessment. Host/fake/build/AST/smoke evidence cannot satisfy a claim owned by HIL or final acceptance. Reuse existing layer authority and FAIL > BLOCKED > PASS semantics. Missing or stale evidence is BLOCKED; observed criterion violations are FAIL. Preserve valid host PASS results separately. |
| REQ-008 | Apply the same assessment through managed delivery completion, spec evidence/status updates and code-review Spec-axis instructions. Reject incompatible PASS updates, including a confirmed SPEC whose evidence is rewritten without changing status to implemented. Do not rely on parsing a free-text PASS word as evidence. |
| REQ-009 | Legacy project/runtime records may be read but cannot silently supply missing validation authority. Reconstruct a valid plan from supported current inputs; report actionable missing fields when reconstruction is impossible. Explicitly non-applicable host-only projects remain usable without a device profile. |
| REQ-010 | Add regression fixtures, schema tests, existing-suite regression, architecture checks, deterministic generated-view comparison and distribution validation. Document limits: executable gates enforce managed entrypoints; they cannot intercept arbitrary model prose or ungoverned filesystem writes. |

## Decisions

| ID | Decision | Rationale |
|---|---|---|
| DEC-001 | Modify only skill workflows. | User selected option 2. |
| DEC-002 | Recommend structured project-context enforcement plus completion checks. | Instructions alone permit the observed omission; forcing HIL everywhere contradicts lowest-sufficient-layer policy. |
| DEC-003 | Retain existing verification-layer authority and device runner ownership. | Avoid duplicated rules and incompatible evidence verdicts. |

## Discussion Context

### DISC-001: Scope

- **Situation:** Options were skill plus firmware, skill only, or firmware only.
- **Question:** Which modification scope should the proposal cover?
- **Options and tradeoffs:** Combined scope repairs this incident and shared workflow; skills only prevents recurrence; firmware only repairs this incident.
- **User answer:** 2。我有在那個任務說重新載入技能。為什麼沒有對專案的硬體驗證要求
- **Explicit rationale:** No separate user rationale was supplied.
- **Resulting impact:** REQ-001 limits scope to skills; REQ-002 and REQ-005 explicitly cover reload.

### DISC-002: Proposal request

- **Situation:** The user has selected skill-only scope and asks for the concrete proposal.
- **Question:** What deliverable is requested now?
- **Options and tradeoffs:** The user directly requests a proposal; implementation is a subsequent authorized phase.
- **User answer:** 提出修改方案
- **Explicit rationale:** No additional rationale provided.
- **Resulting impact:** DEC-002 recommends structured enforcement; REQ-001 excludes firmware work and publication. No product execution authorization has been given.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Product diff stays within skill repository; no firmware mutation, device operation, installation or publication. | Diff and operation audit. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-002 | REQ-002, REQ-003 | Fixture with required runtime policy and applicable physical claim retains required validation on 開始執行, 繼續 and 重新載入技能 even without hardware keywords. | Router integration tests against real production routing code. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-003 | REQ-004, REQ-009 | Missing required matrix, invalid reference or unknown claim is BLOCKED; valid explicit host-only rationale selects no device layer. | Positive and negative project fixtures. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-004 | REQ-005 | Relevant SPEC/policy/profile/build changes reject stale plan/evidence bindings; unchanged reload preserves valid bindings and authorization state. | Hash mutation and continuity tests. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-005 | REQ-006 | Planning/enablement readiness admits appropriately authorized implementation while absent final HIL evidence blocks overall acceptance; missing device permission does not authorize device actions. | Lifecycle transition tests. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-006 | REQ-007, REQ-008 | Host-only evidence for physical AC fails acceptance; partial HIL, stale HIL and smoke-only evidence are BLOCKED; complete matching evidence passes; proven violations remain FAIL. | Evidence-authority table tests and managed completion integration tests. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-007 | REQ-008 | Both implemented status updates and confirmed SPEC evidence-only PASS updates reject insufficient evidence. Review and final-result instructions distinguish partial results. | Spec lifecycle bypass regressions plus instruction contract tests. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |
| AC-008 | REQ-009, REQ-010 | Existing valid host workflows retain behavior; supported legacy records migrate/recompute explicitly; all required suite/schema/architecture/distribution checks pass. | Repository test runners and public governance/distribution CLIs. | PASS: [verification report](../validation/spec0027-report.md); [bound evidence](../validation/evidence-SPEC-0027.json) |

## Recommended implementation

1. Add a demand-owned normalized validation-context contract and repository reader. Extend guided routing and risk inputs while retaining independent prompt-only classification as non-authoritative for governed project completion.
2. Coordinate verification-ladder planning through the existing governance domain. Persist plan bindings with task/SPEC lifecycle state and refresh them on reload/resume.
3. Add a shared completion assessment to delivery orchestration and SPEC evidence recording. Keep format validity separate from semantic evidence sufficiency.
4. Synchronize ask-matt, engineering-risk-routing, verification-ladder, validate-on-device, implement, spec-governance and code-review instructions, their docs and architecture views. Add executable negative regressions before changing implementation.

## Alternatives and tradeoffs

| Candidate | Benefit | Cost/risk | Assessment |
|---|---|---|---|
| Add reminder text only | Small documentation change. | No deterministic protection from short-prompt routing or invalid PASS. | Insufficient. |
| Require HIL for every embedded edit | Simple blanket policy. | Unnecessary device work; violates selective-layer contract. | Reject. |
| Structured project context plus shared completion checks | Traceable decisions and testable enforcement at actual state transitions. | More schema/compatibility work; legacy missing mappings become visible blockers. | Recommend. |

## Architecture impact

The L0 guided_workflow_router coordinates risk_routing_domain, governance_workflow_domain and delivery_workflow_domain; repository_evidence_adapter supplies filesystem facts through demand-owned contracts. verification_ladder_domain remains the semantic owner for selection and evidence authority. SPEC lifecycle state remains with its existing owner. No sibling imports, duplicate rule engines, new background service, threads or runtime scheduling change are proposed. Extend manifest Port/type/state catalogs and generated System/Parent/Flow views for the added context, plan and completion results. No architecture exception is requested.

## Algorithm impact

Project evidence collection is bounded parsing/hashing without an independent product algorithm. Additive gate selection and evidence-authority aggregation affect observable decisions and must update ALG-0001 and ALG-0007 under their existing owners. Reuse deterministic union, canonical ordering and existing verdict precedence. Unknown/missing inputs must not downgrade risk. Acceptance is exact fixture verdicts with zero unauthorized lower-layer substitutions; no statistical or device performance claim is introduced.

## Flow and execution impact

As-is: prompt -> classifier -> selected workflow, with manual project-policy reconciliation. Proposed: project/SPEC facts -> additive assessment -> bound plan -> selected workflow -> evidence-authority completion -> SPEC/result. Filesystem failures return structured blockers before dependent state mutation. Relevant document hashes require fresh reads; avoid unrelated tree scans, network access or device probes during routing. Execution cost is unmeasured and no speed or real-time claim is made. This is a host governance change, validated with production Python code and fixtures; device HIL is not needed merely to test a HIL-selection rule.

Adding a project policy source should affect the repository reader and normalized contract; adding a layer rule should remain in verification_ladder_domain; adding a completion consumer should use the same public assessment. Include Windows/Linux compatibility in existing supported checks. Render changed architecture views through the public architecture CLI and validate the Python analyzer.

## Relationships

- refines: SPEC-0018

## Out of Scope

- Firmware changes or remediation of env_sensing validation artifacts.
- Physical device tests, firmware upload/reset, plugin installation/publication.
- Blanket HIL, new performance thresholds, automatic acceptance exceptions.
- Host-wide interception or guarantees about arbitrary assistant prose outside managed tools.

## Open Decisions

None.

## Routing/Gates
Spec review: PASS

Require SPEC verification, formatter governance, architecture design/development gates with Python analyzer and deterministic generated views, targeted TDD and existing regression, dual-axis code review and distribution validation. This change's verification is host-based production-code execution with fixtures. Reuse existing device validation runner for future projects selected for device layers; this proposal does not run it against hardware.

## Revision History

| Revision | Date | Summary |
|---|---|---|
| 1 | 2026-09-16 | Propose project-policy-aware routing, reload reconciliation and evidence-authority completion for the skill-only scope. |
| 2 | 2026-09-16 | Reconcile the user's skill-only selection and request for a concrete proposal; no unresolved scope decisions. |
| 4 | 2026-09-16 | Recorded implementation PASS evidence. |
