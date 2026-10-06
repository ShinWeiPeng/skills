# spec_governance_domain

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | spec_governance_domain |
| version | 2 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: spec_governance_domain
  level: L2
  role: component
  implementation_status: implemented
  paths:
  - skills/engineering/spec-governance
  parent: delivery_workflow_domain
  depends_on: []
  implements_ports: []
  public_headers: []
  description:
    purpose: Persist and reconcile engineering discussion into one canonical change-set
      specification, materialize it when decision-complete, and verify traceability
      before implementation. Verify the emitted completed-SPEC link, summary and authorization
      status. Own task/turn discussion entry, sourced candidate observations and durable
      repair-input deduplication across host continuations and restarts; saving and
      recovery remain available.
    diagram_summaries:
      zh-TW: 規格保存、調和、具體化與追溯驗證
    input_ports:
    - spec-governance.start
    - spec-governance.reconcile
    - spec-governance.materialize
    - spec-governance.reopen
    - spec-governance.prepare-commit
    - spec-governance.verify
    output_ports:
    - spec-governance.result
    - project-validation.assess
    emitted_events:
    - spec-governance.blocked
    owned_state: []
    side_effects:
    - description: Persist project and task scoped execution receipts; suspend product
        authority independently of SPEC discussion.
    - description: Atomically persist one canonical project-root SPEC Markdown snapshot
        with structured, visibly redacted Discussion Context and embed its normalized
        audit without full transcripts or hidden-reasoning prose; discussion observations
        may include bounded redacted goals, summaries and candidate metadata with
        sources.
    - description: Materialize one decision-complete canonical specification under
        specs/.
    errors:
    - id: specification_unresolved
      condition: Conflicts, open decisions, invalid references, or missing requirement-to-acceptance
        traceability remain.
      event: spec-governance.blocked
      handling: Preserve the last confirmed specification and return to grilling with
        exactly one conclusion-changing question.
    - id: stale_working_spec
      condition: The caller's expected revision or snapshot hash does not match the
        persisted working specification.
      event: spec-governance.blocked
      handling: Preserve the persisted snapshot, reload it, and reconcile the answer
        again without allocating replacement IDs.
    invariants:
    - Every answered decision is persisted before the next decision question.
    - Versioned pending questions survive timeout and mode changes without a deadline.
    - Only an explicit matching answer with a new DISC record clears a pending question.
    - Specification lifecycle writes never authorize product, Git, or external mutations.
    - Preparation continuation derives only missing scenario selectors from unique
      SPEC-scoped rules and verifies original document bytes, full snapshot transitions
      and definition hashes.
    - Proposal completion exposes all acceptance selection gaps before confirmation.
    - Every completed specification is presented in the emitted reply with its current
      ID, title, canonical link, summary and authorization state.
    - Confirmed specifications have unique stable IDs, resolved relations, no open
      decisions, and at least one acceptance criterion per requirement.
    - Confirmed unimplemented specifications reopen in place before a possible contract
      change; implemented specifications never reopen.
    - Implemented specifications record PASS evidence for every acceptance criterion
      and a passing Spec review.
  entrypoints:
  - path: skills/engineering/spec-governance/SKILL.md
    symbol: spec-governance
    kind: skill
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: main
    kind: cli
  - path: skills/engineering/spec-governance/scripts/state_lock.py
    symbol: project_state_lock
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: check_spec_dependencies
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: assess_turn_context
    kind: function
  - path: skills/engineering/spec-governance/scripts/discussion_state.py
    symbol: discussion_request
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: assess_discussion_completion
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: finish_discussion_turn
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: record_question
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: question_surface_policy
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: update_question
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: pending_decision
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: execution_binding
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: read_execution_state
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: write_execution_state
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: assess_execution_compatibility
    kind: function
  public_symbols:
  - path: skills/engineering/spec-governance/SKILL.md
    symbol: spec-governance
    kind: skill
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: main
    kind: function
  - path: skills/engineering/spec-governance/scripts/state_lock.py
    symbol: project_state_lock
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: check_spec_dependencies
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: assess_turn_context
    kind: function
  - path: skills/engineering/spec-governance/scripts/discussion_state.py
    symbol: discussion_request
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: assess_discussion_completion
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: finish_discussion_turn
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: record_question
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: question_surface_policy
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: update_question
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: pending_decision
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: execution_binding
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: read_execution_state
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: write_execution_state
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: assess_spec_evidence_update
    kind: function
  - path: skills/engineering/spec-governance/scripts/execution_state.py
    symbol: assess_execution_compatibility
    kind: function
  - path: skills/engineering/spec-governance/scripts/spec_contract.py
    symbol: acceptance_rows
    kind: function
```
