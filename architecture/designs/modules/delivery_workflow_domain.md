# delivery_workflow_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | delivery_workflow_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: delivery_workflow_domain
  level: L1
  role: domain
  implementation_status: implemented
  paths:
  - skills/engineering/diagnosing-bugs
  - skills/engineering/grill-with-docs
  - skills/engineering/triage
  - skills/engineering/improve-codebase-architecture
  - skills/engineering/setup-matt-pocock-skills
  - skills/engineering/tdd
  - skills/engineering/to-spec
  - skills/engineering/to-tickets
  - skills/engineering/wayfinder
  - skills/engineering/implement
  - skills/engineering/prototype
  - skills/engineering/research
  - skills/engineering/domain-modeling
  - skills/engineering/codebase-design
  - skills/engineering/code-review
  - skills/engineering/resolving-merge-conflicts
  - skills/productivity/grill-me
  - skills/productivity/grilling
  - skills/productivity/handoff
  - skills/productivity/teach
  - skills/productivity/writing-great-skills
  parent: guided_workflow_router
  depends_on:
  - spec_governance_domain
  - formatter_governance_domain
  implements_ports: []
  public_headers: []
  description:
    purpose: Move an engineering idea or defect through planning, implementation,
      and review without bypassing required gates.
    diagram_summaries:
      zh-TW: 從規劃、實作到審查的受治理交付流程
    input_ports: []
    output_ports:
    - delivery-workflow.result
    emitted_events:
    - delivery.tracker-publication-pending
    owned_state: []
    side_effects:
    - description: Admit and atomically apply one hash-checked file replacement through
        the managed delivery CLI, leaving arbitrary host tools outside enforcement.
    errors: []
    invariants:
    - SPEC-0039 continue-execution orchestrates same-event AC preparation, owner confirmation,
      admission, projection and a reviewed continuation; status-only success is not
      a product write.
    - Legacy snapshots are recovered only from grant-bound persisted history; missing
      evidence, malformed state, changed scope and revoked or superseded events remain
      explicit blockers.
    - Continuation checkpoints preserve idempotency after interruption and recheck
      target hashes; implementation admission and actual acceptance evidence remain
      separate.
    - Product mutation and commits require task and repository authorization; specification
      lifecycle writes do not grant that authority.
    - Every repository-modifying change set has one canonical specification before
      implementation.
    - Governed delivery reloads the current canonical hash, working identity and explicit
      human execution instruction.
    - A confirmed specification is verified rather than re-interviewed only with explicit
      resume evidence and no new decision or conflict.
  entrypoints:
  - path: skills/engineering/implement/SKILL.md
    symbol: implement
    kind: skill
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_spec_context
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: manage_delivery_discussion
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_turn_context
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: verify_delivery_admission
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: main
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: execute_request
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: audit_trace
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: main
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_compatibility
    kind: function
  public_symbols:
  - path: skills/engineering/implement/SKILL.md
    symbol: implement
    kind: skill
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_spec_context
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: manage_delivery_discussion
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_turn_context
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: verify_delivery_admission
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: main
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: execute_request
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: audit_trace
    kind: function
  - path: skills/engineering/implement/scripts/managed_delivery.py
    symbol: main
    kind: function
  - path: skills/engineering/implement/scripts/spec_delivery.py
    symbol: assess_delivery_compatibility
    kind: function
```
