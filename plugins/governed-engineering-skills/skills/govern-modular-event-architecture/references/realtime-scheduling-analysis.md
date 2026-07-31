# Workload-driven real-time scheduling analysis

Use this reference whenever a workload is classified `hard-real-time` or
`soft-real-time`. Timing class triggers the scheduling study. The execution
model (`rtos`, `bare-metal`, or `os`) does not. Scheduler compatibility selects
the analysis method.

RTOS use alone does not trigger a scheduling study.

## Design gate

Complete this gate before editing product source:

1. Confirm the CPU/core topology, execution model, scheduler capabilities,
   preemption, priority direction, timer resolution, synchronization protocol,
   interrupt behavior, and migration policy.
2. Derive activation constraints from Flow deadlines, sampling/control rates,
   freshness, throughput, minimum event inter-arrival, and burst bounds.
3. Map every hard/soft workload to candidate execution profiles. Inventory
   every Task, interrupt, Queue, notification, lock, and best-effort activity
   sharing those profiles because all interference must be bounded.
4. Produce at least two structurally different candidates. Change Task
   grouping, activation rate, core allocation, or communication topology;
   renamed copies are not alternatives.
5. Select `analysis_method`. Schema 2.1.0 installs only
   `rate-monotonic-rta`. An EDF, cyclic-executive, global-FP, or other method is
   `BLOCKED` until a proposed ALG, analyzer, schema contract, and tests exist.
6. Run provisional analysis with conservative design budgets, generate the
   human-readable report, and obtain non-AI selection.
7. Implement only after the selected design gate passes. Replace budgets with
   measured/static-analysis bounds and bind final runtime evidence.

RMA compares candidate decompositions; it does not invent Task count or rates.

## Workload coverage and criticality

`realtime_scheduling_studies` is driven by execution mappings:

- every `(hard-or-soft workload, candidate profile)` pair belongs to exactly
  one study;
- every candidate maps every `workload_refs` entry;
- `flow_refs` exactly matches the Flows owned by those workloads;
- unrelated best-effort profiles need no study;
- all Tasks, interrupts, and Channels in a studied profile remain in the
  interference model, including best-effort work.

Task criticality is the strictest timing class among its demand-component
mappings. Flow criticality is the strictest mapped workload for that Flow:

```text
hard-real-time > soft-real-time > best-effort
```

## Supported Rate Monotonic model

`analysis_method: rate-monotonic-rta` requires partitioned, fully preemptive, fixed-priority scheduling:

- bind each Task to exactly one core and forbid migration;
- order by effective period;
- break equal-rate ties by shorter relative deadline, then stable Task ID;
- keep OS priorities unique per core and consistent with numeric direction.

These rules apply independently of whether the runtime is an RTOS, bare metal,
or an operating system. Do not silently substitute Deadline Monotonic, EDF,
Audsley search, global scheduling, or a cyclic executive.

## Generic execution schema

Each analyzed `dedicated-task` declares `realtime_task`:

- `core`;
- periodic `period_ns`, sporadic `minimum_interarrival_ns`, or Server
  `server_type`, `budget_ns`, and `replenishment_period_ns`;
- `relative_deadline_ns`, `release_jitter_ns`, and `blocking_ns`;
- exactly-once `demand_components`.

Provisional components use `budget_ns`. Final components use `final_ns`,
`basis: measured|static-analysis`, `evidence_path`, and `evidence_sha256`.

Each `interrupt` declares `interrupt_interference.core`, `wcet_ns`,
`minimum_interarrival_ns`, and `release_jitter_ns`. An interrupt is not a Task
and does not enter RM ordering, but it interferes with every Task on its core.

Each analyzed Channel declares `realtime_timing` with notification latency,
consumer jitter, copy cost, cross-core status, and exact source/target CPU-cost
accounting. Accounting must equal copy cost exactly.

Profile overheads include `context_switch_ns`, `dispatch_ns`,
`preemption_ns`, and `timer_interrupt_ns`. All canonical time values are
non-negative integer nanoseconds.

The pre-release fields `rtos_design_studies`, `rtos`, `rtos_isr`,
`rtos_timing`, and `timer_isr_ns` are obsolete and configuration `BLOCKED`.
Schema 2.1.0 performs no inference or migration.

## RMA screen and RTA

Compute exact rational utilization per core:

```text
U = sum(C_i / T_i)
```

The Liu-Layland bound is an early sufficient screen. Exceeding it is
`INCONCLUSIVE`, never an automatic failure.

For each Task, compute a level-i busy period and every job response needed for
arbitrary deadlines:

```text
w_i(q) =
  B_i + (q + 1) C_i
  + sum over h in hp(i) of
      ceil((w_i(q) + J_h) / T_h) * (C_h + P_h)

R_i(q) = w_i(q) - q T_i + J_i
R_i = max_q R_i(q)
```

`C` includes demand and per-job overhead, `B` blocking, `J` release jitter, and
`P` preemption cost. Missing bounds or non-convergence are `BLOCKED`.

The conservative Flow bound is:

```text
sum(Task response bounds)
+ sum(Channel notification latency and release jitter)
```

Copy CPU cost is already charged to Tasks and is not added twice.

## Hard and soft verdict policy

The analyzer keeps the gate verdict `PASS`, `FAIL`, or `BLOCKED` and reports a
per-Task/per-Flow `rta_verdict`:

- hard deadline miss: `FAIL`;
- soft deadline miss: `SOFT_RISK`;
- best-effort deadline miss: `INFO`;
- valid bound within deadline: `PASS`;
- missing/invalid/non-convergent input: `BLOCKED`.

A selected hard candidate must have no hard miss. Every soft study workload
requires the following pre-code acceptance plan; a provisional soft-only
candidate may then carry `SOFT_RISK`:

- existing percentile and deadline-miss-rate budgets;
- a `soft_acceptance_plans` entry with validation-plan path and evidence
  format;
- non-AI `risk_approval`.

Final acceptance always requires `soft_slo_results` with `verdict: pass` for
every selected soft workload, plus evidence path/SHA-256 and selected
profile/manifest hash binding. RTA remains visible as worst-case risk; the
declared percentile and miss-rate SLO owns the soft product verdict.

## Human-readable report

Render
`architecture/generated/realtime-study-<study-id>.md` for every study. It
contains:

- workload timing classes, analysis method, execution model, scheduler
  compatibility, requirements, and assumptions;
- candidate Task count, rates, core mapping, utilization, and tradeoffs;
- per-core RM ordering and interrupt interference;
- per-Task criticality, demand, blocking, jitter, response, deadline, and
  `rta_verdict`;
- Channel, synchronization, notification, and cross-core costs;
- Flow criticality, end-to-end bounds, hard failures, and soft risks;
- WCET evidence, soft SLO plans/results, runtime bindings, decisions, and
  human approvals.

The report follows `project.documentation_language`, begins with the generated
marker, and is read-only. `architecture_cli.py gate --phase development|release` rejects missing,
changed, stale, or obsolete reports.

## Runtime and release acceptance

Final accepted profiles require complete WCET evidence, runtime evidence bound
to selected profile and manifest hashes, hard Task/Flow PASS, soft SLO PASS,
and non-AI final approval. Physical and OS-native evidence routes through
`$validate-on-device`; this host-side governance implementation itself does not
require on-device smoke.
