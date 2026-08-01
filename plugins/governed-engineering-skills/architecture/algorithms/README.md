# Algorithm inventory

| Product feature | Owner module | Screening | Record |
|---|---|---|---|
| Engineering risk classification and gate selection | `risk_routing_domain` | Triggered: observable routing, ordered thresholds, fallback and fail-closed behavior | [ALG-0001](ALG-0001-hard-trigger-risk-routing.md) |
| Three-state ProjectState assessment | `workflow_routing_domain` | Triggered: evidence classes, ambiguity rules, and axis precedence select observable states | [ALG-0002](ALG-0002-three-state-project-assessment.md) |
| Ordered intent and workflow selection | `workflow_routing_domain` | Triggered: ordered intent rules, workflow thresholds, fallback, and fail-closed behavior | [ALG-0003](ALG-0003-ordered-workflow-selection.md) |
| Guided workflow composition | `guided_workflow_router` | Not applicable: composes domain decisions without owning another selection method | — |
| Vendor snapshot verification | `vendor_sync_adapter` | Not applicable: exact SHA-256 equality, with no ranking, tuning, or heuristic choice | — |
| Codex plugin discovery | `codex_plugin_adapter` | Not applicable: declarative manifest ingestion | — |
