# local-plugin-installation

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | local-plugin-installation |
| version | 1 |
| kind | flow |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: local-plugin-installation
  owner: plugin_assembly_composition
  description: Select one compatible Python interpreter, recover safe access to only
    the exact ignored Windows artifact when necessary, assemble and validate the root-owned
    Plugin, apply a local-only cache identity, then register and install it before
    opening the Codex Desktop detail page.
  trigger:
    kind: command
    ref: plugin-install.local
    description: The user launches Install Governed Engineering Skills.cmd.
  steps:
  - id: local-plugin-installation.select-python
    order: 1
    module: python_runtime_discovery_adapter
    action: Validate an explicit Python command when supplied; otherwise accept a
      compatible PATH Python or resolve the Windows Python Launcher's highest Python
      3 runtime to one validated absolute interpreter path.
    receives:
    - python-runtime.select
    emits: []
    state_changes: []
    side_effects: []
  - id: local-plugin-installation.recover-artifact-access
    order: 2
    module: windows_artifact_access_adapter
    action: Confirm that the exact dist/governed-engineering-skills output is safely
      replaceable; when an existing Windows artifact is inaccessible, try a bounded
      inherited-ACL repair without elevation and request UAC only if that attempt
      fails.
    receives:
    - plugin-artifact-access.repair
    emits: []
    state_changes: []
    side_effects:
    - Repair inherited ACLs only on the exact ignored dist/governed-engineering-skills
      artifact after rejecting unsafe paths and reparse points.
  - id: local-plugin-installation.assemble
    order: 3
    module: plugin_assembly_composition
    action: Build the complete Plugin from the tracked shell and promoted root Skills,
      then reject missing, stale, or fingerprint-mismatched output.
    receives:
    - plugin-install.local
    emits: []
    state_changes: []
    side_effects:
    - Replace only the ignored dist/governed-engineering-skills candidate.
  - id: local-plugin-installation.localize
    order: 4
    module: plugin_assembly_composition
    action: Apply a local-only cache identity to the validated artifact and regenerate
      its inventory without changing formal release metadata.
    receives: []
    emits: []
    state_changes: []
    side_effects:
    - Mutate only the ignored dist/governed-engineering-skills candidate.
  - id: local-plugin-installation.register
    order: 5
    module: local_install_adapter
    action: Select an executable Codex CLI using verified PATH-first resolution with
      Desktop-runtime fallback, register the repository-local Marketplace, install
      the Plugin, and open its detail page.
    receives:
    - local-install.register
    emits: []
    state_changes: []
    side_effects:
    - Update the current user's Codex Marketplace configuration.
    - Install the Plugin into the current user's Codex cache.
    - Open the Codex Desktop Plugin detail page.
  success:
    result: Codex recognizes the local Marketplace entry and reports successful installation
      from the validated, locally cache-busted artifact.
    events: []
  errors:
  - condition: The explicit, PATH, and Windows Python Launcher candidates do not yield
      a validated Python 3.11-or-newer absolute interpreter.
    event: plugin-distribution.blocked
    handling: Stop before artifact mutation, report observed candidates and versions,
      and provide Python installation or explicit-selection recovery guidance.
  - condition: Assembly or artifact validation fails.
    event: plugin-distribution.blocked
    handling: Stop before invoking Codex or changing user configuration and report
      the failed validation boundary.
  - condition: The existing ignored artifact is inaccessible and exact-target safety,
      reparse-point rejection, non-elevated repair, UAC approval, or post-repair access
      validation fails.
    event: plugin-distribution.blocked
    handling: Stop before assembly and Codex registration, leave unrelated paths untouched,
      return a stable non-zero status, and identify the rejected safety boundary or
      UAC recovery action.
  - condition: Codex resolution, Marketplace registration, Plugin installation, or
      Plugin-page launch fails.
    event: local-install.blocked
    handling: Preserve the validated artifact, issue no removal command against a
      prior Plugin install, return a stable non-zero exit code, and provide the log
      and retry action. A Marketplace registered before installation failure remains
      registered for that retry.
```
