---
spec_version: 1
spec_id: SPEC-0017
revision: 8
status: confirmed
change_set: ai-authorship-format-all
---

# SPEC-triggered full formatting confirmation

## Problem

The implemented formatter policy preserves non-greenfield repository style and does
not ask whether an existing specification should trigger formatting of the whole
program source tree.

## Solution

When a repository contains a governed canonical SPEC, ask the user whether to run
the applicable formatter over product source and test files. Execute no formatting
write unless the user answers affirmatively. Exclude documentation, configuration,
generated files, vendored dependencies, and build artifacts from this full-program
scope.

For a non-greenfield project, first use its discoverable repository CLI formatter.
When no repository CLI formatter is discoverable, fall back to the formatter mapped
by Governed Engineering for the applicable language. Greenfield projects continue
to use the governed formatter mapping. If the selected formatter CLI is unavailable
locally, request native authorization immediately before downloading or installing
it; denial, failure, or unavailable permission evidence is `BLOCKED`.

Before an authorized full-format write, require all targeted product source and test
files to have no pre-existing uncommitted changes; otherwise stop without
formatting. Run both the formatter write and its non-mutating follow-up check through
a deterministic non-interactive CLI. IDE UI operations are not authoritative
evidence. The formatter gate requires the formatter's own CLI check but does not add
a separate semantic checker; normal project tests, typechecking, and builds remain
in the ordinary delivery validation flow.

## User Stories

- As a repository maintainer, I want a SPEC-aware confirmation before any full-source formatting write.
- As a repository maintainer, I want pre-existing edits protected from being mixed with formatter changes.
- As a maintainer and CI operator, I want formatter execution and evidence reproducible without a specific IDE installation.
- As a maintainer of a project without formatter CLI policy, I want a governed fallback and an explicit installation boundary.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | When a governed canonical SPEC exists, the formatter workflow MUST ask whether to format the confirmed complete program-source scope and MUST NOT perform the write without an affirmative answer. |
| REQ-002 | The complete program-source scope MUST include product source and tests and MUST exclude documentation, configuration, generated files, vendored dependencies, and build artifacts. |
| REQ-003 | Formatter selection MUST use a discoverable repository CLI formatter for a non-greenfield project; when none is discoverable, it MUST fall back to the Governed Engineering language mapping. Greenfield projects MUST use the governed mapping. |
| REQ-004 | Before an authorized full-format write, the workflow MUST verify that every targeted product-source and test file has no pre-existing uncommitted change and MUST report `BLOCKED` without formatting when any target is dirty. Unrelated dirty files outside the target scope MUST remain untouched and MUST NOT independently block the operation. |
| REQ-005 | The authorized formatter write and follow-up non-mutating formatter check MUST use deterministic non-interactive CLI commands for the selected formatter and MUST NOT require VS Code, Eclipse, another IDE UI, or a separate semantic checker. Existing tests, typechecks, and builds MUST remain governed by the normal delivery validation flow. |
| REQ-006 | When the selected formatter CLI is unavailable locally, the workflow MUST request native authorization immediately before downloading or installing it and MUST report `BLOCKED` without substitution when authorization is denied, missing, or the installation fails. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Treat canonical SPEC presence as a confirmation trigger, not as proof of AI authorship or automatic authorization to format. |
| DEC-002 | Define “全部程式” as product source plus tests, excluding documentation, configuration, generated files, vendor content, and build artifacts. |
| DEC-003 | Reuse the formatter precedence already settled by SPEC-0016 instead of asking the user to choose again. |
| DEC-004 | Fail closed when any targeted program file has a pre-existing uncommitted change, while allowing unrelated dirty files to remain untouched. |
| DEC-005 | Use the selected formatter's CLI for both write and check; do not treat IDE formatting as authoritative evidence and do not add formatter-specific semantic validation beyond the CLI check. |
| DEC-006 | Extend formatter precedence with a governed language fallback when a non-greenfield repository has no discoverable formatter CLI. |
| DEC-007 | Download or install a missing selected formatter CLI only through the existing native permission boundary. |

## Discussion Context

### DISC-001: SPEC-triggered confirmation

- **Situation:** SPEC presence is deterministic but does not prove AI authorship; automatic full formatting could unexpectedly rewrite an established repository.
- **Question:** How should SPEC presence affect formatter behavior?
- **Options and tradeoffs:** Automatic formatting is simple but risky; explicit SPEC metadata is precise but requires maintenance; asking when a SPEC exists is deterministic while preserving user control.
- **User answer:** `有SPEC後，再用詢問的方式確認是否要formatter`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-001, DEC-001, AC-001.

### DISC-002: Complete program-source scope

- **Situation:** “全部程式” could mean all formatter-supported repository files, only product source, or product source plus tests.
- **Question:** Which files belong to the full-format scope?
- **Options and tradeoffs:** Formatting every supported file maximizes uniformity but creates broad churn; product source only minimizes changes but leaves tests inconsistent; product source plus tests keeps executable code consistent while excluding unrelated repository content.
- **User answer:** `1`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-002, DEC-002, AC-002.

### DISC-003: Formatter precedence is already governed

- **Situation:** A follow-up question asked which formatter to use when repository tooling differs from the governed default.
- **Question:** Is another user decision required?
- **Options and tradeoffs:** Asking again permits an override but contradicts the settled non-greenfield policy; reusing SPEC-0016 avoids contradictory decisions and preserves repository conventions.
- **User answer:** `這是什麼問題情境?`
- **Explicit rationale:** The response requested clarification rather than selecting an override.
- **Resulting impact:** Repository evidence from SPEC-0016 REQ-002 and DEC-001 originally resolved REQ-003, DEC-003, and AC-003 without another user choice; DEC-006 later supersedes that decision for repositories without a CLI formatter.

