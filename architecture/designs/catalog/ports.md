# CAT-ports

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-ports |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: ports
value:
- id: verification-ladder.plan
  owner: verification_ladder_domain
  direction: input
  kind: query
  contract: skills/engineering/verification-ladder/references/verification-ladder.schema.json
  implemented_by:
  - project_validation_binding
  description:
    purpose: Validate one project verification matrix and derive the additive layers
      required by affected architecture references, contract dimensions, execution
      changes, and evidence claims.
    data: Project matrix, governed architecture manifest, optional on-device profile,
      affected trigger categories, and observed evidence layers.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The matrix or a referenced architecture, profile, scenario, trigger,
        threshold, or evidence binding is missing, stale, duplicated, or malformed.
  symbols:
  - main
- id: python-runtime.select
  owner: python_runtime_selection_domain
  direction: input
  kind: query
  contract: scripts/python-runtime-selection-policy.ps1
  implemented_by:
  - python_runtime_discovery_adapter
  description:
    purpose: Select one installed Python 3.11-or-newer interpreter before Plugin assembly.
    data: Optional explicit command plus PATH and Windows Python Launcher candidates.
    timing: sync
    immediate_rejections:
    - code: incompatible
      condition: No contractually ordered candidate resolves a valid compatible interpreter.
  symbols:
  - Select-CompatiblePythonCandidate
- id: plugin-artifact-access.repair
  owner: plugin_assembly_composition
  direction: input
  kind: query
  contract: scripts/install-local.ps1
  implemented_by:
  - windows_artifact_access_adapter
  description:
    purpose: Admit and restore replace access to only the exact governed Windows artifact.
    data: Canonical repository root, exact artifact path, and bounded recovery result.
    timing: sync
    immediate_rejections:
    - code: unsafe-target
      condition: The target is not the exact repository artifact or contains a reparse
        point.
    - code: inaccessible
      condition: Ordinary and approved elevated inherited-ACL repair do not make every
        descendant inspectable and replaceable.
  symbols:
  - install-local
- id: plugin-install.local
  owner: plugin_assembly_composition
  direction: input
  kind: command
  contract: scripts/install-local.ps1
  implemented_by: []
  description:
    purpose: Assemble, validate, and begin installation of the governed Plugin for
      local Codex.
    data: Repository-relative source, output, and Marketplace identities.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The repository source or required assembly tooling is unavailable.
    - code: python-incompatible
      condition: No validated Python 3.11-or-newer interpreter can be selected.
    - code: artifact-access-blocked
      condition: The exact ignored Windows artifact cannot pass bounded path, reparse-point,
        ACL-repair, elevation-consent, and post-repair access checks.
  symbols:
  - install-local
- id: local-install.register
  owner: plugin_assembly_composition
  direction: input
  kind: command
  contract: plugins/governed-engineering-skills/scripts/install-local.ps1
  implemented_by:
  - local_install_adapter
  description:
    purpose: Register the validated local Marketplace and open the governed Plugin
      page.
    data: Validated assembled Plugin path, Marketplace manifest path, and Plugin identifier.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The assembled Plugin or Marketplace manifest is incomplete or inconsistent.
  symbols:
  - install-local
- id: local-install.result
  owner: local_install_adapter
  direction: output
  kind: event
  contract: plugins/governed-engineering-skills/scripts/install-local.ps1
  implemented_by: []
  description:
    purpose: Publish a bounded local Codex installation result.
    data: Stable exit status, installation phase, and actionable diagnostic.
    timing: sync
    immediate_rejections: []
  symbols:
  - install-local
- id: plugin-release.synchronize-artifact
  owner: plugin_assembly_composition
  direction: input
  kind: command
  contract: plugins/governed-engineering-skills/scripts/version_governance.py
  implemented_by:
  - plugin_release_governance_technical
  description:
    purpose: Ask Plugin release governance to bind an assembled Plugin release-state
      to that artifact's current production fingerprint.
    data: Assembled Plugin root path whose release-state fingerprint must match its
      logical production files.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The target lacks a populated assembled Skill tree, or its release-state
        is missing, malformed, or lacks its fingerprint field.
    - code: unavailable
      condition: The assembled Plugin fingerprint cannot be calculated.
  symbols:
  - assemble
- id: plugin-release.inventory
  owner: plugin_assembly_composition
  direction: input
  kind: query
  contract: plugins/governed-engineering-skills/scripts/version_governance.py
  implemented_by:
  - plugin_release_governance_technical
  description:
    purpose: Enumerate the deterministic source-to-artifact files shared by Plugin
      assembly and production fingerprinting.
    data: Repository root mapped to unique normalized Plugin artifact paths and their
      source files.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: A selected source is missing, outside an authoritative source root,
        or maps to a duplicate logical artifact path.
    - code: unavailable
      condition: The tracked repository inventory cannot be read.
  symbols:
  - assemble
