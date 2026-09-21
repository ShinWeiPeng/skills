# SPEC-0036 implementation verification

Canonical contract: specs/SPEC-0036-generic-layout-repair.md, revision 61, confirmed.
Execution authority was reused from the actual authorized source; only the two bootstrap files used the explicit direct-write exception. Subsequent product patches went through managed apply.

## Implemented

- Common modification admission checks SPEC and authorization separately from the results the change will produce. Final acceptance remains enforced.
- Layout checks directories, classification, owners, provenance and references without dependency/AST/isolation gates. Independent architecture checks remain intact.
- Shared SPEC saving waits up to 30 seconds, rereads under lock, can merge verified disjoint baselines, rejects conflicting edits and prevents reopen rollback over newer saves.
- Completeness review no longer confirms a SPEC without an observed explicit user confirmation source. New/revised choices require at least three options; legacy questions remain readable.
- Schema-2 acceptance definitions are regenerated from SPEC, including removals and same-ID changes. The validation consumer verifies the exact projection and preserves hardware layer requirements. Evidence is separate.
- Shared skill policy and human documentation cover history, resumption, authorization, saving and final validation. Historical SPEC files and installed plugin caches were not rewritten.

## Actual checks

See checks.json for exact commands, exit codes and logs. Plugin regression covers short instructions, bounded recovery, legacy acceptance repair, authorization revocation, numeric-ID masking, discussion/confirmation and the new lock/generation cases. Module tests cover layout and project verification. Distribution and formatting checks are included.

## Remaining acceptance gaps

The actual completion entry remains BLOCKED. SPEC-0036 has 21 human-readable criteria and methods; its prose verification plan does not contain the structured evidence-claim/applicability selectors expected by the existing ladder. All 21 definitions were generated, but missing selectors were not invented. This is a planning-data gap, not failure of an executed HIL test. Hardware tests are not applicable to this host-tool change.

Real Codex host hook firing and visible multi-turn response behavior were not established by these fixture/CLI tests. Actual Linux desktop installation was not executed on this Windows host. Therefore the SPEC remains confirmed, not implemented, and this run is BLOCKED for overall acceptance even if all independent automated checks pass.

No further source changes require new permission while revision 61 and its authority remain current. Changing SPEC to add machine-readable selectors would be a revision and, under the user's adopted rule, revoke its existing execution authority. This run did not revise SPEC or silently reauthorize it.

## Compatibility disposition

SPEC-0031: retained; short-command regressions executed.
SPEC-0032: retained bounded recovery; regressions executed.
SPEC-0033: legacy pending-state and repair compatibility retained. One reproduced incompatibility was corrected: legacy preparation now accepts its same-source valid executing receipt after the first repair resumes work. New work uses the common apply entry.
SPEC-0034: confirmation behavior changed only as explicitly required by SPEC-0036; complete review alone is insufficient.
SPEC-0035: compatibility inventory retained; missing future validation results no longer block authorized apply/status, while complete still checks validation. Revisions still invalidate old authority.

Actual completion diagnostics:

```json
[
  "AC-001: evidence claims and applicability rationale required"
]
```
