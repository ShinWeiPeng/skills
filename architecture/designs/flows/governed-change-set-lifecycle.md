# governed-change-set-lifecycle

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | governed-change-set-lifecycle |
| version | 1 |
| kind | flow |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: governed-change-set-lifecycle
  owner: delivery_workflow_domain
  description: Persist and reconcile one modifying change set into a canonical specification,
    materialize it when decision-complete, wait for product execution authorization,
    verify traceability, implement it, and close it only after Spec review and commit
    disposition pass. Reject unsupported AC PASS evidence updates through project-validation.assess.
  trigger:
    kind: command
    ref: spec-governance.reconcile
    description: A modifying engineering discussion confirms one new statement.
  steps:
  - id: governed-change-set-lifecycle.start
    order: 1
    module: spec_governance_domain
    action: Create, transactionally migrate, or resolve one canonical SPEC before
      the first decision question; migration validates legacy identity and history
      and restores the legacy source on failure.
    receives:
    - spec-governance.start
    emits: []
    state_changes: []
    side_effects:
    - Write one canonical SPEC Markdown file with structured Discussion Context and
      an embedded normalized audit epoch.
  - id: governed-change-set-lifecycle.reconcile
    order: 2
    module: spec_governance_domain
    action: Classify the confirmed statement, update stable relationships, and report
      and persist the working specification delta, conflicts, and open decisions before
      another decision question.
    receives:
    - spec-governance.reconcile
    emits: []
    state_changes: []
    side_effects:
    - Atomically replace the working snapshot and append one normalized journal event
      containing affected REQ DEC AC and DISC identities without transcript prose.
  - id: governed-change-set-lifecycle.review-flow-cost
    order: 3
    module: governance_workflow_domain
    action: Review every material as-is and target Flow through functional admission,
      execution and real-time feasibility, maintainability and extensibility change
      scenarios, and model assurance; keep unresolved load-bearing evidence BLOCKED.
    receives: []
    emits: []
    state_changes: []
    side_effects: []
  - id: governed-change-set-lifecycle.materialize
    order: 4
    module: spec_governance_domain
    action: Materialize the decision-complete canonical specification under specs/
      without granting product execution authorization.
    receives:
    - spec-governance.materialize
    emits: []
    state_changes: []
    side_effects:
    - Write one canonical specification revision.
  - id: governed-change-set-lifecycle.authorize
    order: 5
    module: delivery_workflow_domain
    action: Present the confirmed specification and wait for exact product execution
      authorization; reopen it before clarification when a possible contract change
      appears.
    receives:
    - spec-governance.reopen
    emits: []
    state_changes: []
    side_effects:
    - Reopen one confirmed unimplemented specification in place when required.
  - id: governed-change-set-lifecycle.publish
    order: 6
    module: delivery_workflow_domain
    action: Publish a tracker snapshot that names the repository specification as
      canonical.
    receives: []
    emits: []
    state_changes: []
    side_effects:
    - Create or update one tracker Issue when configured.
  - id: governed-change-set-lifecycle.verify
    order: 7
    module: spec_governance_domain
    action: Verify requirement-to-acceptance-to-validation traceability and return
      to grilling only when the request introduces a new decision or conflict.
    receives:
    - spec-governance.verify
    emits: []
    state_changes: []
    side_effects: []
  - id: governed-change-set-lifecycle.formatter-gate
    order: 8
    module: formatter_governance_domain
    action: Select the repository formatter policy or governed fallback, confirm and
      protect any full-program write, reject ambiguous, colliding, or dirty targets,
      and require an available CLI formatter plus a passing non-mutating check before
      product-code mutation.
    receives:
    - formatter-governance.evaluate
    emits:
    - formatter-governance.blocked
    state_changes: []
    side_effects:
    - Create only collision-free minimal scaffold and formatter configuration when
      the confirmed change set targets a greenfield project.
    - Format clean product source and tests only after affirmative confirmation and
      follow the write with the selected formatter CLI's non-mutating check.
  - id: governed-change-set-lifecycle.implement-review
    order: 9
    module: delivery_workflow_domain
    action: Implement through the agreed test seams, run two-axis review, and mark
      the canonical specification implemented only after the Spec axis passes.
    receives: []
    emits: []
    state_changes: []
    side_effects:
    - Update the canonical specification with PASS evidence and implemented status.
  - id: governed-change-set-lifecycle.prepare-commit
    order: 10
    module: spec_governance_domain
    action: Reject staged local working state and require delete, keep-local, or archive
      disposition before the delivery workflow commits.
    receives:
    - spec-governance.prepare-commit
    emits: []
    state_changes: []
    side_effects: []
  success:
    result: The implemented behavior is traceable to one canonical specification whose
      requirements and acceptance criteria have verified PASS evidence.
    events: []
  errors:
  - condition: Reconciliation finds an unresolved conflict or conclusion-changing
      decision.
    event: spec-governance.blocked
    handling: Remain in grilling and ask exactly one conclusion-changing question.
  - condition: A material Flow has unresolved platform units, cost paths, budgets,
      model error, reserve, interference, or scenario coverage.
    event: spec-governance.blocked
    handling: Preserve directional analysis but keep the performance or real-time
      claim BLOCKED until the required evidence is calibrated.
  - condition: Canonical materialization succeeds but tracker publication fails.
    event: delivery.tracker-publication-pending
    handling: Preserve the canonical specification and report BLOCKED with a retry
      target.
  - condition: Local working state is staged or its retention disposition is missing.
    event: spec-governance.blocked
    handling: Preserve the bundle, block commit, and ask exactly one disposition question.
```
