# ADR-0002: Four validation gates and explicit profile completion

- Status: proposed
- Date: 2026-07-22
- Approver: pending
- Approval reference: pending

## Context

The former profile allowed an implicit 30-second scenario window and author-supplied minimum sample counts. A plan could therefore treat one bounded capture as complete acceptance without proving validation capability, per-change checks, flow completion, statistical sufficiency, or release-image hygiene. Supported operating-system resource criteria could also appear to pass through structured application logs when native evidence was unavailable. The first four-gate implementation accepted a shallow Gate 1 summary and did not prove that every change group had risks, host-side checks, hashed artifacts, external-Port contract coverage, or a justified smoke decision.

## Decision

- Require four gates in improvement proposals: Validation Enablement, Per-change Development Validation, Final Runtime Acceptance, and Release Acceptance.
- Require every runtime scenario to declare `phase`, `evidence_mode`, `max_duration_ms`, completion criteria, and enablement prerequisites where applicable.
- Require statistical and native criteria to use a deterministic calculated sample plan or a stable external-standard reference.
- Require native evidence for Windows, Linux, and iOS scheduler/resource criteria; structured logs remain authoritative only for domain semantics and bare-metal/custom statistics.
- Keep ordinary unit, Fake Port, and host integration tests outside the runtime runner. Their native test framework owns assertions and exit codes; no flash, runtime capture, user log upload, or GPT log interpretation is required.
- Replace the shallow Gate 1 summary with structured change groups containing architecture references, risks, reproducible commands, exit codes, verdicts, hashed artifacts, and explicit smoke decisions.
- Recompute Gate 1 in the runner. Require demand-owned contract tests when governed external Ports or L3+ Adapters change, and match required smoke to a declared profile scenario and profile hash.
- Replace profile v1.0 in place. Do not accept the previous implicit scenario contract.

## Alternatives considered

- Preserve the old profile and add optional fields: rejected because incomplete profiles could still produce ambiguous acceptance.
- Apply a universal 30-second window: rejected because low-frequency flows and high-frequency statistics have different completion conditions.
- Let all resource criteria fall back to application logs: rejected because application events do not prove OS scheduling or resource behavior.
- Execute all development tests through the on-device runner: rejected because it couples host-side feedback to runtime collection and obscures the boundary between Gate 1 and Gate 2.
- Keep accepting one opaque Gate 1 evidence path: rejected because it cannot prove per-change coverage or prevent an author-supplied PASS from masking missing checks.

## Benefits, costs, and tradeoffs

The change makes flow completion, sample sufficiency, gate ownership, per-change development coverage, and evidence authority machine-checkable. It increases profile and Gate 1 result authoring work and intentionally invalidates the shallow development-gate document. Native tooling may require permissions and can leave a criterion BLOCKED when unavailable.

## Risks and mitigations

- Formula support is intentionally limited to proportion, mean, and DKW distribution bounds; specialized methods use an external standard reference.
- Acceptance bundles bind prerequisite results to the same profile hash so stale enablement evidence cannot pass the gate.
- Scenario and transport limits remain bounded independently so completion-driven capture cannot run indefinitely.
- Release acceptance remains separate from runtime tooling so a validation image cannot be mistaken for a release artifact.
- A target architecture manifest identifies L3+ Adapters and their implemented Ports; referenced external boundaries require `port-contract` evidence.
- Required smoke remains a separate runtime result bound to the same profile and supports Gate 1 without satisfying Gate 2.

## Compatibility and migration

Existing profile v1.0 files must be rewritten with explicit scenario phase, evidence mode, maximum duration, completion IDs, prerequisites, and sample plans. Gate 1 summary documents must be rewritten to the structured development-gate schema. There is no legacy parser or automatic migration.

## Validation

Pass profile-schema tests, structured development-gate and smoke-matching tests, external-Port contract tests, flow PASS/FAIL/BLOCKED fixtures, sample-plan formula tests, enablement prerequisite tests, native-correlation tests, guided-session regression, skill validation, architecture checking, and deterministic renderer checking.

## Approval

This ADR remains proposed. A human approver, approval date, and external approval reference are required before changing the status to accepted.