- id: plugin-distribution.result
  owner: plugin_assembly_composition
  direction: output
  kind: event
  contract: distribution/personal-marketplace-publication.schema.json
  implemented_by: []
  description:
    purpose: Publish a fail-closed Plugin assembly or Marketplace validation result.
    data: Artifact identity, publication identity, and bounded validation diagnostics.
    timing: sync
    immediate_rejections: []
  symbols:
  - validate_artifact
- id: plugin-integration.result
  owner: integration_validation_technical
  direction: output
  kind: event
  contract: plugins/governed-engineering-skills/scripts/validate_integration.py
  implemented_by: []
  description:
    purpose: Publish the assembled Plugin integration-validation result.
    data: Inventory, metadata, portability, and isolation diagnostics.
    timing: sync
    immediate_rejections: []
  symbols:
  - main
- id: plugin-release.result
  owner: plugin_release_governance_technical
  direction: output
  kind: event
  contract: plugins/governed-engineering-skills/scripts/version_governance.py
  implemented_by: []
  description:
    purpose: Publish the stable Plugin release-identity validation result.
    data: Version, changeset, tag, and release-intent diagnostics.
    timing: sync
    immediate_rejections: []
  symbols:
  - validate_repository
- id: guided-routing.route
  owner: guided_workflow_router
  direction: input
  kind: query
  contract: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
  implemented_by: []
  description:
    purpose: Route one software-engineering request to its safe primary skill.
    data: Task text, project root, explicit skill, available capabilities, risk decision,
      wayfinder complexity evidence, and caller-supplied unresolved-decision evidence.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The task text or project root is malformed.
    - code: unavailable
      condition: Project-state evidence cannot be collected.
  symbols:
  - ask-matt
- id: risk-routing.classify
  owner: risk_routing_domain
  direction: input
  kind: query
  contract: skills/engineering/engineering-risk-routing/references/routing-contract.schema.json
  implemented_by: []
  description:
    purpose: Classify one engineering task and select required gates.
    data: Task text, optional entry skill, available capabilities, and passed gate
      evidence.
    timing: sync
    immediate_rejections: []
  symbols:
  - classify
- id: workflow-routing.assess-project
  owner: workflow_routing_domain
  direction: input
  kind: query
  contract: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
  implemented_by: []
  description:
    purpose: Convert repository evidence into a three-state implementation and documentation
      assessment.
    data: Read-only tracked and non-ignored untracked path evidence.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: Evidence does not satisfy the RepositoryEvidence contract.
  symbols:
  - assess_project_state
- id: workflow-routing.select
  owner: workflow_routing_domain
  direction: input
  kind: query
  contract: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
  implemented_by: []
  description:
    purpose: Select the authoritative skill handoff after intent, project state, risk,
      capability, and complexity checks.
    data: IntentAssessment, ProjectStateAssessment, RoutingDecision, capabilities,
      wayfinder threshold evidence, exact fresh-task confirmed-Spec resume intent,
      and caller-supplied unresolved-decision lifecycle evidence for a non-discoverable
      choice that shapes the change set.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: Any required assessment is missing or malformed.
  symbols:
  - select_workflow
- id: repository-evidence.collect
  owner: workflow_routing_domain
  direction: output
  kind: query
  contract: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
  implemented_by:
  - repository_evidence_adapter
  description:
    purpose: Read repository paths and Git tracking status for project-state assessment.
    data: One project root produces normalized RepositoryEvidence rows.
    timing: sync
    immediate_rejections:
    - code: unavailable
      condition: The root is unreadable or Git evidence collection fails.
  symbols:
  - RepositoryEvidencePort
- id: spec-governance.start
  owner: spec_governance_domain
  direction: input
  kind: command
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Create, migrate, or resolve one canonical project-root working specification
      with embedded audit.
    data: Project root, change-set slug and optional working, task, or branch evidence
      produce one immutable WorkingSpecReference.
    timing: sync
    immediate_rejections:
    - code: ambiguous
      condition: More than one working specification matches without an explicit reference.
  symbols:
  - spec-governance
- id: formatter-governance.evaluate
  owner: formatter_governance_domain
  direction: input
  kind: query
  contract: skills/engineering/formatter-governance/references/formatter-policy-request.schema.json
  implemented_by: []
  description:
    purpose: Evaluate formatter selection, exact-root scaffold safety, full-program
      confirmation and scope, and the pre-product mutation gate through one stable
      CLI contract.
    data: ProjectState, language or repository formatter identity and argv, exact
      root and scaffold paths, prior evidence statuses, tool availability, check status,
      canonical SPEC, confirmation, clean-target evidence, CLI write and check outcomes,
      and native permission outcome.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: Required structured input or exact-root evidence is missing or malformed.
  symbols:
  - main
