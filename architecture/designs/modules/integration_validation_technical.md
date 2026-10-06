# integration_validation_technical

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | integration_validation_technical |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: integration_validation_technical
  level: L3+
  role: technical
  implementation_status: implemented
  paths:
  - plugins/governed-engineering-skills/scripts/validate_integration.py
  parent: null
  depends_on:
  - plugin_release_governance_technical
  implements_ports: []
  public_headers: []
  description:
    purpose: Validate plugin inventory, skill metadata, path portability, and learning-note
      isolation.
    diagram_summaries:
      zh-TW: 驗證外掛清單、叫用政策、可攜性與內容隔離
    input_ports: []
    output_ports:
    - plugin-integration.result
    emitted_events:
    - plugin-integration.blocked
    owned_state: []
    side_effects: []
    errors:
    - id: plugin_integration_invalid
      condition: Inventory, metadata, portability, or learning-note isolation violates
        the assembled Plugin contract.
      event: plugin-integration.blocked
      handling: Emit bounded diagnostics and return a non-zero validation result without
        mutating the Plugin or user configuration.
    invariants:
    - Validation must not mutate the plugin or user configuration.
  entrypoints:
  - path: plugins/governed-engineering-skills/scripts/validate_integration.py
    symbol: main
    kind: cli
  public_symbols:
  - path: plugins/governed-engineering-skills/scripts/validate_integration.py
    symbol: main
    kind: function
```
