# CAT-events

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-events |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: events
value:
- id: formatter-governance.blocked
  owner: formatter_governance_domain
  output_port: formatter-governance.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Report that formatter selection, scaffold safety, permission, or the
      non-mutating check prevents delivery from continuing.
    emitted_when: Any formatter-governance prerequisite fails closed.
    payload_fields:
    - name: reason
      type: string
      meaning: Bounded formatter-policy diagnostic.
    intended_consumers:
    - delivery_workflow_domain
- id: local-install.blocked
  owner: local_install_adapter
  output_port: local-install.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Report that local Codex installation cannot continue safely.
    emitted_when: Artifact validation, Codex resolution, Marketplace registration,
      Plugin installation, or page launch fails.
    payload_fields:
    - name: reason
      type: string
      meaning: Bounded installation diagnostic and recovery action.
    intended_consumers:
    - plugin_assembly_composition
- id: plugin-distribution.blocked
  owner: plugin_assembly_composition
  output_port: plugin-distribution.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Report that Python admission, bounded artifact-access recovery, Plugin
      assembly, or personal Marketplace publication cannot continue safely.
    emitted_when: Python runtime, exact-target ACL recovery, artifact, publication,
      evidence, or output-ownership validation fails.
    payload_fields:
    - name: reason
      type: string
      meaning: Bounded fail-closed validation diagnostic.
    intended_consumers:
    - plugin_release_governance_technical
- id: plugin-integration.blocked
  owner: integration_validation_technical
  output_port: plugin-integration.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Report that the assembled Plugin violates an integration contract.
    emitted_when: Inventory, metadata, portability, or isolation validation fails.
    payload_fields:
    - name: reason
      type: string
      meaning: Bounded integration diagnostic.
    intended_consumers:
    - plugin_release_governance_technical
- id: plugin-release.blocked
  owner: plugin_release_governance_technical
  output_port: plugin-release.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Report that the stable release identity is inconsistent.
    emitted_when: Version, changeset, tag, or release-intent validation fails.
    payload_fields:
    - name: reason
      type: string
      meaning: Bounded release-governance diagnostic.
    intended_consumers:
    - plugin_assembly_composition
- id: spec-governance.blocked
  owner: spec_governance_domain
  output_port: spec-governance.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Tell delivery orchestration that specification work cannot continue safely.
    emitted_when: A reconciliation or verification has unresolved blocking evidence.
    payload_fields:
    - name: verdict
      type: string
      meaning: BLOCKED specification verdict.
    - name: reason
      type: string
      meaning: Conflict, ambiguity, or missing traceability that must be resolved.
    intended_consumers:
    - delivery_workflow_domain
- id: delivery.tracker-publication-pending
  owner: delivery_workflow_domain
  output_port: delivery-workflow.result
  delivery: at-most-once
  envelope:
  - event_type
  - source
  - correlation_id
  - stream_id
  - sequence
  - payload
  lifecycle:
  - received
  - validated
  - processing
  - succeeded
  - failed
  description:
    purpose: Preserve durable context while reporting that its tracker snapshot remains
      pending.
    emitted_when: Canonical materialization succeeds and tracker publication fails.
    payload_fields:
    - name: canonical_spec
      type: CanonicalSpecReference
      meaning: The repository specification that remains authoritative and retryable.
    intended_consumers:
    - guided_workflow_router
```