- id: formatter-governance.result
  owner: formatter_governance_domain
  direction: output
  kind: event
  contract: skills/engineering/formatter-governance/references/formatter-policy-result.schema.json
  implemented_by: []
  description:
    purpose: Publish the formatter policy PASS or BLOCKED decision with bounded evidence.
    data: Project kind and root, formatter identity, check and write argv, program
      and dirty file scopes, confirmation, installation and execution outcomes, mutation
      allowances, and diagnostic reason.
    timing: sync
    immediate_rejections: []
  symbols:
  - main
- id: spec-governance.reconcile
  owner: spec_governance_domain
  direction: input
  kind: command
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Reconcile and persist one newly confirmed discussion statement before
      another decision question.
    data: Expected working revision and hash, existing durable context, and one confirmed
      statement produce a new snapshot, normalized journal event, and consistency
      verdict.
    timing: sync
    immediate_rejections:
    - code: invalid
      condition: The statement or working specification is malformed.
    - code: stale
      condition: Expected revision or snapshot hash differs from persisted state.
  symbols:
  - spec-governance
- id: spec-governance.materialize
  owner: spec_governance_domain
  direction: input
  kind: command
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Persist one decision-complete working specification as the canonical
      repository artifact.
    data: A PASS SpecConsistencyAssessment produces one versioned Markdown specification
      without granting product execution authority.
    timing: sync
    immediate_rejections:
    - code: unresolved
      condition: Conflicts, open decisions, invalid relations, or uncovered requirements
        remain.
  symbols:
  - spec-governance
- id: spec-governance.reopen
  owner: spec_governance_domain
  direction: input
  kind: command
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Reopen a confirmed unimplemented specification in place before clarifying
      a possible contract change.
    data: Expected canonical revision, reason, and specification path produce a working
      canonical revision in the same SPEC file with embedded audit.
    timing: sync
    immediate_rejections:
    - code: implemented
      condition: The specification has already reached implemented status.
    - code: stale
      condition: Expected revision differs from the canonical specification.
  symbols:
  - spec-governance
- id: spec-governance.prepare-commit
  owner: spec_governance_domain
  direction: input
  kind: query
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Detect staged local WORKING-SPEC pairs and require an explicit retention
      disposition.
    data: Project Git state and known working pairs produce delete, keep-local, or
      archive choices without performing Git actions.
    timing: sync
    immediate_rejections:
    - code: staged-local-state
      condition: A path under project-root spec-governance is tracked or staged.
  symbols:
  - spec-governance
- id: spec-governance.verify
  owner: spec_governance_domain
  direction: input
  kind: query
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Verify a canonical specification and its requirement-to-validation traceability.
    data: A resolved canonical specification and current request produce a PASS or
      BLOCKED assessment.
    timing: sync
    immediate_rejections:
    - code: ambiguous
      condition: More than one canonical specification matches the current change
        set.
    - code: invalid
      condition: The selected specification violates the structural contract.
  symbols:
  - spec-governance
- id: spec-governance.result
  owner: spec_governance_domain
  direction: output
  kind: event
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Publish one specification lifecycle result to the delivery parent.
    data: Consistency or traceability verdict with canonical specification identity.
    timing: sync
    immediate_rejections: []
  symbols:
  - spec-governance
- id: delivery-workflow.result
  owner: delivery_workflow_domain
  direction: output
  kind: event
  contract: skills/engineering/spec-governance/references/spec-contract.schema.json
  implemented_by: []
  description:
    purpose: Publish delivery failures that preserve a valid canonical specification.
    data: Canonical specification identity and the pending external delivery action.
    timing: sync
    immediate_rejections: []
  symbols:
  - implement
- id: libclang_toolchain.resolve
  owner: governance_workflow_domain
  direction: output
  kind: query
  contract: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_contract.py
  implemented_by:
  - libclang_toolchain_adapter
  description:
    purpose: Resolve, bind, and verify one lock-pinned target-capable libclang provider.
    data: Toolchain lock and operation mode produce immutable provider evidence or
      fail-closed CAST diagnostics.
    timing: sync
    immediate_rejections:
    - code: CAST001
      condition: Provider or Xtensa capability is unavailable.
    - code: CAST002
      condition: Lock, platform, cache, or receipt is invalid.
  symbols:
  - LibclangToolchainPort
- id: project-validation.assess
  owner: spec_governance_domain
  direction: output
  kind: query
  contract: skills/engineering/verification-ladder/references/project-validation.schema.json
  implemented_by:
  - project_validation_adapter
  - project_validation_binding
  description:
    purpose: Assess project planning or completion before recording acceptance.
    data: Project root, canonical SPEC and phase produce a validation verdict with
      source hashes and diagnostics.
    timing: sync
    immediate_rejections:
    - code: unavailable
      condition: Missing capability, invalid context, stale bindings or inadequate
        evidence.
  symbols:
  - assess_spec_evidence_update
```
