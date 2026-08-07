---
spec_version: 1
spec_id: SPEC-0012
revision: 6
status: implemented
change_set: flat-working-spec-storage
---

# Flat working-spec storage

## Problem

The persistent grilling lifecycle stores each discussion under
`.codex/spec-governance/WSP-<random-id>-<slug>/`, with generic `working.md` and
`journal.jsonl` children. Although the bundles share one parent, a developer must
open opaque directories to identify discussions, and `WSP` is not a documented or
readable expansion of "working specification." The directory-per-discussion shape
adds navigation without providing useful separation when every working
specification has exactly one snapshot and one journal.

The existing lifecycle is implemented by SPEC-0010 and therefore cannot be
reopened. This related change set refines its storage contract without changing
canonical `specs/SPEC-####-*.md` placement or product-execution authorization.

## Solution

Store each working snapshot and its journal as a flat, same-stem pair directly
under project-root `spec-governance/`:

```text
spec-governance/
|-- WORKING-SPEC-<id>-<slug>.md
`-- WORKING-SPEC-<id>-<slug>.journal.jsonl
```

Use a stable twelve-hex-character random ID rather than a content hash. Continue
using the separate full SHA-256 `snapshot_hash` field for optimistic concurrency.
When discovery first encounters a legacy `WSP-<id>-<slug>/` bundle, migrate it
transactionally to the flat pair, verify the migrated snapshot and journal, and
only then remove the legacy directory. Any collision, malformed source, stale
writer, or verification failure preserves the legacy source and returns `BLOCKED`.
Treat project-root `spec-governance/` as local working state rather than repository
content, and retain commit preparation as the fail-closed guard against tracked or
staged working files.

Make the Markdown snapshot independently understandable by adding structured
`DISC-###` records for conclusion-changing decisions. Each record preserves the
situation, question, considered options and tradeoffs, the user's visible original
answer, only the rationale the user explicitly stated, the resulting impact, and
links to affected `REQ/DEC/AC` IDs. Do not store a complete transcript, hidden
reasoning, unrelated conversation, credentials, secrets, or unredacted sensitive
personal data. Keep the JSONL journal normalized rather than duplicating the prose
context.

## User Stories

- As a developer browsing project-local governance state, I can identify every
  active discussion from one directory listing.
- As a developer resuming an older discussion, I can continue without manually
  migrating its legacy WSP bundle.
- As a reviewer, I can distinguish the stable working-spec identity from the
  changing content hash.
- As a developer resuming later, I can understand why a requirement or decision
  exists without reopening the original chat.
- As a repository owner, I retain the existing specification-only write exception
  and explicit product-execution boundary.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | New working snapshots MUST use project-root `spec-governance/WORKING-SPEC-<id>-<slug>.md`, and their journals MUST use the exact same stem followed by `.journal.jsonl`. |
