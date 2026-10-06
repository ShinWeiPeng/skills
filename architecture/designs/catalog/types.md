# CAT-types

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-types |
| version | 2 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: types
value:
- id: plugin-distribution-error
  owner: plugin_assembly_composition
  language: python
  declaration:
    path: scripts/assemble_plugin.py
    symbol: DistributionError
    kind: class
  visibility: cross-module
  semantic_kind: domain-value
  description: Fail-closed assembly, inventory, or source-drift error.
  lifetime: One failed assembly or validation invocation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - plugin_assembly_composition
  references: []
  fields: []
- id: personal-marketplace-publication-record
  owner: plugin_assembly_composition
  language: json-schema
  declaration:
    path: distribution/personal-marketplace-publication.schema.json
    symbol: PersonalMarketplacePublicationRecord
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: Immutable identity and rollback record for one generated personal Git
    Marketplace tree.
  lifetime: One validated Marketplace publication candidate.
  mutability: immutable
  mutation_authority: []
  consumers:
  - plugin_assembly_composition
  references: []
  fields:
  - name: schema_version
    type: string
    role: metadata
    meaning: Publication-record schema version.
  - name: channel
    type: string
    role: domain-identity
    meaning: Personal Git Marketplace publication channel.
  - name: repository_url
    type: string
    role: domain-identity
    meaning: Supported Git repository URL.
  - name: git_ref
    type: string
    role: domain-identity
    meaning: Generated Marketplace branch name.
  - name: source_commit
    type: string
    role: metadata
    meaning: Main commit used to assemble the Plugin.
  - name: source_tag
    type: string
    role: metadata
    meaning: Stable Plugin release tag.
  - name: marketplace_path
    type: string
    role: domain-identity
    meaning: Catalog path within the generated tree.
  - name: sparse_paths
    type: string-array
    role: policy
    meaning: Required Git Marketplace sparse paths.
  - name: artifact
    type: object
    role: metadata
    meaning: Plugin name version inventory and fingerprint.
  - name: tree_fingerprint
    type: string
    role: metadata
    meaning: Deterministic publication-tree fingerprint.
  - name: installation_steps
    type: string-array
    role: policy
    meaning: Optional Codex Marketplace installation instructions.
  - name: rollback
    type: object
    role: policy
    meaning: Prior validated publication commit and recovery method.
  - name: evidence_checklist
    type: string-array
    role: metadata
    meaning: Optional Codex publication verification observations.
- id: repository-artifact
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: RepositoryArtifact
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: One tracked or non-ignored untracked path returned by repository discovery.
  lifetime: One repository evidence query.
  mutability: immutable
  mutation_authority: []
  consumers:
  - workflow_routing_domain
  - repository_evidence_adapter
  references: []
  fields:
  - name: path
    type: string
    role: domain-identity
    meaning: Project-relative normalized artifact path.
  - name: tracking
    type: string
    role: metadata
    meaning: tracked or untracked source of the artifact.
  - name: size_bytes
    type: integer
    role: metadata
    meaning: Artifact size used to distinguish empty placeholders from implementation.
  - name: exclusion_reason
    type: nullable-string
    role: policy
    meaning: Deterministic reason an artifact is excluded, or null when it is eligible
      evidence.
- id: repository-evidence
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: RepositoryEvidence
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: One normalized repository artifact considered by project-state assessment.
  lifetime: One project-state assessment.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  - workflow_routing_domain
  references: []
  fields:
  - name: path
    type: string
    role: domain-identity
    meaning: Project-relative normalized artifact path.
  - name: tracking
    type: string
    role: metadata
    meaning: tracked or untracked source of the evidence.
  - name: size_bytes
    type: integer
    role: metadata
    meaning: Artifact size used to distinguish empty placeholders from implementation.
  - name: classification
    type: string
    role: policy
    meaning: implementation, stateful-context, ambiguous, or excluded.
  - name: reason
    type: string
    role: metadata
    meaning: Deterministic explanation for the classification.
