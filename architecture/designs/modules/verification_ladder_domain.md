# verification_ladder_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | verification_ladder_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: verification_ladder_domain
  level: L2
  role: component
  implementation_status: implemented
  paths:
  - skills/engineering/verification-ladder
  parent: governance_workflow_domain
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Select the lowest sufficient additive verification layers for affected
      module contracts and evidence claims, validate project bindings, and reject
      cross-layer evidence substitution.
    diagram_summaries:
      zh-TW: 選擇模組契約所需驗證層並阻擋跨層證據替代
    input_ports:
    - verification-ladder.plan
    output_ports: []
    emitted_events: []
    owned_state:
    - name: active run operation
      ref: run-operation-context
      description: Context-local nesting identity; only the storage adapter sets and
        resets it while holding the filesystem operation lock.
    side_effects: []
    errors: []
    invariants:
    - Host evidence remains valid for host-observable semantics but never satisfies
      target timing, scheduler, physical-hardware, or long-duration stability claims.
    - Device-dependent PIL, HIL, and System/Soak execution is delegated to validate-on-device
      after Validation Enablement.
    - Missing or stale architecture, scenario, profile, trigger, or evidence bindings
      return BLOCKED instead of silently omitting a layer.
  entrypoints:
  - path: skills/engineering/verification-ladder/SKILL.md
    symbol: verification-ladder
    kind: skill
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: main
    kind: function
  public_symbols:
  - path: skills/engineering/verification-ladder/SKILL.md
    symbol: verification-ladder
    kind: skill
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: main
    kind: function
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: plan
    kind: function
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: validate_matrix
    kind: function
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: validate_paths
    kind: function
  - path: skills/engineering/verification-ladder/scripts/verification_ladder.py
    symbol: assess_evidence
    kind: function
```
