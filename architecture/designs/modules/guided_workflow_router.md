# guided_workflow_router

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | guided_workflow_router |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: guided_workflow_router
  level: L0
  role: composition
  implementation_status: implemented
  paths:
  - skills/engineering/ask-matt
  - skills/engineering/engineering-risk-routing/scripts/guided_workflow_router.py
  - skills/engineering/implement/scripts/discussion_hook.py
  - plugins/governed-engineering-skills/hooks/run-windows.ps1
  parent: null
  depends_on:
  - workflow_routing_domain
  - risk_routing_domain
  - delivery_workflow_domain
  - governance_workflow_domain
  - repository_evidence_adapter
  - project_validation_adapter
  implements_ports: []
  public_headers: []
  description:
    purpose: Automatically route every software-engineering intent by coordinating
      workflow selection, repository state, risk, delivery, and governance domains.
    diagram_summaries:
      zh-TW: 軟體工程請求的自動治理路由與流程協調
    input_ports:
    - guided-routing.route
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Users never need to know or invoke ask-matt for software-engineering work.
    - Every design or specification decision offers two or three meaningful options,
      preferring structured choices and falling back to equivalent numbered text.
    - Every repository-modifying change set completes grilling before mutation.
    - Discoverable facts are explored before any unresolved decision is asked.
    - Every user turn is reassessed, and an active skill reroutes through this module
      with unresolved-decision evidence before asking a repository-modifying design
      or specification question.
    - Unresolved-decision evidence is true exactly while a non-discoverable user choice
      that shapes the change set remains open; it survives short answers through reconciliation
      and clears only when no open decisions remain.
    - A newly discovered discretionary decision stops execution and returns to grilling.
    - A confirmed specification resumes only when the caller supplies explicit resume
      evidence or the fresh task is exactly `開始執行` with an optional canonical Spec
      path; discovery alone proves only durable context.
    - Never route standalone learning-note or HackMD work.
  entrypoints:
  - path: skills/engineering/ask-matt/SKILL.md
    symbol: ask-matt
    kind: skill
  - path: skills/engineering/engineering-risk-routing/scripts/guided_workflow_router.py
    symbol: main
    kind: cli
  public_symbols:
  - path: skills/engineering/ask-matt/SKILL.md
    symbol: ask-matt
    kind: skill
  - path: skills/engineering/engineering-risk-routing/scripts/guided_workflow_router.py
    symbol: route
    kind: function
```
