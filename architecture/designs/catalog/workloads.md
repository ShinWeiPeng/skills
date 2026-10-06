# CAT-workloads

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-workloads |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: workloads
value:
- id: verification-ladder-planning-workload
  flow: verification-ladder-planning
  steps:
  - verification-ladder-planning.evaluate
  timing_class: best-effort
  activation:
    kind: command
  data:
    volume: one bounded project verification matrix and one affected change set
  budgets: []
- id: local-plugin-installation-workload
  flow: local-plugin-installation
  steps:
  - local-plugin-installation.recover-artifact-access
  - local-plugin-installation.assemble
  - local-plugin-installation.register
  timing_class: best-effort
  activation:
    kind: command
  data:
    volume: one local Plugin installation request
  budgets: []
- id: governed-routing-workload
  flow: governed-engineering-route
  steps:
  - governed-engineering-route.assess
  - governed-engineering-route.classify-risk
  - governed-engineering-route.select
  timing_class: best-effort
  activation:
    kind: command
  data:
    volume: one engineering task
  budgets: []
- id: governed-change-set-workload
  flow: governed-change-set-lifecycle
  steps:
  - governed-change-set-lifecycle.start
  - governed-change-set-lifecycle.reconcile
  - governed-change-set-lifecycle.review-flow-cost
  - governed-change-set-lifecycle.materialize
  - governed-change-set-lifecycle.authorize
  - governed-change-set-lifecycle.publish
  - governed-change-set-lifecycle.verify
  - governed-change-set-lifecycle.implement-review
  - governed-change-set-lifecycle.prepare-commit
  timing_class: best-effort
  activation:
    kind: command
  data:
    volume: one modifying engineering change set
  budgets: []
- id: plugin-integration-workload
  flow: plugin-integration
  steps:
  - plugin-integration.verify
  timing_class: best-effort
  activation:
    kind: command
  data:
    volume: one assembled plugin candidate
  budgets: []
```
