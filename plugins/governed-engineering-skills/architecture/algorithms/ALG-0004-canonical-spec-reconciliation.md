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
change-set contract without writing before authorization or repeating the interview
in a later task. Success is a deterministic `PASS` or `BLOCKED` assessment with
stable IDs and an unambiguous canonical path.

## Inputs, outputs, and assumptions

Inputs are the current working specification, one discussion delta, repository
formal context, accepted ADRs, the architecture manifest, optional tracker and branch
evidence, and repository `specs/`. Outputs are `SpecContextAssessment`,
`SpecConsistencyAssessment`, `CanonicalSpecReference`, and
`SpecTraceabilityAssessment`. Repository files are UTF-8 Markdown.

## Ordered method

1. Classify each delta as a domain term, change-set contract, ADR candidate, or open
   decision.
2. Reuse stable `REQ-###`, `DEC-###`, and `AC-###` IDs; assign the next unused ID only
   to genuinely new statements.
3. Compare the working contract with `CONTEXT.md`, accepted ADRs, and the architecture
   manifest; report affected IDs, relations, conflicts, and open decisions.
4. Return `BLOCKED` when any conflict, open decision, dangling reference, duplicate
   ID, or uncovered requirement remains.
5. After explicit authorization, choose the next repository-wide `SPEC-####` and
   materialize one confirmed Markdown file.
6. Resolve later context by explicit path, tracker path, branch match, then unique
   confirmed fallback; ambiguity blocks instead of selecting by recency.
7. Before implementation, verify REQ → AC → validation seams. For `implemented`,
   require PASS evidence for every AC and a passing Spec review with no scope creep.

## Complexity and forbidden behavior

Parsing and validation are linear in bounded specification size plus candidate count.
It is forbidden to write during reconciliation, infer a choice among multiple
candidates, confirm a document with unresolved decisions, mutate a standalone
review, or discard a local canonical spec when tracker publication fails.

## Validation

`tests/test_spec_governance.py` covers stable validation, empty and legacy context,
candidate resolution, ambiguity, confirmed-to-implemented lifecycle, invalid
relations, uncovered requirements, and missing evidence. Router integration tests
cover cross-task verification and resumed implementation.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
