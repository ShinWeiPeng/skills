# repository_evidence_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | repository_evidence_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: repository_evidence_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - skills/engineering/engineering-risk-routing/scripts/repository_evidence.py
  parent: null
  depends_on:
  - workflow_routing_domain
  implements_ports:
  - repository-evidence.collect
  public_headers: []
  description:
    purpose: Enumerate tracked and non-ignored untracked repository evidence without
      mutating Git, the index, or the worktree.
    diagram_summaries:
      zh-TW: 以唯讀方式蒐集可稽核的儲存庫狀態證據
    input_ports: []
    output_ports: []
    emitted_events: []
    owned_state: []
    side_effects: []
    errors: []
    invariants:
    - Never write repository files, Git metadata, or ignore configuration.
    - Exclude ignored dependencies, caches, build outputs, generated artifacts, and
      Git metadata from project-state evidence.
    - Never follow symbolic links or read their target metadata.
    - Preserve safely enumerable excluded paths with deterministic exclusion reasons.
  entrypoints:
  - path: skills/engineering/engineering-risk-routing/scripts/repository_evidence.py
    symbol: GitFilesystemRepositoryEvidenceAdapter
    kind: class
  public_symbols:
  - path: skills/engineering/engineering-risk-routing/scripts/repository_evidence.py
    symbol: GitFilesystemRepositoryEvidenceAdapter
    kind: class
```
