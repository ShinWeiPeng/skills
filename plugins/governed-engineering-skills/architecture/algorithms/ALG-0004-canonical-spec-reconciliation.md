# ALG-0004: Canonical specification reconciliation

## Metadata

- Status: proposed
- Owner module: `spec_governance_domain`
- Product feature: Canonical change-set specification lifecycle
- Flow IDs: `governed-change-set-lifecycle`
- Related ADRs: `ADR-0011`
- Source paths:
  - `skills/spec-governance/scripts/spec_contract.py`
  - `skills/spec-governance/references/spec-contract.schema.json`
- Test and benchmark paths: `tests/test_spec_governance.py`
- Supersedes: none

## Problem and observable success

Turn a multi-round engineering discussion into one logically consistent, durable
change-set contract without requiring product execution authorization or repeating
settled decisions after conversation compaction. Success is a deterministic
`PASS` or `BLOCKED` assessment with stable IDs, monotonic revisions, a verifiable
working snapshot and an unambiguous canonical path.

## Inputs, outputs, and assumptions

Inputs are the persisted working specification, its expected revision and hash, one
discussion delta, repository formal context, accepted ADRs, the architecture
manifest, optional task/tracker/branch evidence, local working bundles and repository
`specs/`. Outputs are `WorkingSpecReference`, `SpecContextAssessment`,
`SpecConsistencyAssessment`, `CanonicalSpecReference`, and
`SpecTraceabilityAssessment`. Snapshots are UTF-8 Markdown and journals are UTF-8
JSONL.

## Ordered method

1. Start or resolve one working bundle by explicit reference, available task/branch
   evidence, then unique fallback; ambiguity blocks instead of selecting by recency.
2. Reject a delta when its expected revision or snapshot hash is stale.
3. Classify each delta as a domain term, change-set contract, ADR candidate, or open
   decision.
4. Reuse stable `REQ-###`, `DEC-###`, and `AC-###` IDs; assign the next unused ID only
   to genuinely new statements.
5. Compare the working contract with `CONTEXT.md`, accepted ADRs, and the architecture
   manifest; report affected IDs, relations, conflicts, and open decisions.
6. Atomically replace the authoritative Markdown snapshot, then append a normalized
   journal event containing the new revision and before/after hashes. A missing
   journal starts a new epoch marked `continuity: unavailable` from the Markdown.
7. Return `BLOCKED` when any conflict, open decision, dangling reference, duplicate
   ID, or uncovered requirement remains.
8. When decision-complete, choose the next repository-wide `SPEC-####` and
   materialize one confirmed Markdown file without product execution authorization.
9. Reopen a confirmed but unimplemented canonical file in place before clarifying a
   possible contract change. Preserve IDs and block delivery while it is working.
10. Before implementation, verify REQ → AC → validation seams. For `implemented`,
    require PASS evidence for every AC and a passing Spec review with no scope creep.
11. Before commit, block staged local bundles and require an explicit delete,
    keep-local, or archive disposition.

## Complexity and forbidden behavior

Parsing, hashing, rendering and validation are linear in bounded specification size
plus candidate count. Each accepted answer performs one atomic snapshot replacement
and one journal append. It is forbidden to infer a choice among multiple candidates,
accept a stale writer, confirm a document with unresolved decisions, reopen an
implemented specification, treat specification persistence as product authorization,
or discard a local canonical spec when tracker publication fails.

## Validation

`tests/test_spec_governance.py` covers stable validation, working-bundle persistence,
journal recovery, stale writers, candidate resolution, ambiguity,
working-to-confirmed-to-reopened-to-implemented lifecycle, commit disposition,
invalid relations, uncovered requirements, and missing evidence. Router integration
tests cover compaction recovery, pre-question reopening, authorization retention and
resumed implementation.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