| REQ-002 | `<id>` MUST be a stable twelve-character lowercase hexadecimal random identifier that is allocated once and retained for the working specification lifetime; it MUST NOT be described or used as a content hash. |
| REQ-003 | Optimistic concurrency MUST continue to use the full SHA-256 `snapshot_hash`, expected revision, and stale-writer rejection independently of the stable working ID. |
| REQ-004 | `start`, `status`, `resolve`, `reconcile`, `materialize`, `reopen`, and `prepare-commit` MUST read and return the flat WorkingSpecReference paths, and all new writes MUST use only the flat format. |
| REQ-005 | On first discovery or explicit access to a valid legacy `.codex/spec-governance/WSP-<id>-<slug>/` bundle, governance MUST automatically migrate it to project-root `spec-governance/WORKING-SPEC-<id>-<slug>` while preserving the ID, slug, snapshot content, journal events, revision, snapshot hash, continuity, task reference, branch reference, and canonical SPEC relation. |
| REQ-006 | Migration MUST write temporary destination files, validate the complete destination pair and journal chain, publish the destination pair, and remove the legacy source only after verification succeeds. A collision, malformed source, stale state, partial write, or failed verification MUST return `BLOCKED` and leave the legacy source recoverable. |
| REQ-007 | Candidate resolution MUST consider flat and legacy representations without double-counting one logical working specification during migration; ambiguity MUST still fail closed and MUST NOT be resolved by recency. |
| REQ-008 | An explicit legacy `WSP-<id>-<slug>` reference MUST act as a migration input and return the new `WORKING-SPEC-<id>-<slug>` reference after successful migration. |
| REQ-009 | Project-root `spec-governance/` MUST be treated as local working state rather than repository content. Governance MUST NOT stage or commit it, and commit preparation MUST detect tracked or staged flat snapshots and journals while preserving the existing delete, keep-local, or archive disposition contract. |
| REQ-010 | Canonical specifications MUST remain under `specs/SPEC-####-*.md`; this change MUST NOT alter canonical numbering, reopening rules, implementation authorization, tracker authority, or the prohibition on reopening implemented specifications. |
| REQ-011 | The schema, skill contracts, architecture manifest, generated Description Views, ADR-0011 proposal, ALG-0004 proposal, tests, integration validation, and release metadata MUST describe and validate the same flat storage and migration behavior. |
| REQ-012 | Every WORKING-SPEC Markdown snapshot MUST contain a human-readable `Discussion Context` section with stable `DISC-###` records for each conclusion-changing user decision. |
| REQ-013 | Each `DISC-###` record MUST contain the situation, decision question, options and material tradeoffs, the user's visible original answer, explicitly stated rationale or `not stated`, resulting impact, and links to affected `REQ/DEC/AC` IDs. It MUST NOT infer an unstated rationale. |
| REQ-014 | Discussion Context MUST exclude complete transcripts, hidden reasoning, unrelated conversation, credentials, secrets, and unredacted sensitive personal data. Required redaction MUST retain a visible reason marker rather than silently altering the answer. |
| REQ-015 | The normalized journal MUST record affected `DISC-###` IDs in its delta and hash chain but MUST NOT duplicate the Discussion Context prose or raw chat. The Markdown snapshot remains authoritative when journal continuity is unavailable. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Replace the directory-per-discussion layout with a flat snapshot/journal pair under project-root `spec-governance/`. |
| DEC-002 | Replace the undocumented `WSP` prefix with the explicit `WORKING-SPEC` prefix. |
| DEC-003 | Use a stable random ID, not an initial or revision-changing content hash, in the filename. |
| DEC-004 | Pair the journal by the exact snapshot stem plus `.journal.jsonl`. |
| DEC-005 | Automatically migrate legacy bundles on first read instead of requiring manual migration or rejecting legacy state. |
| DEC-006 | Make migration transactional and fail closed while preserving the source on every collision or verification failure. |
| DEC-007 | Keep canonical specification placement and authorization boundaries unchanged. |
| DEC-008 | Keep this bootstrap discussion in chat rather than creating the legacy WSP structure that this change replaces; materialize only this decision-complete canonical specification. |
| DEC-009 | Keep project-root `spec-governance/` local and commit-blocked rather than treating working discussion state as repository-tracked content. |
| DEC-010 | Preserve structured decision context in the human-readable snapshot instead of only the normalized final contract. |
| DEC-011 | Preserve the user's visible original answer, while summarizing the question, options, tradeoffs, and impact and recording only explicitly stated rationale. |
| DEC-012 | Keep the JSONL journal normalized and free of transcript prose; use stable `DISC-###` IDs to connect journal deltas to the authoritative Markdown context. |

## Discussion Context

### DISC-001: Flatten the working-spec layout

- **Situation:** The existing WSP directory-per-discussion layout was considered
  difficult to browse.
- **Question:** Keep one directory per discussion or use flat same-stem files?
- **Options and tradeoffs:** Nested bundles group future attachments with lower
  migration cost; flat files make all active discussions visible in one listing.
- **User answer:** `為何建議1?我認為扁平結構不是比較好`
- **Explicit rationale:** The user preferred the flatter, less scattered structure.
- **Resulting impact:** REQ-001, DEC-001.

### DISC-002: Choose a readable working identity

