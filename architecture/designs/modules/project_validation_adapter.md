# project_validation_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | project_validation_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: project_validation_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - skills/engineering/implement/scripts/project_validation_adapter.py
  parent: null
  depends_on:
  - spec_governance_domain
  - project_validation_binding
  implements_ports:
  - project-validation.assess
  public_headers: []
  description:
    purpose: Invoke the selected verification-ladder JSON CLI with bounded execution
      and return project validation facts without device actions.
    diagram_summaries:
      zh-TW: 呼叫專案驗證工具並回傳可追溯結果
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Never operate devices or convert incomplete evidence into PASS.
  entrypoints:
  - path: skills/engineering/implement/scripts/project_validation_adapter.py
    symbol: assess_project_validation
    kind: function
  public_symbols:
  - path: skills/engineering/implement/scripts/project_validation_adapter.py
    symbol: assess_project_validation
    kind: function
```
