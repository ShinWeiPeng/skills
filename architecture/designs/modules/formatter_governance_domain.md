# formatter_governance_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | formatter_governance_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: formatter_governance_domain
  level: L2
  role: component
  implementation_status: implemented
  paths:
  - skills/engineering/formatter-governance
  parent: delivery_workflow_domain
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Select and enforce one formatter policy before product-code mutation,
      preserving repository CLI style, applying governed fallbacks, and governing
      confirmed full-program formatting writes.
    diagram_summaries:
      zh-TW: 在產品程式碼修改前選擇並執行單一格式化政策
    input_ports:
    - formatter-governance.evaluate
    output_ports:
    - formatter-governance.result
    emitted_events:
    - formatter-governance.blocked
    owned_state: []
    side_effects:
    - description: Permit only collision-free minimal scaffold and formatter configuration
        writes before product behavior exists.
    - description: Invoke the selected formatter only after its availability and exact
        target root are verified.
    - description: Format the confirmed clean product-source and test scope only after
        affirmative authorization, then run the same CLI's non-mutating check.
    errors:
    - id: formatter_policy_unresolved
      condition: ProjectState, repository formatter identity, command policy, or prerequisite
        evidence is missing or indeterminate.
      event: formatter-governance.blocked
      handling: Preserve the repository and stop before scaffold or product-code mutation.
    - id: formatter_target_unsafe
      condition: The exact target root is invalid, a scaffold path escapes or repeats
        the root, or any target or ancestor path already exists.
      event: formatter-governance.blocked
      handling: Report structured collision evidence and preserve every existing byte.
    - id: formatter_check_failed
      condition: Tool authorization, availability, non-mutating check, or observed
        check semantics do not pass.
      event: formatter-governance.blocked
      handling: Stop product-code mutation and report the failed prerequisite.
    - id: formatter_full_write_blocked
      condition: Canonical SPEC confirmation is absent or ambiguous, a targeted program
        file is dirty, CLI evidence is missing, or installation fails.
      event: formatter-governance.blocked
      handling: Preserve all target bytes and stop before the full-format write.
    invariants:
    - Greenfield selection uses one governed language mapping; existing projects preserve
      their repository formatter and style or use the governed fallback only when
      no repository CLI formatter is discoverable.
    - Indeterminate project state, target-root ambiguity, path collisions, missing
      authorization, unavailable tooling, or a failing non-mutating check blocks product-code
      mutation.
    - Minimal scaffold never overwrites an existing path and never creates an accidental
      nested project.
    - Canonical SPEC presence triggers one confirmation but never proves AI authorship
      or authorizes a formatting write.
    - Full-program formatting includes clean product source and tests while excluding
      documentation, configuration, generated, vendor, and build paths.
  entrypoints:
  - path: skills/engineering/formatter-governance/SKILL.md
    symbol: formatter-governance
    kind: skill
  - path: skills/engineering/formatter-governance/scripts/formatter_policy.py
    symbol: main
    kind: cli
  public_symbols:
  - path: skills/engineering/formatter-governance/SKILL.md
    symbol: formatter-governance
    kind: skill
  - path: skills/engineering/formatter-governance/scripts/formatter_policy.py
    symbol: main
    kind: function
```