- **Situation:** `WSP` was not formally expanded and the random token was being
  called a hash.
- **Question:** Which readable prefix and identity semantics should replace it?
- **Options and tradeoffs:** A stable random ID preserves paths; content hashes
  either become stale or force renames after reconciliation.
- **User answer:** `選擇WORKING-SPEC-<hash>-<slug>` followed by selection `1` for a
  stable random ID.
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** REQ-002, REQ-003, DEC-002, DEC-003.

### DISC-003: Migrate legacy WSP bundles

- **Situation:** Existing projects may already contain valid WSP bundles.
- **Question:** Read legacy and write new, automatically migrate on first read, or
  reject legacy state?
- **Options and tradeoffs:** Automatic migration unifies the layout but requires a
  transactional fail-closed path.
- **User answer:** `2`
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** REQ-005, REQ-006, REQ-007, REQ-008, DEC-005, DEC-006.

### DISC-004: Move working state to the project root

- **Situation:** The first confirmed proposal still placed new files under
  `.codex/spec-governance/`.
- **Question:** Which root and Git policy should own working discussion state?
- **Options and tradeoffs:** Project-root `spec-governance/` is directly visible,
  while local commit-blocked state avoids review noise and merge conflicts.
- **User answer:** `我想直接移到專案資料夾下的/spec-governance`, followed by
  selection `1` for local, untracked state.
- **Explicit rationale:** The user did not want the working files under
  project-root `.codex/`.
- **Resulting impact:** REQ-001, REQ-005, REQ-009, DEC-001, DEC-009.

### DISC-005: Retain human-readable discussion context

- **Situation:** A normalized specification preserves conclusions but not enough
  context to understand why they were reached.
- **Question:** Preserve structured context, structured context plus selected
  excerpts, or the complete visible transcript?
- **Options and tradeoffs:** Structured context is readable and bounded; excerpts
  and full transcripts increase fidelity at the cost of size, privacy risk, and
  unrelated content.
- **User answer:** `選擇1`
- **Explicit rationale:** The user stated: `我想保留當時的討論情境`.
- **Resulting impact:** REQ-012, REQ-013, REQ-014, REQ-015, DEC-010, DEC-011,
  DEC-012.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003, REQ-004 | Starting and reconciling a new discussion creates only the flat same-stem pair, retains the same stable ID across revisions and reloads, and rejects stale revision or snapshot-hash writers without changing either file. | Focused temporary-repository unit tests for start, reload, reconcile, and stale writers. | PASS: flat-path, stable-ID, reconciliation, reload, and stale-writer unit tests passed in the 43-test focused suite. |
