# execution-and-platform

| Rule ID | Strength | Applicable conditions | Program requirement |
|---|---|---|---|
| EXEC-OPT-001 | SHOULD | After platform confirmation; within latency, ownership and resource constraints. | After platform confirmation, prefer contiguous storage for sequential access, eliminate unnecessary allocation/copy/repeated traversal, hoist loop-invariant work, use natural alignment, keep batching within latency budgets, and declare ownership before shared writes. |
| EXEC-OPT-002 | MUST | Selecting platform optimizations. | Do not treat AoS/SoA conversion, cache-line padding, power-of-two buffers, branchless transforms, manual prefetch, lookup tables, SIMD intrinsics, PGO, LTO, or platform-specific flags as unconditional defaults. |
| EXEC-OBS-001 | MUST | High-frequency instrumentation where per-sample logging can perturb behavior. | Do not log every sample when logging can perturb behavior. Accumulate count, errors, drops, min, max, sum, sum of squares, and fixed histogram buckets without allocation. Emit snapshots from a bounded lower-priority context. Record counter saturation, dropped records, clock source, update cost, snapshot cost, critical-section cost, and bytes per second. |