### DISC-004: Pre-existing target changes

- **Situation:** A formatter write can mix its output with user edits that already exist in targeted product source or tests, even though the governed workflow has not yet authored product changes.
- **Question:** What precondition should apply when targeted files already have uncommitted changes?
- **Options and tradeoffs:** Requiring clean target files prevents mixed diffs but requires the owner to resolve existing work first; proceeding allows faster execution but makes ownership and recovery ambiguous.
- **User answer:** `1`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-004, DEC-004, AC-004.

### DISC-005: Reproducible formatter execution and validation

- **Situation:** VS Code and Eclipse can expose mature formatters, but IDE installations, extensions, profiles, and default-formatter selections vary and are not reliable headless evidence. The repository already has deterministic formatter CLI commands and its ordinary delivery validation tools.
- **Question:** Should IDE formatting, IDE-assisted writing with a CLI check, or CLI-only write and check be authoritative?
- **Options and tradeoffs:** IDE-only execution is convenient but not reproducible in CI; IDE-assisted writing plus CLI checking preserves interactive convenience but creates two execution paths; CLI-only write and check provides one automatable path while leaving ordinary tests and builds to the delivery workflow.
- **User answer:** `3`
- **Explicit rationale:** The user prefers existing mature formatter tooling and selected CLI-only formatter write and check.
- **Resulting impact:** REQ-005, DEC-005, AC-005.

### DISC-006: Missing repository or local formatter CLI

- **Situation:** A non-greenfield repository may have no discoverable formatter CLI, and the governed fallback CLI may not yet be installed locally.
- **Question:** What fallback and installation policy should apply?
- **Options and tradeoffs:** Blocking without fallback preserves existing-project conservatism but prevents formatting; IDE fallback is not reproducible; governed CLI fallback gives deterministic coverage but may require an authorized download or installation.
- **User answer:** `使用專案既有 CLI formatter 執行 write 與 check，如果專案沒有既有的 CLI formatter，則使用governed engirneering skill定義的formatter，如果本機沒有相對應的formatter CLI，則進行下載`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-003, REQ-006, DEC-006, DEC-007, AC-003, AC-006.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | A canonical-SPEC fixture produces one formatter confirmation; affirmative input may continue, while decline or ambiguity performs no formatting write. | Focused contract and temporary-directory integration tests. | Pending execution. |
| AC-002 | REQ-002 | A mixed-file fixture selects product source and tests while excluding documentation, configuration, generated, vendor, and build-output paths. | Focused scope-classification tests. | Pending execution. |
| AC-003 | REQ-003 | Non-greenfield fixtures retain a discoverable repository CLI formatter and select the governed language formatter only when no repository CLI is discoverable; greenfield fixtures use the governed mapping. | Focused formatter-precedence and fallback tests. | Pending execution. |
| AC-004 | REQ-004 | A dirty targeted source or test fixture returns `BLOCKED` with byte-identical files; a fixture dirty only outside the selected scope may continue and preserves unrelated files. | Temporary-repository integration tests with Git status and before/after hashes. | Pending execution. |
| AC-005 | REQ-005 | Greenfield and non-greenfield fixtures require explicit CLI write and check argv, reject IDE-only evidence, accept the selected formatter's successful non-mutating CLI check, and leave project tests/typechecks/builds to the delivery validation contract. | Focused policy-contract and integration tests. | Pending execution. |
| AC-006 | REQ-006 | Missing-CLI fixtures require native installation authorization; denial, missing evidence, and installation failure remain `BLOCKED`, while authorized successful installation proceeds to the non-mutating formatter check. | Focused permission-boundary and temporary-environment tests. | Pending execution. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-001 | refines | SPEC-0016 |
| REQ-002 | depends_on | DEC-002 |
| REQ-002 | refines | SPEC-0016 |
| REQ-003 | depends_on | DEC-006 |
| REQ-003 | refines | SPEC-0016 |
| REQ-004 | depends_on | DEC-004 |
| REQ-004 | refines | SPEC-0016 |
| REQ-005 | depends_on | DEC-005 |
| REQ-005 | refines | SPEC-0016 |
| REQ-006 | depends_on | DEC-007 |
| REQ-006 | refines | SPEC-0016 |
| DEC-006 | supersedes | DEC-003 |

## Out of Scope

- Guessing AI authorship from code-style heuristics.
- Treating SPEC presence alone as formatting authorization.
- Formatting documentation, configuration, generated files, vendored dependencies, or build artifacts as part of the full-program operation.
- Replacing a discoverable repository CLI formatter with the governed fallback.
- Automatically stashing, committing, reverting, or overwriting pre-existing target-file changes.
- Requiring an IDE installation, extension, interactive IDE operation, or new formatter-specific semantic checker.
- Downloading or installing formatter tooling without native authorization.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS.
- Spec governance: decision-complete; reconfirmation required.
- TDD and code review: required after confirmation and fresh execution authorization.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-26 | Started AI-authorship full-format policy clarification. |
| 2 | 2026-08-26 | Defined SPEC presence as a confirmation trigger rather than authorization. |
| 3 | 2026-08-26 | Defined full-program scope as product source plus tests with explicit exclusions. |
| 4 | 2026-08-26 | Reused SPEC-0016 formatter precedence and removed the redundant formatter-choice question. |
| 5 | 2026-08-26 | Required clean targeted program files before an authorized full-format write. |
| 6 | 2026-08-27 | Selected deterministic CLI formatter write and check without IDE or formatter-specific semantic-check dependencies. |
| 7 | 2026-08-27 | Reopened before clarification: Add governed CLI fallback and authorized formatter installation when an existing project has no formatter CLI. |
| 8 | 2026-08-27 | Added governed CLI fallback and native-authorized installation for missing formatter tooling. |