- id: project-state-assessment
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: ProjectStateAssessment
    kind: interface
  visibility: cross-module
  semantic_kind: query
  description: Evidence-backed three-state assessment of implementation and durable
    project context.
  lifetime: One guided route.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references:
  - repository-artifact
  - repository-evidence
  fields:
  - name: implementation
    type: string
    role: policy
    meaning: present, absent, or indeterminate implementation state.
  - name: stateful_context
    type: string
    role: policy
    meaning: present, absent, or indeterminate durable documentation state.
  - name: evidence
    type: repository-evidence-array
    role: metadata
    meaning: Included and excluded path evidence supporting both axes.
- id: intent-assessment
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: IntentAssessment
    kind: interface
  visibility: cross-module
  semantic_kind: query
  description: Ordered hard-intent classification for one engineering request.
  lifetime: One guided route.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references: []
  fields:
  - name: intent
    type: string
    role: policy
    meaning: Explicit skill, confirmed-Spec resume, code understanding, diagnosis,
      review, implementation-design, or indeterminate.
  - name: explicit_skill
    type: nullable-string
    role: contract-control
    meaning: User-selected skill that outranks inferred intent.
  - name: matched_terms
    type: string-array
    role: metadata
    meaning: Ordered deterministic term evidence.
  - name: requires_modification
    type: boolean
    role: policy
    meaning: Whether the change set must complete grilling before mutation.
- id: workflow-selection-options
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: WorkflowSelectionOptions
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: Explicit caller evidence that controls safe workflow-selection exceptions.
  lifetime: One guided route.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  - workflow_routing_domain
  references: []
  fields:
  - name: resume_confirmed_spec
    type: boolean
    role: contract-control
    meaning: True only when the request explicitly continues the selected confirmed
      specification without a new decision or conflict; defaults to false.
- id: guided-route-decision
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: GuidedRouteDecision
    kind: interface
  visibility: cross-module
  semantic_kind: query
  description: Authoritative engineering skill handoff with capability and gate evidence.
  lifetime: One guided route and its handoff.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references:
  - project-state-assessment
  - intent-assessment
  - spec-context-assessment
  fields:
  - name: selected_skill
    type: nullable-string
    role: contract-control
    meaning: Authoritative primary skill or fallback selected for immediate safe handoff.
  - name: project_state
    type: ProjectStateAssessment
    role: metadata
    meaning: Evidence-backed implementation and durable-context assessment.
  - name: intent_assessment
    type: IntentAssessment
    role: metadata
    meaning: Ordered engineering intent classification.
  - name: spec_context
    type: SpecContextAssessment
    role: contract-control
    meaning: Active canonical specification selection required by modifying workflows.
  - name: state
    type: string
    role: contract-control
    meaning: PASS, DEGRADED, or BLOCKED.
  - name: reason
    type: string
    role: metadata
    meaning: Reader-facing explanation of the handoff.
  - name: required_gates
    type: string-array
    role: policy
    meaning: Risk gates preserved from RoutingDecision.
  - name: fallback
    type: nullable-string
    role: contract-control
    meaning: Transparent equivalent primitive used when the preferred skill is unavailable.
  - name: resume_target
    type: nullable-string
    role: contract-control
    meaning: Workflow target after decisions, gates, or capabilities are resolved.
  - name: turn_context
    type: nullable-object
    role: metadata
    meaning: Immutable recovered task decision evidence including exact pending options
      and working identity.
- id: spec-context-assessment
  owner: workflow_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/guided-routing-contract.schema.json
    symbol: SpecContextAssessment
    kind: interface
  visibility: cross-module
  semantic_kind: query
  description: Deterministic binding between one engineering request and its canonical
    specification.
  lifetime: One guided route and its specification handoff.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  - workflow_routing_domain
  references: []
  fields:
  - name: status
    type: string
    role: policy
    meaning: none, ambiguous, working, confirmed, implemented, or invalid.
  - name: selected_path
    type: nullable-string
    role: domain-identity
    meaning: Project-relative canonical specification path selected for this change
      set.
  - name: candidates
    type: string-array
    role: metadata
    meaning: Deterministically ordered matching specification paths.
  - name: reason
    type: string
    role: metadata
    meaning: Evidence-backed explanation of selection or ambiguity.
