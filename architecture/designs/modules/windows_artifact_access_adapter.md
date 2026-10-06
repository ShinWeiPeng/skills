# windows_artifact_access_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | windows_artifact_access_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: windows_artifact_access_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - scripts/windows-artifact-access.ps1
  parent: null
  depends_on: []
  implements_ports:
  - plugin-artifact-access.repair
  public_headers: []
  description:
    purpose: Bind the exact governed artifact-access request to Windows filesystem
      inspection, inherited ACL reset, and narrowly scoped UAC process execution.
    diagram_summaries:
      zh-TW: 修復唯一受治理產物的 Windows 存取權限
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects:
    - description: Inspect every artifact descendant and create/delete bounded probes
        to prove recursive read and replacement access.
    - description: Reset inherited ACLs only for the exact admitted artifact, using
        an elevated PowerShell helper only after ordinary repair fails.
    errors:
    - id: windows_artifact_access_refused
      condition: The path is outside the exact artifact boundary, is a reparse point,
        remains partially inaccessible, elevation is declined, or ACL reset fails.
      event: plugin-distribution.blocked
      handling: Return a fail-closed result to composition without invoking assembly
        or Codex registration and identify the rejected safety boundary.
    invariants:
    - Repository roots, dist roots, ancestors, siblings, outside paths, and any root
      or nested reparse point are never ACL repair targets.
    - Elevated execution derives the only target from the admitted repository root.
  entrypoints:
  - path: scripts/windows-artifact-access.ps1
    symbol: Ensure-GovernedArtifactAccess
    kind: function
  public_symbols:
  - path: scripts/windows-artifact-access.ps1
    symbol: Ensure-GovernedArtifactAccess
    kind: function
```
