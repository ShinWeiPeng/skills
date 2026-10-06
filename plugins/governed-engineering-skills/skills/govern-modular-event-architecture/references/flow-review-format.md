# Flow review format

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

