# Algorithm inventory

| Product feature | Owner module | Screening | Record |
|---|---|---|---|
| Engineering risk classification and gate selection | `risk_routing_domain` | Triggered: observable routing, ordered thresholds, fallback and fail-closed behavior | [ALG-0001](ALG-0001-hard-trigger-risk-routing.md) |
| Three-state ProjectState assessment | `workflow_routing_domain` | Triggered: evidence classes, ambiguity rules, and axis precedence select observable states | [ALG-0002](ALG-0002-three-state-project-assessment.md) |
| Ordered intent and workflow selection | `workflow_routing_domain` | Triggered: ordered intent rules, workflow thresholds, fallback, and fail-closed behavior | [ALG-0003](ALG-0003-ordered-workflow-selection.md) |
| Canonical specification reconciliation and verification | `spec_governance_domain` | Triggered: stable identity assignment, ordered context resolution, consistency rules, and fail-closed traceability verdicts | [ALG-0004](ALG-0004-canonical-spec-reconciliation.md) |
| Flow cost review and model assurance | `governance_workflow_domain` | Triggered: observable candidate filtering, tiered evidence escalation, assurance verdicts, and Pareto recommendation behavior | [ALG-0005](ALG-0005-evidence-calibrated-flow-cost-review.md) |
| Compatible Python runtime selection | `python_runtime_selection_domain` | Triggered: ordered search, minimum-version threshold, fallback, and fail-closed behavior determine whether local installation proceeds | [ALG-0006](ALG-0006-compatible-python-runtime-selection.md) |
| Guided workflow composition | `guided_workflow_router` | Not applicable: composes domain decisions without owning another selection method | — |
| Plugin artifact assembly | `plugin_assembly_composition` | Not applicable beyond ALG-0006 runtime admission: deterministic file selection and SHA-256 identity, with no ranking, tuning, or heuristic choice | — |
| Personal Marketplace publication-tree generation | `plugin_assembly_composition` | Not applicable: exact path mapping and byte-for-byte release identity checks have one prescribed result with no heuristic, statistical, scheduling, or optimization choice | — |
| Local Codex runtime resolution | `local_install_adapter` | Not applicable: this integration adapter probes two contractually ordered executable locations and applies a fixed availability fallback; it owns no product-domain ranking, tuning, estimation, optimization, or probabilistic method | — |
| Codex plugin discovery | `codex_plugin_adapter` | Not applicable: declarative manifest ingestion | — |
