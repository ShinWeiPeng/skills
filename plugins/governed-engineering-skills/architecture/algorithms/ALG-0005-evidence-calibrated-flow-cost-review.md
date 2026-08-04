# ALG-0005: Evidence-calibrated Flow cost review

## Metadata

- Status: proposed
- Owner module: `governance_workflow_domain`
- Product feature: Flow cost review and model assurance
- Flow IDs: `governed-change-set-lifecycle`
- Related ADRs: none
- Source paths:
  - `skills/govern-modular-event-architecture/references/flow-cost-review.md`
  - `skills/improve-codebase-architecture/SKILL.md`
  - `skills/clarify-improvement-proposals/SKILL.md`
- Test and benchmark paths:
  - `tests/test_flow_cost_governance.py`
- Supersedes: none

## Problem and observable success

Architecture recommendations can preserve inherited orchestration or call a
candidate faster, maintainable, extensible, stack-safe, or real-time-ready
without proving the execution paths and evidence behind those claims. Success
means every material recommendation exposes its admission constraints,
execution model, evolution scenarios, assurance status, missing evidence, and
tradeoffs, and refuses unsupported winner or real-time claims.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are repository evidence, product scenarios, as-is and target Flows,
platform/toolchain facts, workload timing classes, budgets, static cost models,
benchmarks, runtime evidence, and change scenarios. Units come from the target
contract and are never inferred across RTOS/framework versions. Missing values
remain missing rather than becoming zero.

The output is a directional or confirmed recommendation with:

- functional-admission verdict;
- execution and real-time constraint results;
- maintainability/extensibility comparison;
- `estimated`, `calibrated`, `validated`, or `BLOCKED` model assurance;
- constraint failures, Pareto tradeoffs, and evidence gaps.

Evidence is trustworthy only when its build, target, scenario, trigger,
observation window, and units match the claim.

## Constraints and quantitative acceptance thresholds

- A hard functional, deadline, or resource constraint cannot be traded away.
- Hard/soft real-time evidence follows the existing workload-driven scheduling
  and runtime-acceptance contracts.
- Every budget and reserve names a product, standard, platform, baseline, or
  human-confirmed source.
- No universal stack margin, utilization threshold, deadline, SLO, or weighted
  score is permitted.
- Contract tests cover every normative fail-closed fixture and entry skill.

## Candidate methods and comparative evidence

1. **Functional checklist only:** rejected because it cannot compare execution
   speed, real-time feasibility, or evolution cost.
2. **Universal weighted score:** rejected because a favorable maintainability
   score could hide a deadline miss and arbitrary weights would invent product
   priorities.
3. **Benchmark every Flow:** rejected because Greenfield and ordinary
   best-effort work would be blocked even when measurement cannot change the
   decision.
4. **Tiered evidence with constraint filtering and Pareto comparison:**
   selected because it preserves hard constraints, escalates evidence when
   decision-relevant, and exposes rather than erases tradeoffs.

## Selected method and reasons for rejecting alternatives

Evaluate four dimensions in order: functional admission, execution/real-time
feasibility, maintainability/extensibility, and model assurance. Filter hard
failures, retain explicit soft risks only through existing policy, mark missing
load-bearing evidence `BLOCKED`, then compare surviving candidates on a Pareto
front. Require static cost models for all material Flows and quantitative
evidence when timing/resource triggers can change the recommendation.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

```text
for candidate in structurally_distinct_candidates:
    if functional_admission_fails(candidate):
        reject(candidate)
    cost = build_static_cost_model(candidate)
    if quantitative_evidence_triggered(candidate):
        cost = calibrate_or_block(cost)
    if hard_constraint_fails(cost):
        reject(candidate)
    evolution = evaluate_change_scenarios(candidate)
    assurance = classify_assurance(cost)

survivors = non_rejected_candidates
if any survivor has load_bearing_BLOCKED_evidence:
    publish directional comparison; do not publish a winner
else:
    publish Pareto comparison and explain the selected tradeoff
```

There is no numeric tie-breaker. The human-confirmed product constraints and
tradeoff preference select among non-dominated candidates.

## Parameters, calibration, versioning, and compatibility

Project-owned budgets, reserves, scenarios, and target/toolchain versions are
inputs, not algorithm defaults. Existing external wire, storage, ABI, and
ordering contracts remain constraints; internal orchestration is independently
reviewable. This feature adds no manifest schema or public CLI.

## Time and space complexity and resource budgets

The prompt workflow is proportional to the number of reviewed candidates,
Flow steps, evidence rows, and change scenarios. It creates no product runtime
state. Target-product execution costs are analyzed by the owning project and
existing architecture/runtime tools.

## Errors, degradation, fallback, and forbidden behavior

- Missing load-bearing evidence yields `BLOCKED`, not PASS or FAIL.
- An estimated model may support direction but not a platform winner.
- High-water evidence never proves an unexecuted path.
- Average-only evidence never proves real-time acceptance.
- Static and runtime evidence cross-check; neither erases a disagreement.
- Do not invent missing values, units, thresholds, reserves, or approvals.

## Validation cases and evidence

- Existing Register-style hidden callback re-entry.
- Stack API unit ambiguity across pinned runtime versions.
- Healthy high-water with an uncovered error/retry path.
- Debug/release build mismatch.
- Observed cost exceeding prediction without reconciled reserve.
- Average-only real-time evidence.
- Best-effort benchmark trigger with only a static estimate.
- Greenfield portable estimate before platform selection.
- Change scenarios for a source, subscriber, adapter, processing stage, and
  platform variant.

The executable contract is
`python -m unittest tests.test_flow_cost_governance -v`; the full suite,
integration validation, architecture gate, deterministic renderer, vendor lock,
and version governance provide regression evidence.

## Risks and monitoring

The contract adds analysis cost and can leave more recommendations BLOCKED.
Monitor false blocking, repeated missing-evidence categories, report size, and
whether users can trace each verdict to a requirement or evidence source.
Refine trigger wording rather than weakening fail-closed semantics.

## Human approval

Pending. Codex must not mark this record accepted or invent approval metadata.
