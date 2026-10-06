# libclang_toolchain_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | libclang_toolchain_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: libclang_toolchain_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_adapter.py
  parent: null
  depends_on:
  - governance_workflow_domain
  implements_ports:
  - libclang_toolchain.resolve
  public_headers: []
  description:
    purpose: Provision and verify the official lock-pinned Espressif libclang distribution
      for target-capable C/C++ governance.
    diagram_summaries:
      zh-TW: 安裝並驗證鎖定版本的 Espressif libclang 工具鏈
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects:
    - description: Explicit install creates an immutable per-user version cache.
    errors: []
    invariants:
    - Gate execution never downloads or overwrites a cache.
    - Library loading is explicit and hash-verified.
  entrypoints:
  - path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_adapter.py
    symbol: EspressifLibclangToolchainAdapter
    kind: class
  public_symbols:
  - path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_adapter.py
    symbol: EspressifLibclangToolchainAdapter
    kind: class
```
