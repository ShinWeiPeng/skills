# python_runtime_discovery_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | python_runtime_discovery_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: python_runtime_discovery_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - scripts/python-runtime-selection.ps1
  parent: null
  depends_on:
  - python_runtime_selection_domain
  implements_ports:
  - python-runtime.select
  public_headers: []
  description:
    purpose: Discover and execute explicit, PATH, and Windows Python Launcher candidates,
      convert process output into validated observations, and apply the functional
      runtime-selection policy for the one-click installer.
    diagram_summaries:
      zh-TW: 探測 Windows Python 候選並套用相容性政策
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects:
    - description: Execute bounded side-effect-free Python capability probes through
        PATH applications or the Windows Python Launcher.
    errors:
    - id: python_runtime_probe_failed
      condition: A candidate cannot execute, returns malformed output, reports an
        old version, or resolves a missing executable path.
      event: plugin-distribution.blocked
      handling: Preserve the observation as a diagnostic and follow the domain-owned
        admission or fallback action without entering Plugin assembly.
    invariants:
    - Every accepted executable is normalized to an absolute path and revalidated.
    - Python 2 and Python 3.10 are observable candidates but never execution runtimes.
  entrypoints:
  - path: scripts/python-runtime-selection.ps1
    symbol: Resolve-CompatiblePython
    kind: function
  public_symbols:
  - path: scripts/python-runtime-selection.ps1
    symbol: Resolve-CompatiblePython
    kind: function
```
