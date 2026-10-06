# CAT-boundary_mappings

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-boundary_mappings |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: boundary_mappings
value:
- id: routing-assessments-to-guided-handoff
  interaction: Combine workflow-owned intent and project state with risk-owned gate
    evidence without letting either sibling depend directly on the other.
  producer: risk_routing_domain
  consumer: workflow_routing_domain
  parent: guided_workflow_router
  producer_contract: routing-decision
  consumer_contract: guided-route-decision
  mapping_owner: guided_workflow_router
  state_objects: []
  allowed_edges:
  - guided_workflow_router->risk_routing_domain
  - guided_workflow_router->workflow_routing_domain
  forbidden_edges:
  - risk_routing_domain->workflow_routing_domain
  - workflow_routing_domain->risk_routing_domain
- id: canonical-spec-to-delivery-context
  interaction: Project the child-owned canonical specification result into its parent
    delivery workflow without leaking the child contract to a sibling.
  producer: spec_governance_domain
  consumer: delivery_workflow_domain
  parent: delivery_workflow_domain
  producer_contract: canonical-spec-reference
  consumer_contract: delivery-spec-context
  mapping_owner: delivery_workflow_domain
  state_objects: []
  allowed_edges:
  - delivery_workflow_domain->spec_governance_domain
  forbidden_edges:
  - spec_governance_domain->delivery_workflow_domain
- id: delivery-spec-to-routing-context
  interaction: Convert delivery-owned canonical specification evidence into the routing
    domain's request-to-spec context without creating a sibling dependency.
  producer: delivery_workflow_domain
  consumer: workflow_routing_domain
  parent: guided_workflow_router
  producer_contract: delivery-spec-context
  consumer_contract: spec-context-assessment
  mapping_owner: guided_workflow_router
  state_objects: []
  allowed_edges:
  - guided_workflow_router->delivery_workflow_domain
  - delivery_workflow_domain->spec_governance_domain
  - guided_workflow_router->workflow_routing_domain
  forbidden_edges:
  - spec_governance_domain->workflow_routing_domain
  - workflow_routing_domain->delivery_workflow_domain
```