- id: working-spec-reference
  owner: spec_governance_domain
  language: json-schema
  declaration:
    path: skills/engineering/spec-governance/references/spec-contract.schema.json
    symbol: WorkingSpecReference
    kind: interface
  visibility: module-public
  semantic_kind: domain-value
  description: Stable identity, revision, hash, flat project-root paths, and continuity
    epoch for one persisted canonical working specification.
  lifetime: One change set from first grilling question through commit disposition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - delivery_workflow_domain
  references: []
  fields:
  - name: working_id
    type: string
    role: domain-identity
    meaning: Project-local opaque identity for the working change set.
  - name: snapshot_path
    type: string
    role: metadata
    meaning: Project-relative authoritative Markdown snapshot path.
  - name: journal_path
    type: string
    role: metadata
    meaning: Project-relative audit container path; equals snapshot_path for a canonical
      single-file SPEC. Legacy JSONL paths remain readable during migration.
  - name: revision
    type: integer
    role: metadata
    meaning: Monotonically increasing working revision.
  - name: snapshot_hash
    type: string
    role: contract-control
    meaning: SHA-256 digest required for optimistic concurrency.
  - name: continuity
    type: string
    role: policy
    meaning: continuous or unavailable journal-history status.
  - name: status
    type: string
    role: policy
    meaning: working while interviewing or confirmed after materialization.
  - name: spec_id
    type: string
    role: domain-identity
    meaning: SPEC-0000 before first materialization or the preserved canonical SPEC
      ID.
  - name: change_set
    type: string
    role: metadata
    meaning: Stable lowercase change-set slug.
  - name: task_ref
    type: string-or-null
    role: metadata
    meaning: Optional task evidence used after an explicit reference.
  - name: branch_ref
    type: string-or-null
    role: metadata
    meaning: Optional branch evidence used after task evidence.
- id: discussion-context-record
  owner: spec_governance_domain
  language: json-schema
  declaration:
    path: skills/engineering/spec-governance/references/spec-contract.schema.json
    symbol: DiscussionContextRecord
    kind: interface
  visibility: module-public
  semantic_kind: domain-value
  description: Human-readable context for one conclusion-changing discussion decision.
  lifetime: One change set from the decision through commit disposition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - delivery_workflow_domain
  references: []
  fields:
  - name: discussion_id
    type: string
    role: domain-identity
    meaning: Stable DISC-### identity.
  - name: situation
    type: string
    role: domain-value
    meaning: Decision context visible to the user.
  - name: question
    type: string
    role: domain-value
    meaning: Conclusion-changing question.
  - name: options_and_tradeoffs
    type: string
    role: policy
    meaning: Considered choices and material tradeoffs.
  - name: user_answer
    type: string
    role: domain-value
    meaning: Visible original user answer after required redaction.
  - name: explicit_rationale
    type: string
    role: domain-value
    meaning: User-stated rationale or not stated.
  - name: resulting_impact
    type: string-array
    role: metadata
    meaning: Affected REQ DEC and AC identities.
- id: spec-consistency-assessment
  owner: spec_governance_domain
  language: json-schema
  declaration:
    path: skills/engineering/spec-governance/references/spec-contract.schema.json
    symbol: SpecConsistencyAssessment
    kind: interface
  visibility: module-public
  semantic_kind: query
  description: Classified specification delta with relationship and unresolved-decision
    evidence.
  lifetime: One discussion reconciliation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - delivery_workflow_domain
  references: []
  fields:
  - name: verdict
    type: string
    role: contract-control
    meaning: PASS or BLOCKED.
  - name: delta
    type: object-array
    role: domain-value
    meaning: Added or changed stable IDs and their knowledge classifications.
  - name: conflicts
    type: object-array
    role: policy
    meaning: Unresolved logical contradictions with durable or working context.
  - name: open_decisions
    type: string-array
    role: policy
    meaning: Conclusion-changing decisions that prevent materialization.
