# Evidence-calibrated Flow cost review

Use this contract before recommending a Flow-affecting architecture. Treat a
Flow as the ordered movement of data, control, state changes, and side effects
across Modules and runtime Execution Units.

## Four ordered dimensions

Evaluate each candidate in this order. A later advantage never cancels an
earlier hard failure.

### 1. Functional admission

Prove state invariants, semantic ownership, legal dependency direction, commit
before publication, declared ordering, bounded re-entry, and explicit failure
propagation. Separate external compatibility from internal orchestration:
wire, storage, ABI, and observable ordering constraints do not require retaining
callbacks, Tasks, Queues, or call topology.

### 2. Execution cost and real-time feasibility

Model the critical path and resource bottlenecks. Record applicable compute,
copy/serialization, Queue waiting, notification, context-switch, locking,
blocking, I/O, scheduler, interrupt, cache, bandwidth, memory, stack, power, and
retry costs. Relate every budget to a product requirement, external standard,
platform limit, measured baseline, or human-confirmed target. Never invent a
universal utilization threshold, stack margin, deadline, or SLO.

For hard/soft real-time workloads, apply `execution-efficiency.md` and
`realtime-scheduling-analysis.md`. Require WCET, relative deadline, release
jitter, blocking, Queue/notification cost, context-switch and preemption cost,
core allocation, and interrupt interference. Average-only evidence cannot
support a real-time PASS.

### 3. Maintainability and extensibility

Evaluate concrete change scenarios rather than subjective cleanliness. Include
project-relevant examples from:

- add a source;
- add a subscriber;
- add an adapter;
- add a processing stage;
- add a platform variant.

For each scenario, list affected Modules, interfaces, mappings, Flows, tests,
execution profiles, configuration, migration, and deployment artifacts. Prefer
the candidate that concentrates change at one semantic owner, preserves stable
interfaces and contract tests, avoids new sibling coupling, and increases
locality and leverage.

### 4. Model assurance

Assign exactly one assurance verdict:

- `estimated`: static derivation with explicit assumptions and no target
  calibration;
- `calibrated`: target measurement covers declared scenarios and records
  prediction error;
- `validated`: every acceptance scenario and reserve passes with
  release-equivalent evidence;
- `BLOCKED`: a load-bearing unit, path, platform fact, build composition,
  interference source, budget, reserve, trigger, observation window, or
  scenario is unresolved.

Do not rename `BLOCKED` to an estimate. A model may support directional
comparison while `estimated`, but it cannot establish a platform performance
winner or real-time PASS.

## Required Flow Review record

For every material as-is or candidate Flow, record:

| Field | Required content |
|---|---|
| Identity | Flow ID, trigger, timing class, candidate name, and owning L0/L1 Module |
| Ordered path | Module, Port/Event, execution context, sync/async delivery, state commit, side effects, and error path per step |
| Data | Semantic owner, representation, payload size/range, copies, lifetime, mutation authority, fan-out, and Queue capacity |
| Build | Target, CPU, ABI, RTOS/runtime/framework version, compiler, optimization, LTO, logging, and release composition |
| Budget | Metric, limit, units, source, applicable scenario, and required reserve/headroom |
| Prediction | Formula or derivation, predicted value/range, assumptions, and static-analysis evidence reference |
| Observation | Observed value/distribution, run and scenario identity, evidence reference, measurement overhead, and build/manifest binding |
| Assurance | Model verdict, prediction error, scenario coverage, uncovered risks, reserve source, and remediation |
| Evolution | Change-scenario matrix with affected artifacts, locality, leverage, compatibility, and migration cost |

Use the same units and grain for all candidates. Absence of a runtime
measurement is explicit; do not write a zero.

## Existing project and Greenfield entry

### Existing project

Reconstruct the actual as-is Flow from source, configuration, runtime state,
and production-equivalent evidence. Establish an as-is baseline before
describing a winner. Treat accepted ADRs and external contracts as constraints,
not proof that the internal Flow is good.

### Greenfield

Start from product scenarios and define end-to-end Flow before fixing Modules,
Ports, Events, Tasks, Queues, or platform specialization. Build a portable
estimate. If execution evidence can change the architecture choice, require a
bounded prototype or benchmark before selecting a platform winner.