| AC-002 | REQ-005, REQ-006, REQ-008 | First access to a valid legacy bundle produces a verified flat pair with equivalent metadata and journal continuity, returns the new reference, and removes the legacy directory only after success. | Migration unit tests with valid snapshot and journal fixtures. | PASS: migration tests verified equivalent snapshot content, task/branch metadata, event revision and continuity, returned new reference, and post-verification source removal. |
| AC-003 | REQ-006, REQ-007 | Destination collision, malformed source, tampered journal, simulated partial write, or ambiguous candidates return `BLOCKED`, preserve the legacy source byte-for-byte, and do not expose a partial destination as valid. | Fail-closed migration and resolver fixture tests. | PASS: valid-destination collision, stale terminal hash, invalid chain, ambiguity, and simulated second-file publication failure tests passed with byte-preserving rollback. |
| AC-004 | REQ-004, REQ-007, REQ-009, REQ-010 | Materialization and reopening continue to resolve the correct canonical SPEC, while commit preparation detects flat local files and returns the unchanged three disposition options without performing an action. | Lifecycle, resolver, reopen, materialize, and commit-preparation tests. | PASS: lifecycle, implemented-reopen rejection, resolver, staged-path, and non-performing disposition tests passed. |
| AC-005 | REQ-011 | Public contracts, architecture descriptions, algorithm record, proposed ADR, generated views, plugin documentation, and release metadata agree on the new path and migration semantics and contain no normative legacy-write requirement. | Contract search, schema tests, deterministic render check, integration validation, and version-governance check. | PASS: integration validated 28 skills; generated views and architecture development gate passed; version governance passed. |
| AC-006 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015 | The complete plugin regression and two-axis review find no missing required behavior, incorrect behavior, or scope creep. | Full automated test suite followed by Standards and Spec code review. | PASS: all 157 plugin tests passed; Standards review PASS; SpecTraceabilityAssessment PASS with no uncovered IDs or scope creep. |
| AC-007 | REQ-012, REQ-013 | After several decisions and a process-equivalent reload, the Markdown snapshot renders stable `DISC-###` records containing every required field, exact retained user answers, explicit `not stated` rationale markers, and valid affected-ID links. | Focused renderer, reconciliation, stable-ID, reload, and schema tests. | PASS: DISC reconciliation, stable-ID delta, required-field, affected-link, exact-answer, and reload assertions passed. |
| AC-008 | REQ-014, REQ-015 | Transcript-only and unrelated messages are excluded, sensitive fixtures are visibly redacted, hidden reasoning is absent, and journal events contain affected DISC IDs without context prose. | Privacy-boundary, redaction, normalized-journal, tamper, and missing-journal recovery tests. | PASS: snapshot-wide credential/personal-data redaction, H1 single-exchange transcript rejection, hidden-reasoning checks, normalized DISC-only journal, tamper, and recovery assertions passed. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| SPEC-0012 | refines | SPEC-0010 |
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-002 |
| REQ-002 | depends_on | DEC-003 |
| REQ-003 | depends_on | DEC-003 |
| REQ-005 | depends_on | DEC-005 |
| REQ-006 | depends_on | DEC-006 |
| REQ-009 | depends_on | DEC-009 |
| REQ-010 | depends_on | DEC-007 |
| REQ-012 | depends_on | DEC-010 |
| REQ-013 | depends_on | DEC-011 |
| REQ-014 | depends_on | DEC-011 |
| REQ-015 | depends_on | DEC-012 |
| AC-001 | depends_on | REQ-004 |
| AC-002 | depends_on | REQ-008 |
| AC-003 | depends_on | REQ-007 |
| AC-004 | depends_on | REQ-010 |
| AC-005 | depends_on | REQ-011 |
| AC-006 | depends_on | REQ-011 |
| AC-007 | depends_on | REQ-013 |
| AC-008 | depends_on | REQ-015 |

## Architecture Impact

- **Affected level and owner:** existing L2 `spec_governance_domain` under
  `delivery_workflow_domain`; no module is added, split, merged, or reparented.
- **Affected public contract:** `WorkingSpecReference.working_id`,
  `snapshot_path`, and `journal_path` patterns change. The existing
  `spec-governance.start`, `reconcile`, `materialize`, `reopen`, and
  `prepare-commit` Ports retain their ownership and synchronous behavior.
- **Affected content contract:** working snapshots gain required stable
  `DISC-###` records and normalized reconciliation deltas gain affected DISC IDs;
  the Markdown remains authoritative and the journal remains owner-private
  machine history.
- **Dependencies and mappings:** no dependency edge, parent mapping, event,
  state-object owner, runtime adapter, composition root, ABI, wire contract, or
  external storage contract is added.
- **Flow:** `governed-change-set-lifecycle.start` and `.reconcile` retain their
  order and atomic persistence invariant but write flat pairs. Start/status/resolve
  gain a bounded legacy-migration branch. Failure continues through
  `spec-governance.blocked`.
- **Description Views impact:** update the manifest descriptions for
  `spec_governance_domain`, WorkingSpecReference, affected Ports, and the
  governed-change-set lifecycle; regenerate `architecture/ARCHITECTURE.md`,
  `architecture/generated/system.md`, and
  `architecture/generated/delivery_workflow_domain.md`. No other Parent or
  execution page should change.
- **ADR impact:** revise proposed ADR-0011 because flat storage changes its proposed
  working-bundle representation. No MUST-rule exception or self-approved ADR is
  required.

