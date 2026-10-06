# workflow_routing_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | workflow_routing_domain |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: workflow_routing_domain
  level: L1
  role: domain
  implementation_status: implemented
  paths:
  - skills/engineering/engineering-risk-routing/scripts/project_state.py
  - skills/engineering/engineering-risk-routing/scripts/workflow_selection.py
  - skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
  - skills/engineering/engineering-risk-routing/references/intent-rules.json
  parent: guided_workflow_router
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Own deterministic engineering-intent classification, three-state project
      assessment, capability fallback, and final skill handoff selection.
    diagram_summaries:
      zh-TW: 意圖分類、專案狀態評估與技能交接選擇
    input_ports:
    - workflow-routing.assess-project
    - workflow-routing.select
    output_ports:
    - repository-evidence.collect
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Explicit skills outrank inferred intent.
    - Intent selects the primary flow before project state and risk gates are applied.
    - A uniquely resolved confirmed specification does not bypass ProjectState interview
      precedence without explicit resume evidence.
    - Pending unresolved-decision evidence means a non-discoverable user choice affects
      implementation behavior, an interface, a persistent parameter, failure policy,
      specification scope, or an acceptance threshold.
    - Pending unresolved-decision evidence overrides lexical ambiguity in a short
      follow-up, selects grilling before the question is presented, and resumes at
      spec-governance for reconciliation.
    - Exact fresh-task `開始執行` derives resume evidence; quoted, negated, or conversational
      uses do not.
    - Resume evidence fails closed unless it identifies one valid confirmed specification;
      ambiguous candidates require one explicit selection.
    - A reopened working canonical specification blocks execution even when completed
      stages contain evidence from its prior confirmed revision.
    - Indeterminate intent or project state is never silently guessed.
    - Risk classification adds gates but never replaces the primary user intent.
  entrypoints:
  - path: skills/engineering/engineering-risk-routing/scripts/project_state.py
    symbol: assess_project_state
    kind: function
  - path: skills/engineering/engineering-risk-routing/scripts/workflow_selection.py
    symbol: select_workflow
    kind: function
  public_symbols:
  - path: skills/engineering/engineering-risk-routing/scripts/project_state.py
    symbol: RepositoryEvidencePort
    kind: class
  - path: skills/engineering/engineering-risk-routing/scripts/project_state.py
    symbol: assess_project_state
    kind: function
  - path: skills/engineering/engineering-risk-routing/scripts/workflow_selection.py
    symbol: classify_intent
    kind: function
  - path: skills/engineering/engineering-risk-routing/scripts/workflow_selection.py
    symbol: select_workflow
    kind: function
```
