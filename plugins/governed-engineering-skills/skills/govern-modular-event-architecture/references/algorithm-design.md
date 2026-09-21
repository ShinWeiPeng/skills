# Product algorithm design governance

Use this process for deterministic algorithms, heuristics, statistical or
machine-learning methods, and third-party or standardized algorithms used by
product features.

## Two-stage screening

Record a screening result for every product feature. A feature requires a full
Algorithm Design Record when any condition is true:

- the method changes a user-observable result;
- it performs ranking, scoring, search, optimization, estimation, filtering,
  control, scheduling, inference, deduplication, or anomaly detection;
- correctness depends on probability, tolerance, or a data distribution;
- it uses thresholds, calibration, models, or tunable strategies;
- CPU, memory, latency, throughput, power, or real-time limits affect the
  feasible method;
- it selects Task grouping, scheduling, Queue capacity, data layout, tiling,
  branch strategy, SIMD/vectorization, PGO/LTO, load balancing, or fixed
  platform tuning parameters;
- it affects safety, security, privacy, fairness, or compliance; or
- it needs degradation, fallback, or failure behavior.

For a feature that triggers none of these conditions, record `not applicable`
and the reason in the proposal or inventory. Do not create an empty algorithm
record.

## Record location and lifecycle

Store each record at
`architecture/algorithms/ALG-####-<slug>.md`. The L1 or L2 functional module
that implements the method owns the record. Keep
`architecture/algorithms/README.md` as an inventory mapping product features
and owning module IDs to screening results and record paths.

Use these statuses:

- `legacy-review`: the algorithm already exists, but its evidence or human
  approval is incomplete;
- `proposed`: the design is complete enough for review but is not approved;
- `accepted`: a human product or technical owner approved it;
- `superseded`: a newer record replaces it.

An accepted record MUST name the human approver, approval date, and external
approval reference. Codex MUST NOT approve its own record or invent approval
metadata.

## Required record

Use this structure:

```markdown
# ALG-####: Descriptive algorithm name

## Metadata
- Status:
- Owner module:
- Product feature:
- Flow IDs:
- Related ADRs:
- Source paths:
- Test and benchmark paths:
- Supersedes:

## Problem and observable success
## Inputs, outputs, units, ranges, and data-quality assumptions
## Constraints and quantitative acceptance thresholds
## Candidate methods and comparative evidence
## Selected method and reasons for rejecting alternatives
## Exact behavior, formula or pseudocode, boundaries, and tie-breaking
## Parameters, calibration, versioning, and compatibility
## Time and space complexity and resource budgets
## Errors, degradation, fallback, and forbidden behavior
## Validation cases and evidence
## Risks and monitoring
## Human approval
```

The validation section includes applicable golden vectors, property tests,
boundary and fault cases, benchmarks, regression datasets, commands, expected
observable output, pass conditions, and evidence locations.

## Evidence proportional to risk

Begin with theoretical analysis, relevant standards, prior measurements, and
existing project evidence. Prototype or benchmark competing candidates before
selection when uncertainty is material, candidate differences affect an
acceptance threshold, or a resource budget is tight. A missing required
prototype, benchmark, dataset, or measurement leaves the decision unresolved;
do not call the proposal decision-complete.

Apply additional evidence by family:

- **Deterministic:** invariants, exact boundary behavior, deterministic
  tie-breaking, and worst-case time and space complexity.
- **Heuristic:** solution-quality bounds or empirical distribution, stop
  conditions, sensitivity to seeds or initial state, and adversarial cases.
- **Statistical or ML:** dataset provenance, train/validation/test separation,
  leakage controls, confidence or uncertainty, drift, bias, model and feature
  versions, and retraining or rollback policy.
- **Third-party or standardized:** standard or library version, configuration,
  conformance evidence, licensing and security constraints, and upgrade policy.

## Relationship to architecture

Schema 2.1.0/2.2.0 retains the execution-efficiency requirement to link the owning `ALG-####` to the applicable Workload, Execution Profile, Data Access Profile, Microarchitecture Profile, Real-time Scheduling Study, and Flow IDs. Scheduler and Task-set selection are algorithm-bearing and follow `realtime-scheduling-analysis.md`; RMA/RTA applies only to the supported RM fixed-priority method. Tier 2 requires a portable baseline, representative benchmark composition, neighboring parameter candidates, and full-Flow regression evidence.

Do not model private L2 algorithm steps as top-level end-to-end flows. Link the
record to the owning module and applicable L0/L1 Flow IDs instead.

If an algorithm decision changes public inputs or outputs, owned state, events,
errors, side effects, timing, resource contracts, module boundaries, or
dependency direction, update `architecture/manifest.yaml`, generated
Description Views, code, and tests in the same change. Create a separate
proposed ADR when the choice changes durable architecture, crosses module
boundaries, or requires a MUST-rule exception; cross-link the ADR and algorithm
record.

## Existing-project adoption

Inventory every L1 and L2 functional module and its product features. Create
records for all triggered algorithms. Mark already implemented algorithms
`legacy-review` when evidence or approval is incomplete; never relabel them
`accepted` without human approval.

New and changed algorithms comply immediately. Rank legacy gaps by safety,
user-visible product impact, data uncertainty, and resource risk, then
remediate them in stages until each record is supported and reviewed.
