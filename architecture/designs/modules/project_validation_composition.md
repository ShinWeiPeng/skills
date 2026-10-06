# project_validation_composition

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | project_validation_composition |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: project_validation_composition
  level: L0
  role: composition
  implementation_status: implemented
  paths:
  - skills/engineering/implement/scripts/project_validation_workflow.py
  parent: null
  depends_on:
  - delivery_workflow_domain
  - project_validation_adapter
  implements_ports: []
  public_headers: []
  description:
    purpose: Inject the project validation adapter into existing specification and
      delivery public CLIs.
    diagram_summaries:
      zh-TW: 在入口注入專案驗證工具
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Functional consumers receive the demand-owned validation callable; they never
      construct the technical adapter.
  entrypoints:
  - path: skills/engineering/implement/scripts/project_validation_workflow.py
    symbol: main
    kind: cli
  public_symbols:
  - path: skills/engineering/implement/scripts/project_validation_workflow.py
    symbol: main
    kind: function
```