- id: canonical-spec-reference
  owner: spec_governance_domain
  language: json-schema
  declaration:
    path: skills/engineering/spec-governance/references/spec-contract.schema.json
    symbol: CanonicalSpecReference
    kind: interface
  visibility: module-public
  semantic_kind: domain-value
  description: Stable identity and lifecycle metadata for one canonical change-set
    specification.
  lifetime: One specification revision.
  mutability: immutable
  mutation_authority: []
  consumers:
  - delivery_workflow_domain
  references: []
  fields:
  - name: spec_id
    type: string
    role: domain-identity
    meaning: Repository-unique SPEC identifier.
  - name: path
    type: string
    role: metadata
    meaning: Project-relative canonical Markdown path.
  - name: revision
    type: integer
    role: metadata
    meaning: Monotonically increasing specification revision.
  - name: status
    type: string
    role: policy
    meaning: working, confirmed, or implemented lifecycle state; only confirmed may
      enter implementation verification.
- id: delivery-spec-context
  owner: delivery_workflow_domain
  language: markdown
  declaration:
    path: skills/engineering/implement/SKILL.md
    symbol: CanonicalSpecReferenceProjection
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: Delivery-owned projection of the canonical specification identity for
    guided routing.
  lifetime: One guided route and its delivery handoff.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references:
  - canonical-spec-reference
  fields:
  - name: spec_id
    type: string
    role: domain-identity
    meaning: Repository-unique SPEC identifier.
  - name: path
    type: string
    role: metadata
    meaning: Project-relative canonical Markdown path.
  - name: revision
    type: integer
    role: metadata
    meaning: Monotonically increasing specification revision.
  - name: status
    type: string
    role: policy
    meaning: confirmed or implemented lifecycle state.
- id: spec-traceability-assessment
  owner: spec_governance_domain
  language: json-schema
  declaration:
    path: skills/engineering/spec-governance/references/spec-contract.schema.json
    symbol: SpecTraceabilityAssessment
    kind: interface
  visibility: module-public
  semantic_kind: query
  description: Requirement, acceptance, validation, and scope-conformance verdict
    for implementation.
  lifetime: One pre-implementation verification or Spec review.
  mutability: immutable
  mutation_authority: []
  consumers:
  - delivery_workflow_domain
  references:
  - canonical-spec-reference
  fields:
  - name: verdict
    type: string
    role: contract-control
    meaning: PASS or BLOCKED.
  - name: uncovered_requirements
    type: string-array
    role: policy
    meaning: REQ identifiers without acceptance coverage.
  - name: uncovered_acceptance
    type: string-array
    role: policy
    meaning: AC identifiers without a validation method or required evidence.
  - name: scope_creep
    type: string-array
    role: policy
    meaning: Implemented behavior not authorized by the canonical specification.
- id: repository-evidence-port
  owner: workflow_routing_domain
  language: python
  declaration:
    path: skills/engineering/engineering-risk-routing/scripts/project_state.py
    symbol: RepositoryEvidencePort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Demand-owned interface for read-only repository evidence collection.
  lifetime: Process lifetime.
  mutability: immutable
  mutation_authority: []
  consumers:
  - workflow_routing_domain
  - repository_evidence_adapter
  references:
  - repository-artifact
  fields: []
- id: git-filesystem-repository-evidence-adapter
  owner: repository_evidence_adapter
  language: python
  declaration:
    path: skills/engineering/engineering-risk-routing/scripts/repository_evidence.py
    symbol: GitFilesystemRepositoryEvidenceAdapter
    kind: class
  visibility: module-public
  semantic_kind: adapter-binding
  description: Git-aware implementation of the repository evidence Port.
  lifetime: One guided routing process.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references:
  - repository-evidence-port
  - repository-artifact
  fields: []
