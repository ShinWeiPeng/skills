# ALG-0004: Canonical specification reconciliation

## Metadata

- Status: proposed
- Owner module: `spec_governance_domain`
- Product feature: Canonical change-set specification lifecycle
- Flow IDs: `governed-change-set-lifecycle`
- Related ADRs: `ADR-0011`
- Source paths:
  - `skills/engineering/spec-governance/scripts/spec_contract.py`
  - `skills/engineering/spec-governance/references/spec-contract.schema.json`
- Test and benchmark paths: `plugins/governed-engineering-skills/tests/test_spec_governance.py`
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

1. Start or resolve one flat
   `spec-governance/WORKING-SPEC-<hash>-<slug>.{md,journal.jsonl}` pair by explicit
   reference, available task/branch evidence, then unique fallback; ambiguity blocks
   instead of selecting by recency. On first read, transactionally migrate a valid
   legacy `.codex/spec-governance/WSP-*` bundle and preserve it if migration fails.
2. Reject a delta when its expected revision or snapshot hash is stale.
3. Classify each delta as a domain term, change-set contract, ADR candidate, or open
   decision.
4. Reuse stable `REQ-###`, `DEC-###`, `AC-###`, and `DISC-###` IDs; assign the next
   unused ID only to genuinely new statements. Each discussion record captures the
   situation, question, options and tradeoffs, user answer, explicit rationale, and
   resulting impact. Redact recognized credentials and sensitive personal data with
   a visible reason marker, and reject transcript or hidden-reasoning structures.
5. Compare the working contract with `CONTEXT.md`, accepted ADRs, and the architecture
   manifest; report affected IDs, relations, conflicts, and open decisions.
6. Atomically replace the authoritative Markdown snapshot, then append a normalized
   journal event containing the new revision, before/after hashes, and affected
   `DISC-###` IDs only; journal events do not duplicate discussion prose. A missing
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

`plugins/governed-engineering-skills/tests/test_spec_governance.py` covers stable validation, working-bundle persistence,
journal recovery, stale writers, candidate resolution, ambiguity,
working-to-confirmed-to-reopened-to-implemented lifecycle, commit disposition,
invalid relations, uncovered requirements, and missing evidence. Router integration
tests cover compaction recovery, pre-question reopening, authorization retention and
resumed implementation.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending

## SPEC-0020 continuity extension

Approved scope: task 01a085c7-8a93-7a73-b625-2b09168538ec, plugin-only repair
selected by the user and explicitly authorized with 開始執行.

Persist one versioned question inside the authoritative Markdown before presenting
options. Recovery has no time input: elapsed time cannot change pending state.
Require explicit non-empty answer, matching question version, matching working
revision/hash and a new DISC record before clearing the question. Duplicate or
stale responses preserve the previous snapshot. Other open decisions and conflicts
remain blockers. Delivery reloads canonical identity, current file hash and
traceability plus working identity/status before admitting the original human
execution instruction. No global host interception is claimed.

Validation: test_turn_continuity.py covers restart, stale/duplicate answers,
read-only follow-ups, conflict preservation and explicit delivery admission.

## SPEC-0022 execution boundary extension

Route success carries no product-write permission. The delivery parent observes
the selected workflow before dependent tools. Spec-owned execution receipts bind
project/task identity and exact canonical, snapshot and journal hashes. Managed
operations serialize receipt changes, reject stale or suspended state, then check
one reviewed target hash before atomic replacement. This conservative equality
policy rejects even non-semantic revision drift; it never refreshes old evidence.
Direct host tools and caller-authored evidence authenticity remain outside the
plugin guarantee. Validate both managed denial hash invariants and actual assistant
trace behavior across project types; missing model trace evidence stays BLOCKED.

## Revision authorization refinement (SPEC-0023)

Materialization always returns authorization_retained=false. Semantic-delta
classification remains descriptive only. Every revision requires fresh explicit
execution authorization, including no-delta reconfirmation and evidence updates.
The existing managed receipt hash binding rejects prior-state execution.

## Discussion completion (SPEC-0024)

The existing SPEC context now includes a read-only continuation assessment.
Mixed user messages preserve all answers, changes and factual questions; reconcile
before selecting the next pending decision. Completion compares current saved
question identity/version/content and working context with observed presentation.
A persisted decision with remaining open decisions cannot end a turn without a
question, concrete evidenced blocker or explicit discussion pause. With decisions
complete, materialize and present the proposal. This deterministic assessment
and per-turn delivery trace audit own no additional persistent state and never
authorize product execution. Source observation authenticity remains caller-attested.
