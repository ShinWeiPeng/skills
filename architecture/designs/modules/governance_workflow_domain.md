# governance_workflow_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | governance_workflow_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: governance_workflow_domain
  level: L1
  role: domain
  implementation_status: implemented
  paths:
  - skills/engineering/clarify-improvement-proposals
  - skills/engineering/explain-code-flow
  - skills/engineering/govern-modular-event-architecture
  - skills/engineering/validate-on-device
  - skills/engineering/coding-standards
  parent: guided_workflow_router
  depends_on:
  - verification_ladder_domain
  implements_ports: []
  public_headers: []
  description:
    purpose: Enforce decision completeness, evidence-calibrated Flow cost review,
      architecture ownership, evidence-backed explanation, and bounded runtime validation.
    diagram_summaries:
      zh-TW: 決策完整性、架構、流程成本與執行證據治理
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Codex never approves its own ADR or Algorithm Design Record.
    - A material Flow recommendation evaluates functional admission, execution and
      real-time feasibility, maintainability and extensibility, and model assurance
      before Module, Port, Event, or execution decisions are finalized.
    - Estimated models cannot establish a platform performance winner or real-time
      PASS; load-bearing evidence gaps remain BLOCKED.
    - C/C++ AST governance resolves native libclang only through its demand-owned
      pinned provider contract.
  entrypoints:
  - path: skills/engineering/govern-modular-event-architecture/SKILL.md
    symbol: govern-modular-event-architecture
    kind: skill
  public_symbols:
  - path: skills/engineering/govern-modular-event-architecture/SKILL.md
    symbol: govern-modular-event-architecture
    kind: skill
  - path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_contract.py
    symbol: LibclangToolchainPort
    kind: class
```
