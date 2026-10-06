# Runtime checks

Use contract tests for boundary failures, arithmetic overflow, full queues/pools,
partial progress, cancellation, readers still holding data, notification overwrite,
persistent fault recovery and independent slow branches. Test both aggregation
triggers with a controlled clock and backpressure; triggering is not delivery.

Target claims need matching platform/build/workload evidence: resource maxima,
stack bounds, allocation/reclamation behavior, timing/blocking and instrumentation
cost. Host fixtures do not prove target real-time behavior or absence of memory
fragmentation. Long-run tests need bounded duration and representative load,
budgets and observable failure criteria defined by the project.

Use verification-ladder and validate-on-device for evidence selection and collection.
Preserve fixed runs, hashes and limitations; never substitute file/schema validity
for product behavior or count missing evidence as PASS.
