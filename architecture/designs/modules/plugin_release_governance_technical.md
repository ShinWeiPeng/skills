# plugin_release_governance_technical

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | plugin_release_governance_technical |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: plugin_release_governance_technical
  level: L3+
  role: technical
  implementation_status: implemented
  paths:
  - plugins/governed-engineering-skills/scripts/version_governance.py
  parent: null
  depends_on: []
  implements_ports:
  - plugin-release.inventory
  - plugin-release.synchronize-artifact
  public_headers: []
  description:
    purpose: Validate and release the repository's only release unit through continuous
      stable-only SemVer.
    diagram_summaries:
      zh-TW: 以穩定語意版本治理唯一外掛發佈單元
    input_ports: []
    output_ports:
    - plugin-release.result
    emitted_events:
    - plugin-release.blocked
    owned_state: []
    side_effects:
    - description: An authorized release intent atomically updates plugin version
        metadata, the production fingerprint, applied changesets, and the changelog.
    - description: Artifact synchronization updates only the assembled Plugin release-state
        fingerprint before its immutable inventory is generated.
    errors:
    - id: plugin_release_identity_invalid
      condition: Version, changelog, changeset, tag, or release intent is inconsistent.
      event: plugin-release.blocked
      handling: Stop before tagging or Marketplace publication and report the stale
        release identity.
    invariants:
    - Plugin package and Codex manifest versions remain identical.
    - Plugin release metadata is the repository's sole active version authority.
    - Local Codex cachebusters never become formal release versions.
    - Formal plugin versions contain no prerelease or general build metadata.
    - Every release intent names the complete pending changeset set, and the highest
      declared bump determines the next stable version.
    - Invalid transitions or inconsistent metadata are rejected before any release
      file is modified.
    - Production fingerprint synchronization rejects the tracked incomplete Plugin
      shell and accepts only a populated assembled Skill tree.
    - Production fingerprints hash only entries selected by the deterministic assembly
      inventory, independent of ignored or untracked workspace artifacts.
  entrypoints:
  - path: plugins/governed-engineering-skills/scripts/version_governance.py
    symbol: main
    kind: cli
  public_symbols:
  - path: plugins/governed-engineering-skills/scripts/version_governance.py
    symbol: assembly_source_inventory
    kind: function
  - path: plugins/governed-engineering-skills/scripts/version_governance.py
    symbol: validate_repository
    kind: function
  - path: plugins/governed-engineering-skills/scripts/version_governance.py
    symbol: synchronize_production_fingerprint
    kind: function
```