- id: routing-decision
  owner: risk_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/routing-contract.schema.json
    symbol: RoutingDecision
    kind: interface
  visibility: cross-module
  semantic_kind: query
  description: Deterministic classification and workflow-resume result.
  lifetime: One routing evaluation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references: []
  fields:
  - name: task_class
    type: string
    role: domain-value
    meaning: Classified engineering task family.
  - name: matched_hard_triggers
    type: string-array
    role: policy
    meaning: Ordered matched trigger evidence.
  - name: risk_class
    type: nullable-string
    role: policy
    meaning: R0 through R3 or null when outside the router.
  - name: required_gates
    type: string-array
    role: policy
    meaning: Gates that must pass before the workflow resumes.
  - name: next_skill
    type: nullable-string
    role: contract-control
    meaning: Compatibility advisory for the first risk gate; GuidedRouteDecision owns
      the authoritative handoff.
  - name: status
    type: string
    role: contract-control
    meaning: PASS or BLOCKED.
  - name: return_to_flow
    type: nullable-string
    role: contract-control
    meaning: Workflow target after gates pass.
- id: gate-result
  owner: risk_routing_domain
  language: json-schema
  declaration:
    path: skills/engineering/engineering-risk-routing/references/routing-contract.schema.json
    symbol: GateResult
    kind: interface
  visibility: cross-module
  semantic_kind: domain-value
  description: Evidence-bearing result for one required gate.
  lifetime: One governed workflow and its handoffs.
  mutability: immutable
  mutation_authority: []
  consumers:
  - guided_workflow_router
  references: []
  fields:
  - name: gate
    type: string
    role: domain-identity
    meaning: Skill or validation gate identity.
  - name: status
    type: string
    role: contract-control
    meaning: PASS or BLOCKED.
  - name: evidence
    type: string-array
    role: metadata
    meaning: References to reproducible evidence.
  - name: resume_target
    type: nullable-string
    role: contract-control
    meaning: Workflow target after the gate.
- id: governance-diagnostic
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/check_architecture.py
    symbol: Diagnostic
    kind: class
  visibility: private
  semantic_kind: private-helper
  description: Internal architecture diagnostic.
  lifetime: One governance invocation.
  mutability: owner-mutable
  mutation_authority:
  - governance_workflow_domain
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: governance-manifest-error
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/check_architecture.py
    symbol: ManifestError
    kind: class
  visibility: private
  semantic_kind: private-helper
  description: Internal manifest loading failure.
  lifetime: One failed governance invocation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: governance-ast-evidence
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/ast_analyzer.py
    symbol: AstEvidence
    kind: class
  visibility: private
  semantic_kind: private-helper
  description: Internal C/C++ AST evidence accumulator.
  lifetime: One analyzer invocation.
  mutability: owner-mutable
  mutation_authority:
  - governance_workflow_domain
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: libclang-toolchain-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_contract.py
    symbol: LibclangToolchainPort
    kind: class
  visibility: cross-module
  semantic_kind: port
  description: Demand-owned contract for explicit provider installation and offline
    verification.
  lifetime: One governance CLI composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  - libclang_toolchain_adapter
  references:
  - libclang-toolchain-evidence
  fields: []
- id: libclang-toolchain-evidence
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_contract.py
    symbol: LibclangToolchainEvidence
    kind: class
  visibility: cross-module
  semantic_kind: domain-value
  description: Immutable provider identity, integrity, path, version, and capability
    evidence.
  lifetime: One provider operation or C/C++ gate.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  - libclang_toolchain_adapter
  references: []
  fields:
  - name: provider
    type: str
    role: domain-identity
    meaning: Provider identifier.
  - name: provider_version
    type: str
    role: domain-value
    meaning: Provider release.
  - name: binding_version
    type: str
    role: domain-value
    meaning: Python binding release.
  - name: library_path
    type: Path
    role: metadata
    meaning: Explicit verified library path.
  - name: archive_sha256
    type: str
    role: metadata
    meaning: Official archive digest.
  - name: library_sha256
    type: str
    role: metadata
    meaning: Extracted library digest.
  - name: target_triple
    type: str
    role: policy
    meaning: Xtensa probe target.