Every Flow-affecting review compares at least two structurally different
candidates. Change execution grouping, communication topology, state/effect
sequencing, or another load-bearing structure; renamed copies are not
alternatives. A local refactor may mark Flow impact `N/A` only with a specific
reason supported by the traced call and dependency scope.

## Tiered evidence and benchmark triggers

Every material Flow gets a static cost model. Escalate to quantitative
prototype, benchmark, or runtime evidence when any of these can change the
recommendation:

- hard-real-time or soft-real-time timing;
- an explicit latency, throughput, memory, bandwidth, stack, power, or cost
  budget;
- high frequency, burst arrivals, large payloads, large fan-out, or repeated
  traversal;
- a new Task, Thread, core hop, Queue, copy, serialization, allocation, lock,
  retry, or blocking operation;
- an unbounded depth, capacity, lifetime, or interference source;
- a constrained platform resource or an as-is baseline close to its budget;
- batching, data layout, priority, affinity, scheduler, compiler, or algorithm
  changes;
- material disagreement or uncertainty in the static model.

If no trigger applies to a best-effort Flow, retain the static comparison and
state why stronger evidence is not decision-relevant.

## Stack model assurance

Bind a stack claim to target, CPU, ABI, RTOS, runtime/framework version,
compiler, optimization, LTO, logging, release composition, and API units.
Verify whether task creation and high-water APIs report bytes or words for the
actual pinned version.

Static analysis covers the maximum legal call chain, callback re-entry,
recursion bounds, indirect calls and function pointers, virtual dispatch,
library and error/logging paths, large locals, variable-length arrays,
`alloca`, TLS, and architecture-applicable interrupt/exception overhead. Any
unresolved load-bearing target is `BLOCKED`.

Target calibration uses a production-equivalent build and declared worst-case
scenarios. Record high-water, canary/guard verdict, overflow/reset/watchdog
patterns, nesting depth, payload/change count, and instrumentation overhead.
High-water proves only executed paths.

Use this relationship without claiming zero error:

```text
required_stack
= max(static_covered_bound,
      measured_peak + uncovered_path_delta)
+ explicit_uncertainty_reserve
```

The reserve source identifies compiler/library variation, uncovered-but-bounded
paths, release diagnostics, or another concrete uncertainty. A fixed generic
percentage is not evidence.

## Candidate selection

Apply constraint filtering first:

1. reject functional-admission failures;
2. reject hard deadline or hard resource-budget failures;
3. retain soft risks only through the existing quantified SLO and human-risk
   process;
4. mark missing load-bearing evidence `BLOCKED`.

Then present the surviving candidates as a Pareto comparison across latency,
throughput, jitter, CPU, memory, stack, bandwidth, power, reliability, change
surface, locality, leverage, compatibility, and migration cost. Do not combine
them into a universal weighted score. State the sacrificed qualities and the
evidence that makes the recommendation valid.

## Fail-closed fixtures

These fixtures are normative regression examples:

| Fixture | Evidence condition | Required verdict |
|---|---|---|
| `STACK-UNIT-AMBIGUITY` | Task stack or high-water API units are not verified for the pinned RTOS/framework version. | `BLOCKED` |
| `HIDDEN-REENTRY` | Static call depth omits an allowed `Execute -> callback -> Execute` path or unresolved indirect target. | `BLOCKED` |
| `SCENARIO-GAP` | High-water is healthy but a load-bearing error, retry, maximum-payload, or nested path did not execute. | `BLOCKED` |
| `BUILD-MISMATCH` | Measurement build differs materially in compiler flags, LTO, logging, library, or release composition. | `BLOCKED` |
| `PREDICTION-OVERRUN` | Observed cost exceeds prediction and the error plus reserve has not been reconciled. | `BLOCKED` |
| `MISSING-RESERVE-SOURCE` | A claimed resource reserve or headroom has no product, standard, platform, baseline, measured-variation, or human-confirmed source. | `BLOCKED` |
| `AVERAGE-ONLY-REALTIME` | A hard/soft real-time claim has averages but lacks the required worst-case bound or SLO evidence. | `BLOCKED` |
| `BEST-EFFORT-RISK` | A benchmark trigger can change the recommendation but only a static estimate exists. | `BLOCKED` |

Physical-device or OS-native calibration and acceptance route through
`validate-on-device`. A build, ordinary log, smoke test, or successful
functional test cannot substitute for the required runtime evidence.
