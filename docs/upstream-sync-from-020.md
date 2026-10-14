# Upstream merge from governed 0.20.0

User request (2026-10-14): abandon the old 0.21.0 changes and merge the updated
`mattpocock/skills` into the selected 0.20.0 branch.

## Source commits

- Fork base: `c334a7f7a9193f26f8f63ab8922da94c1c7fe282` (`governed-engineering-skills@0.20.0`).
- Upstream: `49dd158d1076134a641b33efb035946536778336` (main, 2026-10-09).
- Excluded former fork tip: `b55c495c2b1825c5a8e37519fe57d99706476074`.

## Integration requirements

1. Merge upstream history into the 0.20.0 base without incorporating the former
   0.21.0 fork commit or untracked files from the original checkout.
2. Integrate upstream promoted skills and supported workflow fixes, preserving
   the fork's automatic engineering router, canonical specifications, execution
   governance, debugging model gate and native installer/release infrastructure.
3. Keep the fork's governed merge skill. Replace writing-great-skills with
   writing-for-agents; add implement-spec, pr, retro, wizard, to-questionnaire and
   wait-what to the exact shipped inventory.
4. Prefer the new GLOSSARY names while recognizing legacy CONTEXT documents and
   preserving empty-document classification.
5. Validate assembly, compatibility inventory, integration, routing, version
   metadata and relevant existing suites. Preserve current governed version
   0.20.0; record the changed sources through the existing pending-release owner
   without applying or publishing a release.

## Conflict decisions

- The fork's persisted one-question-at-a-time discussion and automatic invocation
  overrides take precedence over upstream's stateless/manual wrappers and rounds.
- Parallel implement-spec shares implement's canonical spec and admission gates.
- The fork-owned release workflow remains authoritative; root upstream package
  version machinery and relocated upstream changesets are consolidated into one
  governed changeset rather than a second conflicting release system.
- Fork-specific human-facing workflow documentation keeps its behavioral rules;
  new capabilities and upstream fixes are reflected in the affected pages.
- Upstream retires its generic merge skill, while the fork retains its governed
  merge workflow and corresponding manifest/docs entry.

## Validation

Checks completed against the isolated merge tree on 2026-10-14:

| Check | Result |
| --- | --- |
| Single-source assembly / distribution / artifact validation | PASS, 36 promoted skills |
| Governed version metadata | PASS, current version remains 0.20.0; release intent not applied |
| Assembled plugin contracts | PASS, 395 tests |
| Shared distribution contracts | PASS, 39 tests, including 2 platform skips |
| Architecture module contracts | PASS, 105 tests |
| Governance domain contracts | PASS, 17 tests |
| Verification ladder domain / ladder contracts | PASS, 12 / 32 tests |
| Device/OS contract unit tests | PASS, 70 tests; no physical-device acceptance claim |
| Whole-project layout and source-bound dependency checks | PASS |
| Architecture render and release gate | PASS; baseline SHOULD advisories remain |
| Pinned cached libclang provider verification | PASS |
| Windows local installer / bounded artifact-access contracts | PASS |
| Bash syntax for wizard and debugging HITL templates | PASS |
| Latest upstream wizard and HITL template contents | Byte-identical to pinned upstream |
| Git whitespace and unresolved-conflict checks | PASS |
| Independent Standards review | Reported admission issues repaired and rechecked |
| Independent Spec review | Ownership/layout issues repaired; final layout gate PASS |
| Official Claude marketplace strict validation | PASS |
| Official Claude plugin/root strict validation | Existing CLAUDE.md-context warning, reproduced on clean 0.20.0 baseline |

The complete Python suites ran 670 tests in total (2 platform-condition skips).
An initial Windows atomic-file replacement lock cleared on retry; the complete
395-test plugin suite subsequently passed. The installer fixture's xcopy failed
with a long workspace temporary path and passed with a shorter workspace Temp
path. No installer or atomic-write production code was changed for those issues.

The official Claude validator accepts the plugin manifest in ordinary mode and
warns that root CLAUDE.md is not shipped as plugin context. Strict mode promotes
that same baseline warning to failure. The maintainer context file is retained;
its removal or a new Claude distribution layout is outside this upstream merge.

Two reviewed test files changed their source hashes without changing their
literal dynamic import targets. Their source-bound dependency hashes were
refreshed after review, and the whole-project gate passed. The pinned temporary
clang Python binding remains an ignored build dependency, not a shipped source.

The former 0.21.0 tip is not an ancestor of the merge base. Final parent/history
checks are performed after the merge commit. The original checkout's unrelated
untracked files are not incorporated into this commit.
