# Project document responsibilities

| Document | Owner | Format source | Project data | Creation/check entry |
|---|---|---|---|---|
| SPEC | spec-governance | SPEC contract and owner validator | Confirmed requirements, decisions, relationships and ACs | Existing discussion, reconciliation and materialization CLI |
| Module and public interface design | Architecture governance | module-design-format.md | Manifest implementation_design modules/interfaces and existing IDs | Architecture render and gate; source/caller review |
| Data-flow design | Architecture governance | data-flow-design-format.md | Manifest implementation_design flows and existing flow IDs | Architecture render and gate; actual data-path review |
| Algorithm record | Architecture governance | algorithm-record-format.md | Owner's method, alternatives, parameters and evidence | algorithm-design-workflow.md and architecture review |
| Flow cost review | Architecture governance | flow-review-format.md | Actual/candidate paths, models and observations | flow-cost-checks.md |
| ADR | Shared plugin ADR governance | adr/format.md profiles | Decision proposed by domain-modeling or architecture governance | adr/workflow.md and adr/checks.md; proposing Skill owns domain substance |
| Coding-rule applicability | coding-standards | rule-versioning.md binding | Project facts, budgets, paths and selected shared catalog | Design gate and code review; unknown facts remain unresolved |
| Validation evidence | verification-ladder and relevant validation Skill | Existing run manifest and evidence contracts | Actual command/device observations and source/input hashes | Existing bounded run storage and acceptance assessment |

The owner maintains the meaning and lifecycle. The format defines required fields.
Project data supplies the actual facts. The entry performs creation or validation.
Generated views project their declared source; they are not a second editable owner.

In a source checkout this shared directory is under
`plugins/governed-engineering-skills/references`. In an assembled plugin it is
`references`. Skill references live under the corresponding Skill's `references`
directory in both layouts.
