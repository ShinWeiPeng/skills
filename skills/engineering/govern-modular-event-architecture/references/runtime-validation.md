# Runtime validation architecture

Apply this reference when a change needs physical-device evidence, operating-system scheduling/resource evidence, test-only commands, runtime trace adapters, or high-frequency statistics.

## Boundaries

- Keep native trace, Serial, TCP, test logging, statistics export, clocks, process execution, and evidence storage in L3+ adapters.
- Let the demand-side L0-L2 module own the observability or test-control port. Do not let a functional module depend on ETW, perf, Instruments, Serial, TCP, a logger, or a concrete test framework.
- Wire test-only adapters in a test composition root. Release composition roots must not include test command parsers or test protocol wiring.
- Prefer observation at task, Port, and Event boundaries. If a hot internal path needs instrumentation, use a demand-owned metrics port or compile-time test hook whose release wiring is absent.
- Model guided user action as an external adapter interaction and preserve actor/source in evidence.
- Use guided forms to collect ordered user facts and generate summary tables only as read-only projections. The verdict domain must not trust an edited table or a user-supplied PASS/FAIL value. Preserve the immutable session, response revision chain, confirmation, and attachment hashes.

## Evidence routing

- A project profile manually selects target platform, native provider, and allowed fallback.
- Use native OS evidence for scheduler, thread, CPU, memory, I/O, and network criteria. Use application events for domain semantics.
- Correlate native and application sources with a run ID and monotonic time mapping. Missing required correlation blocks the criterion.
- Permit structured-log fallback only when declared and observable. Preserve requested provider, actual provider, and fallback reason.
- For bare-metal or platforms without a native provider, use bounded structured events and O(1) statistics.
- Bind runtime evidence to the accepted Execution Profile and manifest hash. Cache or branch claims require hardware counters or a declared equivalent; wall-clock timing alone cannot prove the claimed mechanism.
- Use each Execution Profile's `assurance_scope` to bound the claim. Functional
  compatibility evidence cannot satisfy performance or real-time acceptance.
  Record validation-tool OS/Python metadata outside the governed target profile.
- For a final hard/soft real-time profile, measure or conservatively bound every scheduling-analysis input selected by `references/realtime-scheduling-analysis.md`: Task execution demand, blocking, release jitter, scheduler/interrupt overhead, Queue/notification latency, and cross-core copy cost. Re-run final analysis from those inputs. Soft workloads additionally require percentile and deadline-miss-rate SLO evidence; a trace without matching analysis and SLO binding is not acceptance.
- Preserve the portable/as-is baseline and compare cycles, instructions, cache/branch misses, latency, throughput, memory, binary size, and power applicable to the decision.

## High-frequency instrumentation

Do not log every sample when logging can perturb behavior. Accumulate count, errors, drops, min, max, sum, sum of squares, and fixed histogram buckets without allocation. Emit snapshots from a bounded lower-priority context. Record counter saturation, dropped records, clock source, update cost, snapshot cost, critical-section cost, and bytes per second.

Use hard limits for any single forbidden event. Use a declared distribution method for naturally variable latency, jitter, throughput, skew, noise, or rates. Require minimum samples plus maximum duration, an explicit warm-up phase, and an instrumentation budget. Exceeding the measurement budget makes evidence `BLOCKED`, not product `FAIL`.

## Governance data

Architecture Description Views must show affected module, demand-owned Port, emitted Event, L3+ adapter, test composition root, source path, entrypoint, public symbol, clock, side effect, failure behavior, and associated L0/L1 Flow. The validation profile should reference stable Flow, Module, Port, or Event IDs.

Run architecture validation before runtime evidence collection. Then route physical or native-platform execution through `$validate-on-device` and preserve its evidence bundle.
