# architecture_governance_cli

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | architecture_governance_cli |
| version | 2 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: architecture_governance_cli
  level: L0
  role: composition
  implementation_status: implemented
  paths:
  - skills/engineering/govern-modular-event-architecture/scripts/architecture_cli.py
  - skills/engineering/govern-modular-event-architecture/scripts/architecture_document_update.py
  - skills/engineering/govern-modular-event-architecture/scripts/design_sources.py
  parent: null
  depends_on:
  - governance_workflow_domain
  - libclang_toolchain_adapter
  - spec_governance_domain
  implements_ports: []
  public_headers: []
  description:
    purpose: Compose the governance engine and pinned native provider behind the single
      public architecture CLI. Compose design sources and durable architecture document
      updates through the specification document owner.
    diagram_summaries:
      zh-TW: 透過單一命令列介面執行架構治理與原生分析
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects:
    - description: Dispatch one bounded governance or toolchain operation.
    errors: []
    invariants:
    - Gate execution never downloads or replaces a native provider cache.
  entrypoints:
  - path: skills/engineering/govern-modular-event-architecture/scripts/architecture_cli.py
    symbol: main
    kind: function
  public_symbols:
  - path: skills/engineering/govern-modular-event-architecture/scripts/architecture_cli.py
    symbol: main
    kind: function
```
