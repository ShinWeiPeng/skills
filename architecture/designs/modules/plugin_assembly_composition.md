# plugin_assembly_composition

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | plugin_assembly_composition |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: plugin_assembly_composition
  level: L0
  role: composition
  implementation_status: implemented
  paths:
  - scripts/assemble_plugin.py
  - scripts/install-local.ps1
  - scripts/validate_distribution.py
  - distribution/skill-compatibility.json
  - distribution/personal-marketplace-publication.schema.json
  parent: null
  depends_on:
  - codex_plugin_adapter
  - local_install_adapter
  - python_runtime_selection_domain
  - python_runtime_discovery_adapter
  - windows_artifact_access_adapter
  - plugin_release_governance_technical
  implements_ports: []
  public_headers: []
  description:
    purpose: Assemble one complete Plugin artifact from the tracked Plugin shell and
      the two authoritative promoted Skill buckets, normalize host-specific invocation
      metadata, select and validate one Python 3.11+ interpreter before assembly,
      safely recover access to only the exact ignored Windows artifact, coordinate
      the supported local Codex installation, and optionally emit a deterministic
      Codex Git Marketplace publication tree.
    diagram_summaries:
      zh-TW: 組裝單一外掛並產生個人 Git 市集發佈樹
    input_ports:
    - plugin-release.inventory
    - plugin-release.synchronize-artifact
    - plugin-install.local
    - plugin-artifact-access.repair
    - local-install.register
    output_ports:
    - plugin-distribution.result
    emitted_events:
    - plugin-distribution.blocked
    owned_state: []
    side_effects:
    - description: Replace only selected ignored output directories with a deterministic
        Plugin artifact and Marketplace publication tree.
    - description: Rehearse release validation in a temporary checkout populated exclusively
        from the current tracked working-tree files.
    - description: Apply a local-only cache identity to the ignored validated artifact
        without changing formal release metadata.
    - description: Invoke the local installation adapter only after the assembled
        Plugin inventory and fingerprint validate.
    - description: Request the Windows artifact-access adapter to repair inherited
        access only for the exact ignored dist/governed-engineering-skills artifact,
        with elevation available only after a bounded non-elevated attempt fails.
    errors:
    - id: plugin_distribution_invalid
      condition: Source metadata, artifact inventory, publication identity, tree fingerprint,
        Codex installation evidence, or output ownership is invalid.
      event: plugin-distribution.blocked
      handling: Fail closed, preserve unrelated files, and report the mismatched identity
        or validation boundary.
    - id: python_runtime_incompatible
      condition: An explicitly injected Python command is incompatible, or neither
        PATH Python nor the Windows Python Launcher resolves Python 3.11 or newer.
      event: plugin-distribution.blocked
      handling: Stop before assembly, report every observed candidate and version,
        and explain how to install or explicitly select Python 3.11 or newer.
    - id: plugin_artifact_access_blocked
      condition: The existing ignored artifact is inaccessible and its exact canonical
        path, repository containment, reparse-point safety, non-elevated repair, or
        explicitly approved elevated repair cannot be validated.
      event: plugin-distribution.blocked
      handling: Refuse paths outside the exact governed artifact, stop before assembly
        and Codex registration, preserve unrelated files, and report whether elevation
        was declined or the bounded ACL repair failed.
    invariants:
    - Root engineering and productivity buckets are the only editable Skill source.
    - The tracked Plugin shell never contains a skills directory.
    - Plugin assembly and production fingerprinting consume the same deterministic
      source-to-artifact inventory and reject duplicate logical artifact paths.
    - Every artifact records one complete file inventory and SHA-256 content fingerprint.
    - Assembly stages the complete replacement before removing a previous validated
      artifact.
    - Assembled release-state mutation is delegated to Plugin release governance before
      inventory creation.
    - The supported local installer consumes the same validated assembled artifact
      as optional Marketplace publication.
    - Codex Desktop and Codex CLI are the only supported installation surfaces.
    - Python selection completes before artifact mutation and the selected absolute
      interpreter performs every assembly, validation, and localization command.
    - Windows ACL recovery accepts only the canonical repository-owned dist/governed-engineering-skills
      directory and never a repository root, ancestor, sibling, outside path, symbolic
      link, junction, or other reparse point.
    - '`marketplace-release` is generated and never becomes an editable Skill source.'
    - Release readiness is reported only after a tracked-file-only rehearsal passes
      assembly, distribution, artifact, version, Marketplace-candidate, and tag eligibility
      validation.
  entrypoints:
  - path: scripts/assemble_plugin.py
    symbol: main
    kind: cli
  - path: scripts/install-local.ps1
    symbol: install-local
    kind: script
  public_symbols:
  - path: scripts/install-local.ps1
    symbol: install-local
    kind: script
  - path: plugins/governed-engineering-skills/scripts/install-local.ps1
    symbol: install-local
    kind: script
  - path: scripts/assemble_plugin.py
    symbol: assemble
    kind: function
  - path: scripts/assemble_plugin.py
    symbol: validate_artifact
    kind: function
  - path: scripts/assemble_plugin.py
    symbol: localize_artifact
    kind: function
  - path: scripts/assemble_plugin.py
    symbol: write_marketplace_publication
    kind: function
  - path: scripts/assemble_plugin.py
    symbol: rehearse_release
    kind: function
  - path: scripts/validate_distribution.py
    symbol: validate
    kind: function
```
