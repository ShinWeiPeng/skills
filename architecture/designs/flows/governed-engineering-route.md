# governed-engineering-route

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | governed-engineering-route |
| version | 1 |
| kind | flow |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: governed-engineering-route
  owner: guided_workflow_router
  description: Automatically classify every software-engineering request and turn-boundary
    decision handoff, inspect project state, preserve risk gates, and select an immediate
    safe skill.
  trigger:
    kind: command
    ref: guided-routing.route
    description: The user states a software-engineering intent, answers a new turn,
      or an active skill is about to ask a repository-modifying design or specification
      question; no ask-matt invocation is required.
  steps:
  - id: governed-engineering-route.assess
    order: 1
    module: workflow_routing_domain
    action: Classify ordered hard intent including exact fresh-task confirmed-Spec
      resume, preserve caller-supplied unresolved-decision evidence from before the
      first design question through answer reconciliation, and assess implementation
      and durable context from repository evidence.
    receives:
    - workflow-routing.assess-project
    - repository-evidence.collect
    emits: []
    state_changes: []
    side_effects: []
  - id: governed-engineering-route.classify-risk
    order: 2
    module: risk_routing_domain
    action: Match ordered risk hard triggers and preserve the required governance
      gates. Add project-policy and AC-plan obligations from fresh validation facts,
      preserving them on reload and short commands.
    receives:
    - risk-routing.classify
    emits: []
    state_changes: []
    side_effects: []
  - id: governed-engineering-route.select
    order: 3
    module: workflow_routing_domain
    action: Apply explicit-skill, intent, project-state, confirmed-spec resume evidence,
      unresolved-decision handoff, risk-gate, capability, and wayfinder precedence
      to produce the authoritative GuidedRouteDecision.
    receives:
    - workflow-routing.select
    emits: []
    state_changes: []
    side_effects: []
  success:
    result: A PASS or DEGRADED decision selects an immediate safe handoff; pending
      design or specification decisions select grilling before the previous skill
      asks them and name spec-governance as the immediate reconciliation target, while
      invalid evidence or missing non-substitutable capability returns BLOCKED.
    events: []
  errors: []
```
