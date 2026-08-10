# Algorithm inventory

| Product feature | Owner module | Screening result | Record |
|---|---|---|---|
| C/C++ architecture evidence classification | `governance_engine` | Full record required because conservative pointer analysis and fail-closed classification affect validation results. | [ALG-0001](ALG-0001-ast-boundary-analysis.md) |
| Workload-driven real-time Task-set and scheduling validation | `realtime_schedulability_analysis` | Full record required because timing class, method selection, Task grouping, rates, priority, core allocation, soft SLO policy, and fallback behavior affect product deadlines. | [ALG-0002](ALG-0002-partitioned-rma-rta.md) |
| Python source conformance and adoption readiness | `governance_engine` | Full record required because AST classification and gate aggregation determine whether implementation evidence is verified, deferred, failed, or blocked. | [ALG-0003](ALG-0003-python-ast-adoption-verdict.md) |
