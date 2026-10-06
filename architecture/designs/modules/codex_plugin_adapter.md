# codex_plugin_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | codex_plugin_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: codex_plugin_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - plugins/governed-engineering-skills/.codex-plugin
  parent: null
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Bind the integrated skill directory to Codex plugin discovery.
    diagram_summaries:
      zh-TW: 將整合技能目錄接入 Codex 外掛探索機制
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - The manifest discovers exactly one flat skills root.
  entrypoints:
  - path: plugins/governed-engineering-skills/.codex-plugin/plugin.json
    symbol: governed-engineering-skills
    kind: manifest
  public_symbols:
  - path: plugins/governed-engineering-skills/.codex-plugin/plugin.json
    symbol: governed-engineering-skills
    kind: manifest
```