## Algorithm Impact

The canonical-specification lifecycle remains algorithm-bearing because candidate
resolution, stable identity, transactional migration, collision handling, journal
verification, stale-writer behavior, DISC-ID preservation, context redaction, and
answer-to-contract linkage affect observable results and recovery. Revise proposed
`ALG-0004`; do not allocate a second algorithm record. Its owner remains
`spec_governance_domain`, and its public architecture effect is limited to
WorkingSpecReference path, identity patterns, and working-snapshot content.

## Flow Execution Impact

The affected flow is best-effort and has no latency, throughput, memory, power, or
real-time budget. The selected flat-plus-migration candidate performs bounded local
filesystem I/O linear in the snapshot and journal size. Current nested storage and
flat storage without migration were considered: nested storage has lower
implementation cost but retains the navigation problem; no-migration flat storage
breaks existing discussions. Transactional auto-migration is selected because it
preserves functional continuity and the requested browsing behavior.

The cost model is `estimated`. That is sufficient for directional comparison because
the change adds no Task, Thread, Queue, callback, retry loop, platform dependency, or
performance claim. Functional admission still requires atomic publication,
source preservation on failure, deterministic ambiguity handling, and unchanged
optimistic concurrency.

## Evolution Impact

- **Add a discussion:** one same-stem pair appears in the existing directory; no
  new nested directory is created.
- **Add a reader or adapter:** it consumes WorkingSpecReference rather than deriving
  paths independently; legacy parsing remains localized in spec governance.
- **Add a processing stage:** reconciliation and materialization continue to use
  the same stable reference and require no sibling dependency.
- **Add an attachment:** out of scope; a later change must define whether attachments
  use a related stem or a separate storage owner.
- **Add a platform variant:** no impact because storage is project-relative,
  UTF-8, best-effort local filesystem state with no platform-performance claim.

## Alternatives Considered

1. **Keep one directory per WSP:** lowest migration cost and naturally groups future
   attachments, but retains opaque navigation and generic child filenames.
2. **Use a flat current-content hash:** makes the filename content-verifiable but
   renames it on every reconciliation, breaking stable references and stale-writer
   handling.
3. **Use an initial-content hash:** keeps the filename stable but becomes misleading
   after the first reconciliation.
4. **Reject or manually migrate legacy bundles:** simplifies implementation but
   makes existing discussions unavailable or imposes manual recovery.
5. **Flat stable-ID pair with first-read migration:** selected because it provides
   direct directory visibility, stable identity, and backward continuity with a
   bounded fail-closed migration cost.
6. **Normalized contract without discussion context:** compact but cannot explain
   why a decision exists after the original chat is unavailable.
7. **Selected excerpts or a complete transcript:** preserves more wording but adds
   unrelated content, privacy risk, and review noise. Structured DISC records are
   selected instead.

## Implementation Order

1. Add failing tests for flat creation, pairing, reload, stale writers, migration,
   collision, tampered journal, ambiguity, canonical lifecycle, commit preparation,
   structured DISC rendering, stable DISC IDs, redaction, and journal separation.
2. Update WorkingSpecReference schema and central path/identity helpers.
3. Implement transactional legacy discovery and migration behind the existing
   spec-governance entry points.
4. Extend reconciliation and rendering with structured Discussion Context while
   keeping journal events normalized and free of transcript prose.
5. Update lifecycle behavior and all bundled skill/path/content contracts.
6. Revise the architecture manifest, proposed ADR-0011, proposed ALG-0004, and
   regenerate Description Views.
7. Update changeset and release metadata, then run focused, integration, full,
   version, architecture, and two-axis review gates.

## Validation Matrix

