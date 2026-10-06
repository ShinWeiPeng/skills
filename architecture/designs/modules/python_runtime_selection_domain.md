# python_runtime_selection_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | python_runtime_selection_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: python_runtime_selection_domain
  level: L1
  role: domain
  implementation_status: implemented
  paths:
  - scripts/python-runtime-selection-policy.ps1
  parent: plugin_assembly_composition
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Own the deterministic admission policy that accepts an explicit compatible
      runtime, otherwise prefers a compatible PATH observation and requests Windows
      Launcher fallback only after that observation is rejected.
    diagram_summaries:
      zh-TW: 選取並驗證相容的 Python 執行環境
    input_ports:
    - python-runtime.select
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Explicit candidate admission is authoritative and never silently replaced.
    - A compatible PATH observation is accepted before requesting launcher fallback.
    - A launcher observation is accepted only after its resolved runtime is revalidated.
  entrypoints:
  - path: scripts/python-runtime-selection-policy.ps1
    symbol: Select-CompatiblePythonCandidate
    kind: function
  public_symbols:
  - path: scripts/python-runtime-selection-policy.ps1
    symbol: Select-CompatiblePythonCandidate
    kind: function
```
