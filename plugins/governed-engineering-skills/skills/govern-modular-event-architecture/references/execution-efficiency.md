# Platform execution efficiency governance

Optimize useful work per unit of CPU, memory, bandwidth, and energy while preserving correctness, reliability, and timing contracts. Logical Modules and runtime Execution Units are independent views: never infer one Task or Thread per Module.

## Required workflow

1. Confirm the target platform, CPU, runtime, compiler, cache topology, and scheduler capabilities with a human. Logical architecture may continue while these are unknown; execution, cache, branch, and platform-efficiency decisions remain `BLOCKED`.
2. Define Flow workloads and classify them as `hard-real-time`, `soft-real-time`, or `best-effort`.
3. Establish an as-is `legacy-review` profile and runtime baseline for implemented projects. New projects start with a portable `proposed` profile.
4. Compare Execution Unit, Channel, data-layout, and microarchitecture candidates. Do not use Task count or average CPU utilization as a proxy for efficiency.
5. Require human approval metadata before a profile becomes `accepted`. Release variants reference only accepted profiles.

## Optimization tiers

### Tier 0: safe defaults

After platform confirmation, prefer contiguous storage for sequential access, eliminate unnecessary allocation/copy/repeated traversal, hoist loop-invariant work, use natural alignment, keep batching within latency budgets, and declare ownership before shared writes.

Do not treat AoS/SoA conversion, cache-line padding, power-of-two buffers, branchless transforms, manual prefetch, lookup tables, SIMD intrinsics, PGO, LTO, or platform-specific flags as unconditional defaults.

### Tier 1: design cost analysis

Every hard-real-time workload records working-set/reuse-distance, memory traffic/arithmetic intensity, branch frequency and predictability, SIMD/data dependencies, Amdahl/parallelism/false sharing, and allocation/locking/queue/blocking bounds.

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

Meet Flow budgets first, then compare with the portable or as-is baseline. Do not regress another critical latency, jitter, memory, reliability, binary-size, or power criterion. A cache or branch improvement claim requires hardware counters or a declared equivalent; unavailable or invalid evidence is `BLOCKED`.
