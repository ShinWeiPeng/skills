# project_validation_binding

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | project_validation_binding |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: project_validation_binding
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - skills/engineering/verification-ladder/scripts/project_validation.py
  parent: null
  depends_on:
  - spec_governance_domain
  - verification_ladder_domain
  implements_ports:
  - project-validation.assess
  - verification-ladder.plan
  public_headers: []
  description:
    purpose: Bind project files and CLI evidence to the SPEC owner acceptance parser
      and verification planner; resource planning stays in verification-ladder.
    diagram_summaries:
      zh-TW: 串接專案檔案、共用規格格式與驗證規劃
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Never treat absent evidence as successful verification.
  entrypoints:
  - path: skills/engineering/verification-ladder/scripts/project_validation.py
    symbol: main
    kind: cli
  public_symbols:
  - path: skills/engineering/verification-ladder/scripts/project_validation.py
    symbol: main
    kind: function
  - path: skills/engineering/verification-ladder/scripts/project_validation.py
    symbol: assess_project
    kind: function
  - path: skills/engineering/verification-ladder/scripts/project_validation.py
    symbol: spec_contract
    kind: function
```
