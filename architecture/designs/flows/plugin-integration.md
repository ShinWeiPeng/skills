# plugin-integration

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | plugin-integration |
| version | 1 |
| kind | flow |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: plugin-integration
  owner: plugin_assembly_composition
  description: Validate the assembled plugin and its routed contracts using repository-owned
    host integration suites.
  trigger:
    kind: command
    ref: plugin-release.synchronize-artifact
    description: Maintainer requests source-to-artifact integration verification.
  steps:
  - id: plugin-integration.verify
    order: 1
    module: plugin_assembly_composition
    action: Assemble canonical skill sources, then run integration suites and inventory
      validation against the candidate.
    receives:
    - plugin-release.synchronize-artifact
    emits: []
    state_changes: []
    side_effects:
    - Create independent host-test evidence under artifacts/tests/.
  success:
    result: All selected host suites and source-to-artifact checks pass with fixed
      run evidence.
    events: []
  errors:
  - condition: A contract, dependency capability or artifact binding is incomplete.
    event: plugin-distribution.blocked
    handling: Keep independent evidence and report FAIL or BLOCKED; do not publish.
```
