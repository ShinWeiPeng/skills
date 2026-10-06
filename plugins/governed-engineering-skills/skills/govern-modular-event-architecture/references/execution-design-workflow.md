# Platform execution efficiency governance

Optimize useful work per unit of CPU, memory, bandwidth, and energy while preserving correctness, reliability, and timing contracts. Logical Modules and runtime Execution Units are independent views: never infer one Task or Thread per Module.

## Required workflow

1. Confirm the target platform, CPU, runtime, compiler, cache topology, and scheduler capabilities with a human. Logical architecture may continue while these are unknown; execution, cache, branch, and platform-efficiency decisions remain `BLOCKED`.
2. Define Flow workloads and classify them as `hard-real-time`, `soft-real-time`, or `best-effort`.
3. Establish an as-is `legacy-review` profile and runtime baseline for implemented projects. New projects start with a portable `proposed` profile.
4. Compare Execution Unit, Channel, data-layout, and microarchitecture candidates. Do not use Task count or average CPU utilization as a proxy for efficiency.
5. Require human approval metadata before a profile becomes `accepted`. Release variants reference only accepted profiles.

For every hard/soft real-time workload, also apply
[workload-driven scheduling analysis](realtime-scheduling-analysis.md). Task
count, activation rate, priority, scheduler method, and core allocation are
pre-code design decisions: compare at least two candidates, generate the
human-readable study report, and obtain human selection. Use RMA/RTA only for a
compatible RM fixed-priority scheduler.

## Optimization tiers

### Tier 0: safe defaults

Apply [EXEC-OPT-001 and EXEC-OPT-002](../../coding-standards/rules/execution-and-platform.md).

### Tier 1: design cost analysis

Every hard-real-time workload records working-set/reuse-distance, memory traffic/arithmetic intensity, branch frequency and predictability, SIMD/data dependencies, Amdahl/parallelism/false sharing, and allocation/locking/queue/blocking bounds.

Every hard/soft real-time workload additionally records periodic, sporadic, or
Server activation; WCET source; deadline; release jitter; blocking; scheduler
and interrupt overheads; Queue/notification cost; core assignment; and
end-to-end Flow chains. Missing or average-only interference bounds are
`BLOCKED`. Hard misses fail; soft misses become `SOFT_RISK` and require an SLO
plan plus final percentile/miss-rate evidence.

Soft-real-time and best-effort workloads enter Tier 1 only when a prototype misses a declared budget or evidence identifies cache, branch, stall, bandwidth, allocation, or synchronization risk.

### Tier 2: platform specialization

Keep a correct portable baseline. Use representative data and the release compiler/build composition. Compare neighboring tile, array, queue, or batch candidates and record cycles, instructions, cache/branch misses, latency, throughput, memory, binary size, and power. Fixed selected parameters belong to the platform variant; startup auto-tuning is not the default.

## Data and branch planning

Plan the active working set, not total dataset size:

```text
active_working_set = live inputs + outputs + intermediate data + indexes/metadata
```

Declare element size, layout, stride, reuse, alignment, sharing, cache target, and candidates. Reserve cache headroom for other resident data and associativity conflicts; never equate usable capacity with nominal cache size.

For hot branches, record representative condition distributions and compare the original branch with grouping, lookup, conditional move, masks/SIMD, or branchless alternatives. Branchless code is not inherently faster because it may execute both paths or lengthen dependency chains.

## Runtime acceptance

Use [runtime checks](runtime-checks.md).


## OS planning

Read [platform format](platform-design-format.md), [execution format](execution-design-format.md) and [OS checks](os-execution-checks.md). Preserve the confirmed OS; compare bare metal, RTOS and general OS only while selection is open. Present all nine applicability decisions before SPEC confirmation. Default to processing-stage execution units with bounded OS channels; proposed merges need workload analysis, handoff/buffering/lifecycle cost and human selection. Keep modules distinct from Tasks. Existing hard/soft real-time obligations, supported scheduling analysis and at least two candidates remain required. Apply the seven conditional OS rules; separate design feasibility, implementation conformance and acceptance evidence.
