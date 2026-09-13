# ALG-0002: Partitioned Rate Monotonic and response-time analysis

## Metadata

- Status: proposed
- Owner module: `realtime_schedulability_analysis`
- Product feature: Workload-driven real-time Task-set design and schedulability validation
- Flow IDs: `validate-architecture`
- Related ADRs: `ADR-0005`
- Source paths: `scripts/realtime_analysis.py`, `scripts/schema_v2.py`, `scripts/render_architecture.py`
- Test and benchmark paths: `tests/test_realtime_analysis.py`, `tests/test_architecture.py`
- Supersedes: none

## Problem and observable success

Select Task count, activation rates, priorities, and core allocation for every
hard/soft workload before product implementation, then apply an analysis method
compatible with the declared scheduler. Success means all interference is
bounded, hard deadlines pass RTA, soft misses are explicit risks with SLO
plans/evidence, and a deterministic Markdown report is reviewable.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are schema 2.1.0 workload timing classes, execution profiles, dedicated Tasks, mappings, Channels,
Flow chains, nonnegative integer nanosecond bounds, and approval/evidence
metadata. Provisional demand uses design budgets. Final demand uses measured or
static-analysis values with evidence references. Outputs are per-core RM order,
utilization screens, Task response bounds, Flow bounds, candidate fingerprints,
PASS/FAIL/BLOCKED gate verdicts, per-item PASS/FAIL/SOFT_RISK/INFO/BLOCKED RTA verdicts, and generated Markdown.

## Constraints and quantitative acceptance thresholds

Scheduling is partitioned, fully preemptive, fixed-priority, and migration-free.
Every Task belongs to one core. OS priorities are unique per core and preserve
RM order. Hard Task/Flow misses fail; soft misses are risks governed by
percentile and miss-rate SLOs. Missing bounds, invalid accounting, or
non-convergence is `BLOCKED`.

## Candidate methods and comparative evidence

- Liu-Layland utilization is a cheap sufficient screen but rejects some
  schedulable Task sets.
- Single-job constrained-deadline RTA is simpler but invalid for arbitrary
  deadlines.
- Level-i busy-period arbitrary-deadline RTA is deterministic, exact for the
  supported fixed-priority model, and supports all declared deadlines.
- Simulation and runtime traces are valuable evidence but cannot prove every
  worst-case phasing.

## Selected method and reasons for rejecting alternatives

Use utilization only as an `INCONCLUSIVE` screen and use level-i busy-period,
multi-job fixed-point RTA as the authoritative verdict. Compute each core
independently. Add declared Channel CPU costs to endpoint Tasks, and add Channel
notification latency and release jitter to conservative ordered Flow bounds.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. Derive effective period from periodic period, sporadic minimum inter-arrival
   time, or Server replenishment period.
2. Sort each core by `(effective period, relative deadline, stable Task ID)`.
3. Validate the concrete OS priority order against that logical order.
4. Compute the level-i busy period for each Task.
5. For each job `q` in the busy period, iterate:

```text
w_i(q) =
  B_i + (q + 1) C_i
  + sum(h in hp(i)) ceil((w_i(q) + J_h) / T_h) * (C_h + P_h)

R_i(q) = w_i(q) - q T_i + J_i
R_i = max_q R_i(q)
```

6. Classify `R_i > D_i` as hard `FAIL`, soft `SOFT_RISK`, or best-effort
   `INFO` from workload mappings.
7. Compute a Flow bound as the sum of ordered Task response bounds plus Channel
   notification and release-jitter bounds. Copy CPU time is already charged to
   Tasks and is not double-counted.
8. Fingerprint candidate grouping, rates, cores, and communication topology;
   reject duplicate candidates.
9. Render inputs, comparisons, results, rationale, and approval as generated
   Markdown.

## Parameters, calibration, versioning, and compatibility

Canonical time is integer nanoseconds. Fixed-point iteration is capped at
10,000 steps; hitting the cap is `BLOCKED`. Schema 2.0.2 is not migrated or
reinterpreted. Supporting global scheduling, migration, EDF, or a different
priority assignment requires a new proposed algorithm record.

## Time and space complexity and resource budgets

RM sorting is `O(n log n)` per core. RTA cost is bounded by Task count, jobs in
the level-i busy period, higher-priority Task count, and the fixed iteration
cap. Candidate and report generation are linear in declared profiles, Tasks,
Channels, and Flow chains after RTA.

## Errors, degradation, fallback, and forbidden behavior

Do not guess a period, WCET, blocking, jitter, interrupt cost, or cross-core cost. Do
not substitute average event rate for a minimum inter-arrival bound. Do not
silently change priority assignment when RM fails. Do not run RMA for an
incompatible scheduler. Do not accept a hard miss or a soft risk without its
required SLO plan, risk acceptance, and final evidence.

## Validation cases and evidence

Fixtures cover hard/soft non-RTOS triggering, best-effort RTOS exclusion,
mixed criticality, unsupported methods, periodic, sporadic, and Server activation; equal-rate
tie-breaking; single-core and partitioned multicore analysis; arbitrary
deadlines; blocking, jitter, context-switch, preemption, ISR, Queue, and
cross-core costs; utilization-bound inconclusive cases; Task and Flow misses;
invalid accounting; candidate uniqueness; human approval; provisional/final
evidence; deterministic reports; and stale-report rejection.

## Risks and monitoring

The conservative Flow sum may reject phase-aware pipelines that a holistic
analysis could prove. Such a case remains `BLOCKED` or `FAIL` under this model
until a reviewed algorithm extension is approved. Incorrect physical WCET or
jitter evidence can invalidate final RTA, so runtime evidence remains bound to
the selected profile and manifest.

## Human approval

Pending.