| Scope | Command or steps | Expected observable output | Pass condition | Evidence format |
|---|---|---|---|---|
| Canonical SPEC | `python skills/spec-governance/scripts/spec_contract.py validate --spec specs/SPEC-0012-flat-working-spec-storage.md` | JSON verdict with no structural or traceability errors. | Exit 0 and `PASS`. | Command, exit code, minimal JSON output. |
| Focused lifecycle | `python -m unittest tests.test_spec_governance -v` | Flat-path, migration, failure, resolver, lifecycle, and commit tests all report `ok`. | Exit 0 with zero failures/errors. | Console output plus test count. |
| Routing/contracts | `python -m unittest tests.test_decision_question_contract tests.test_guided_routing -v` | No skill or routing contract retains contradictory legacy-write behavior. | Exit 0 with zero failures/errors. | Console output plus test count. |
| Integration | `python scripts/validate_integration.py` | Plugin integration validation succeeds. | Exit 0. | Command, exit code, minimal output. |
| Version governance | `python scripts/version_governance.py check` | Package, manifest, changelog, changeset, release state, and fingerprint agree. | Exit 0. | Command, exit code, minimal output. |
| Architecture | `python tools/architecture/architecture_cli.py gate --phase development --manifest architecture/manifest.yaml --adoption architecture/adoption.yaml --baseline architecture/baseline.yaml --format text` | Schema, Python AST evidence, deterministic generated views, and empty baseline pass. | Exit 0 and architecture `PASS`. | Command, exit code, diagnostics summary. |
| Full regression | `python -m unittest discover -s tests -v` | Entire plugin suite completes with no failures or errors. | Exit 0. | Console output plus test count. |
| Review | Run governed two-axis code review against the implementation fixed point. | Standards and Spec reports identify no blocking finding. | Both axes PASS. | Review reports linked to the implementation revision. |

## Out of Scope

- Moving canonical `specs/SPEC-####-*.md` files into `.codex/`.
- Reopening or rewriting implemented SPEC-0010 or SPEC-0011.
- Changing product execution authorization, tracker publication, canonical
  numbering, journal contents, or commit disposition choices.
- Adding working-spec attachments, an index database, a cleanup daemon, or
  cross-repository storage.
- Persisting this bootstrap discussion in the legacy WSP layout.
- Saving a complete visible transcript, unrelated conversation, hidden reasoning,
  credentials, secrets, or unredacted sensitive personal data.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS - the user selected a flat pair, the explicit `WORKING-SPEC`
  prefix, a stable random ID, automatic first-read migration, and chat-only
  bootstrap reconciliation.
- Spec reconciliation: PASS - the user selected structured discussion context;
  stable DISC records, retained visible answers, explicit-rationale boundaries,
  redaction, affected-ID links, and normalized-journal separation have acceptance
  coverage with no open decision.
- Architecture proposal: PASS - the change remains within the existing
  `spec_governance_domain`; the intended manifest and Description View changes are
  identified, with no new owner, dependency, runtime state, or execution unit.
- Algorithm screening: PASS for design - revise proposed ALG-0004 with transactional
  migration and stable-ID behavior; no second algorithm owner is introduced.
- Flow-cost review: estimated PASS for directional selection - best-effort bounded
  local I/O, no product performance claim, and explicit fail-closed functional
  admission.
- Implementation authorization: PASS - the user issued exact `開始執行`.
- Spec review: PASS - no uncovered requirements or acceptance criteria and no
  scope creep.
- Required implementation gates: PASS - TDD, architecture development gate,
  complete validation matrix, and two-axis code review passed.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-07 | Materialized the confirmed flat working-spec storage and migration contract from chat-only reconciliation. |
| 2 | 2026-08-07 | Reopened after the user corrected the target storage root to project-root `spec-governance/`; tracking policy remains open. |
| 3 | 2026-08-07 | Reconfirmed project-root `spec-governance/` as local, commit-blocked working state and retained `.codex/spec-governance/WSP-*` only as a legacy migration source. |
| 4 | 2026-08-07 | Reopened after the user requested preservation of the human-readable discussion context; retention granularity remains open. |
| 5 | 2026-08-07 | Reconfirmed structured DISC records with visible original answers, explicit-rationale boundaries, privacy exclusions, affected-ID links, and normalized-journal separation. |
| 6 | 2026-08-07 | Recorded implementation PASS evidence after full regression, integration, architecture, version, and two-axis review gates passed. |
