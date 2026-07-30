# Algorithm inventory

| Product feature | Owner module | Screening | Record |
|---|---|---|---|
| Engineering risk classification and gate selection | `risk_routing_domain` | Triggered: observable routing, ordered thresholds, fallback and fail-closed behavior | [ALG-0001](ALG-0001-hard-trigger-risk-routing.md) |
| Guided workflow presentation | `guided_workflow_router` | Not applicable: presents the classifier result without selecting another method | — |
| Vendor snapshot verification | `vendor_sync_adapter` | Not applicable: exact SHA-256 equality, with no ranking, tuning, or heuristic choice | — |
| Codex plugin discovery | `codex_plugin_adapter` | Not applicable: declarative manifest ingestion | — |
