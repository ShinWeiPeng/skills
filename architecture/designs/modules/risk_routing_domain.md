# risk_routing_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | risk_routing_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: risk_routing_domain
  level: L1
  role: domain
  implementation_status: implemented
  paths:
  - skills/engineering/engineering-risk-routing
  parent: guided_workflow_router
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Own engineering risk classes, gate selection, fail-closed behavior, and
      resume targets.
    diagram_summaries:
      zh-TW: 工程風險分級、必要閘門與失敗關閉決策
    input_ports:
    - risk-routing.classify
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Higher hard-trigger risk always takes precedence.
    - Missing required capabilities or evidence cannot be downgraded.
  entrypoints:
  - path: skills/engineering/engineering-risk-routing/scripts/classify_risk.py
    symbol: main
    kind: cli
  public_symbols:
  - path: skills/engineering/engineering-risk-routing/scripts/classify_risk.py
    symbol: classify
    kind: function
```
