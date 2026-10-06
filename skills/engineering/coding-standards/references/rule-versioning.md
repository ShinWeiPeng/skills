# Rule versioning

The initial shared catalog is version `1`. Keep stable rule IDs across edits;
change the catalog version when the meaning, applicability or strength changes.
Maintain that number in this Skill's `references/catalog.json`.
Record a digest of the topic documents beside the project's selected version and
applicability results. A version label alone cannot detect an unpublished edit.
The plugin release version and the architecture schema version are separate.

Before further implementation or review, compare the installed catalog with the
project's recorded version and digest. Derive deterministic ID/path/field mappings
and update current design data through its owner. Never infer missing facts,
upgrade a proposed human decision to accepted, or silently weaken a constraint.
Keep conflicts and missing decisions visible for discussion. Run all dependent
checks after migration; do not run old and new applicability policies in parallel.

Current working or confirmed-but-unimplemented SPECs are updated through the SPEC
owner. Implemented SPECs and fixed evidence remain historical records; a successor
describes changed requirements. The controlled preparation exception belongs to
spec-governance; ordinary rule/contract changes do not restore an old receipt.

Preserve existing MUST remediation, exact approved temporary deferrals and release
debt policy. New and touched code comply immediately. Before edits inspect Git
status to protect unrelated changes; a universally clean repository is not required.

## Recorded binding and check

The manifest owns `coding_rules: {version, sha256, applicability}`. The architecture
gate uses `coding_rule_contract.catalog()` to obtain the selected package's rule IDs
and SHA-256 of sorted file names and normalized UTF-8 contents. `applicability` maps
every current ID to `{status, reason}`: status is `applicable` or `not-applicable`,
and reason identifies the relevant project facts and paths. Unresolved facts remain
discussion items; they cannot be recorded as a passing binding.

Before confirming an adopted module design, populate both `coding_rules` and
`implementation_design`. The architecture gate reports `CODING001` for a missing,
stale or incomplete binding. Historical manifests without either extension stay
readable; this compatibility result does not satisfy the new design workflow.
The checker validates recorded decisions and cannot infer hardware facts or whether
a human-facing design presentation actually occurred. The Skill must do that review.

For a project's generated tool mirror, set `GOVERNED_CODING_RULES` to the resolved
shared Skill's `rules` directory before the gate. Source/installed Skill CLIs find
the adjacent catalog directly. Never copy rule files into each project. A missing
catalog blocks adopted-rule checks; moving an installation requires refreshing
the selected path and checking its digest.