- id: toolchain-provider-error
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_contract.py
    symbol: ToolchainProviderError
    kind: class
  visibility: cross-module
  semantic_kind: domain-value
  description: Fail-closed CAST001 or CAST002 provider diagnostic.
  lifetime: One failed provider operation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - architecture_governance_cli
  - governance_workflow_domain
  - libclang_toolchain_adapter
  references: []
  fields: []
- id: espressif-libclang-toolchain-adapter
  owner: libclang_toolchain_adapter
  language: python
  declaration:
    path: skills/engineering/govern-modular-event-architecture/scripts/libclang_toolchain_adapter.py
    symbol: EspressifLibclangToolchainAdapter
    kind: class
  visibility: module-public
  semantic_kind: adapter-binding
  description: Official artifact installer and offline cache verifier.
  lifetime: One CLI composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - architecture_governance_cli
  references:
  - libclang-toolchain-port
  - libclang-toolchain-evidence
  fields: []
- id: collection-input-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/execution.py
    symbol: CollectionInputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Runtime-evidence collection input contract.
  lifetime: One validation composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: collection-output-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/execution.py
    symbol: CollectionOutputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Runtime-evidence collection output contract.
  lifetime: One validation composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: transport-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/execution.py
    symbol: TransportPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Runtime-evidence transport contract.
  lifetime: One validation composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: guided-session-input-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/guided.py
    symbol: GuidedSessionInputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Guided validation-session input contract.
  lifetime: One guided session.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: guided-session-output-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/guided.py
    symbol: GuidedSessionOutputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Guided validation-session output contract.
  lifetime: One guided session.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: runtime-verdict
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/model.py
    symbol: Verdict
    kind: class
  visibility: module-public
  semantic_kind: domain-value
  description: Runtime validation verdict value.
  lifetime: One criterion evaluation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: criterion-result
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/model.py
    symbol: CriterionResult
    kind: class
  visibility: module-public
  semantic_kind: domain-value
  description: Evidence-bearing criterion result.
  lifetime: One criterion evaluation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references:
  - runtime-verdict
  fields: []
- id: verdict-input-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/model.py
    symbol: VerdictInputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Verdict-domain input contract.
  lifetime: One validation composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: verdict-output-port
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/model.py
    symbol: VerdictOutputPort
    kind: class
  visibility: module-public
  semantic_kind: port
  description: Verdict-domain output contract.
  lifetime: One validation composition.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: validation-profile-error
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/profile.py
    symbol: ProfileError
    kind: class
  visibility: private
  semantic_kind: private-helper
  description: Invalid runtime-validation profile failure.
  lifetime: One failed profile load.
  mutability: immutable
  mutation_authority: []
  consumers:
  - governance_workflow_domain
  references: []
  fields: []
- id: platform-transport-adapter
  owner: governance_workflow_domain
  language: python
  declaration:
    path: skills/engineering/validate-on-device/scripts/vod/providers.py
    symbol: PlatformTransportAdapter
    kind: class
  visibility: private
  semantic_kind: adapter-binding
  description: Platform transport implementation selected by runtime validation.
  lifetime: One validation composition.
  mutability: owner-mutable
  mutation_authority:
  - governance_workflow_domain
  consumers:
  - governance_workflow_domain
  references:
  - transport-port
  fields: []
- id: spec-document-error
  owner: spec_governance_domain
  language: python
  declaration:
    path: skills/engineering/spec-governance/scripts/document_bundle.py
    symbol: DocumentError
    kind: class
  visibility: private
  semantic_kind: private-helper
  description: Source-located shared document format and reference failure.
  lifetime: One rejected document operation.
  mutability: immutable
  mutation_authority: []
  consumers:
  - spec_governance_domain
  references: []
  fields: []
```
