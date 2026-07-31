# ADR-0005: Schema 2.1.0 workload-driven real-time scheduling governance

- Status: proposed
- Date: 2026-07-31
- Approver: pending
- Approval reference: pending

## Context

Execution model and timing criticality are independent. Triggering RMA merely
because a profile uses an RTOS over-governs best-effort RTOS systems and misses
hard/soft real-time work on bare metal or an operating system. Hard and soft
real-time also have different acceptance semantics: hard requires a worst-case
deadline guarantee, while soft permits a quantified miss rate or percentile.

## Decision

- Retain the unpublished schema version 2.1.0 and replace its pre-release
  RTOS-specific scheduling fields with generic real-time fields.
- Let hard/soft workload mappings trigger `realtime_scheduling_studies`.
  RTOS use alone does not trigger a study.
- Use `analysis_method` to dispatch scheduler-compatible analyzers. Initially
  support only `rate-monotonic-rta`; unsupported methods are `BLOCKED`.
- Permit RTOS, bare-metal, and OS execution profiles when their scheduler
  satisfies the selected analyzer contract.
- Require exactly-once study coverage for each real-time workload/profile
  mapping and include all same-profile interference.
- Treat hard Task/Flow RTA misses as `FAIL`, soft misses as `SOFT_RISK`, and
  best-effort misses as informational.
- Permit a provisional soft risk only with quantified SLO budgets, validation
  plan, and non-AI risk acceptance. Require final PASS SLO evidence.
- Generate one marker-owned `realtime-study-<id>.md` report and reject missing,
  changed, stale, or obsolete reports.
- Reject obsolete pre-release fields without migration or inference.

## Alternatives considered

- RTOS plus timing-class filtering still misses non-RTOS real-time systems.
- Requiring worst-case RTA PASS for soft workloads collapses soft into hard
  semantics and contradicts permitted percentile/miss-rate budgets.
- Allowing an unplanned soft risk postpones critical validation decisions until
  after implementation.
- Forcing RM for every scheduler excludes valid EDF and time-triggered designs;
  such methods instead require their own ALG and analyzer.
- Advancing to 2.2.0 would preserve an unpublished and misleading 2.1.0
  contract, creating unnecessary compatibility work.

## Consequences

Mixed systems govern only profiles that carry real-time workloads, while all
interference within those profiles remains bounded. Reports distinguish
worst-case guarantees from soft SLO acceptance. Existing pre-release
`rtos_design_studies`, `rtos`, `rtos_isr`, and `rtos_timing` input is
configuration `BLOCKED` until a human rewrites it using the generic contract.

## Validation

Fixtures cover hard/soft non-RTOS triggers, best-effort RTOS exclusion, mixed
criticality, RM compatibility, unsupported methods, hard failures, soft risks,
SLO plan/evidence requirements, candidate coverage, generated reports,
bootstrap, integration, and stale-document rejection.

## Approval

Pending human approval. Codex must not mark this ADR accepted.
