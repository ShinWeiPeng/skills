---
spec_version: 1
spec_id: SPEC-0016
revision: 6
status: implemented
change_set: formatter-governance
---

# Formatter governance

## Problem

The governed engineering skills defer to repository conventions but do not define
how to discover, select, run, or verify language formatters when a repository has no
explicit formatter policy. This leaves formatting behavior inconsistent across
greenfield projects while a universal override could disrupt established projects.

## Solution

Add a promoted, model-invoked `formatter-governance` skill that centrally owns
ProjectState-aware formatter discovery, greenfield defaults, repository-style
preservation, check/write command selection, and formatter evidence reporting. Map
it as an L2 component under the existing `delivery_workflow_domain`; its L1 parent
coordinates use by routing, TDD, implementation, and code review without direct
sibling dependencies or duplicated formatter mappings.

A greenfield project uses this complete mainstream mapping:

| Language or file family | Greenfield default |
|---|---|
| Python | Ruff formatter |
| JavaScript, TypeScript, JSON, CSS, Markdown, YAML | Prettier |
| C and C++ | clang-format |
| Go | gofmt |
| Rust | rustfmt through `cargo fmt` |
| C# | dotnet format |
| Java | google-java-format |

A non-greenfield project preserves and uses its repository's established formatting
style and tooling. An indeterminate ProjectState fails closed until the existing
router resolves whether repository conventions exist.

For a greenfield target, the workflow may first create only a minimal scaffold in
the explicitly selected project root: package/build metadata, directory skeleton,
formatter dependency declarations and configuration, and generator-required
boilerplate without product behavior. It must preflight the exact target paths and
must not overwrite, merge through, or force replacement of any existing file or
directory. After the minimal scaffold exists and before product code is authored,
the applicable formatter must be available and its non-mutating check must pass;
otherwise the workflow is `BLOCKED`. Installing or downloading a missing formatter
always requires explicit authorization.

## User Stories

- As a developer starting a greenfield project, I want governed engineering work to
  select a predictable formatter without requiring pre-existing configuration.
- As a maintainer of an existing project, I want its established formatting style
  and tooling preserved.
- As a governed workflow maintainer, I want one formatter-policy owner rather than
  duplicated rules in routing, implementation, tests, and review.
- As a repository owner, I want scaffold initialization to preserve every existing
  file and stop when the target directory is not safely empty.
- As a reviewer, I want a non-mutating formatter check that can produce evidence.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | When ProjectState is `absent / absent`, the governed engineering workflow MUST select Ruff for Python; Prettier for JavaScript, TypeScript, JSON, CSS, Markdown, and YAML; clang-format for C/C++; gofmt for Go; rustfmt through `cargo fmt` for Rust; dotnet format for C#; and google-java-format for Java. |
| REQ-002 | When ProjectState is not greenfield and repository conventions are discoverable, the workflow MUST preserve and use the repository's existing formatting style and tooling instead of replacing them with governed defaults. |
| REQ-003 | When ProjectState is indeterminate, formatter selection MUST fail closed until the existing ProjectState ambiguity is resolved. |
| REQ-004 | The policy MUST distinguish a non-mutating format check from an authorized formatting write. |
| REQ-005 | Authoritative skill instructions, tests, promoted documentation, router mapping, Plugin manifests, and required release metadata MUST remain consistent. |
| REQ-006 | A promoted model-invoked `formatter-governance` skill MUST be the single authoritative owner of formatter discovery, selection, command policy, and evidence reporting. |
| REQ-007 | The existing delivery workflow parent MUST coordinate formatter governance for routing, TDD, implementation, and code review without direct sibling dependencies or duplicated mapping tables. |
| REQ-008 | Before the formatter is available, a greenfield workflow MAY create only the minimal scaffold required to configure the project and formatter, and MUST NOT add product behavior. |
| REQ-009 | Before scaffolding, the workflow MUST resolve and inspect the exact target root and paths; it MUST NOT overwrite existing files, use a force-overwrite option, or create an unintended nested duplicate project. |
| REQ-010 | After minimal scaffolding and before authoring product code, the applicable formatter MUST be available and its non-mutating check MUST pass; otherwise the workflow is `BLOCKED`. |
| REQ-011 | Formatter installation or download MUST NOT occur without explicit authorization through the applicable native permission boundary. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use ProjectState-aware precedence: greenfield (`absent / absent`) projects use Governed Engineering Skill formatter defaults; non-greenfield projects preserve repository formatting style and tooling; indeterminate projects do not guess. |
| DEC-002 | Adopt the complete mainstream greenfield mapping: Ruff; Prettier; clang-format; gofmt; rustfmt via `cargo fmt`; dotnet format; and google-java-format for their specified languages and file families. |
| DEC-003 | Create a separate promoted, model-invoked `formatter-governance` skill as the single formatter-policy owner and integrate it through the governed delivery workflow. |
| DEC-004 | Architect `formatter-governance` as an L2 component under `delivery_workflow_domain`; the L1 parent coordinates routing, TDD, implementation, and review consumers. |
| DEC-005 | Allow only a non-destructive minimal scaffold before formatter availability; require formatter check PASS before product code, and otherwise return `BLOCKED`. |

## Discussion Context

### DISC-001: Formatter precedence by project maturity

- **Situation:** A universal formatter default would make greenfield projects consistent but could conflict with an established repository's style and CI configuration.
- **Question:** Should formatter defaults apply universally, only as a fallback, or only to greenfield projects?
- **Options and tradeoffs:** Repository-first fallback preserves local compatibility; central enforcement maximizes uniformity but risks disruptive diffs; greenfield-only defaults supply a convention where none exists while leaving established projects unchanged.
- **User answer:** `綠地的專案使用Governed Engineering Skill   內的formatter，非綠地則沿用專案風格`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-001, REQ-002, REQ-003, DEC-001, AC-001.

### DISC-002: Greenfield language mapping scope

- **Situation:** Greenfield defaults could cover only Python, Python plus web files, or the complete mainstream language set.
- **Question:** Which language-to-formatter mapping should the initial governed policy provide?
- **Options and tradeoffs:** Python-only is cheapest but narrow; Python plus web covers common projects at moderate cost; the complete mapping covers mainstream projects consistently but creates the largest documentation and validation matrix.
- **User answer:** `1`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-001, DEC-002, AC-001.

### DISC-003: Formatter workflow ownership

- **Situation:** Formatter policy can be duplicated across existing workflows, placed in the router, or owned by a separate skill.
- **Question:** Which governed workflow should own formatter discovery and verification?
- **Options and tradeoffs:** A separate skill creates one reusable and testable source of truth but adds a promoted module and integration work; router ownership bloats entry routing; per-workflow ownership duplicates rules and can drift.
- **User answer:** `1`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-005, REQ-006, REQ-007, DEC-003, DEC-004, AC-003, AC-004.

### DISC-004: Missing formatter and scaffold boundary

- **Situation:** Blocking before any files exist can prevent creation of the package/build metadata needed to configure the formatter, while waiting until completion permits product code to accumulate without formatter evidence.
- **Question:** At what point should a missing applicable formatter block a greenfield workflow?
- **Options and tradeoffs:** Immediate blocking is strongest but can deadlock initialization; completion-only blocking preserves progress but discovers formatting issues late; allowing only minimal scaffold and then blocking enables formatter setup without permitting unformatted product work.
- **User answer:** `採用此方案。`
- **Explicit rationale:** Not stated.
- **Resulting impact:** REQ-004, REQ-008, REQ-009, REQ-010, REQ-011, DEC-005, AC-002, AC-005.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-002, REQ-003 | Greenfield examples select every formatter in the complete mapping; non-greenfield examples select repository conventions; indeterminate examples fail closed. | Focused contract tests and manual instruction review. | PASS: formatter selection contract tests cover the complete mapping, aliases, existing conventions, and indeterminate fail-closed behavior. |
| AC-002 | REQ-004, REQ-008, REQ-010, REQ-011 | Minimal scaffold creation is allowed before formatter availability, but product code is rejected until an authorized formatter is available and a non-mutating check passes. | Focused positive and negative contract tests covering scaffold, permission, check, and product-code boundaries. | PASS: mutation-gate tests cover structured prerequisites, greenfield-only scaffold, permission denial, unavailable tooling, failed check, and product-code PASS. |
| AC-003 | REQ-005 | Skill source, docs, router, Plugin manifests, tests, architecture views, and release metadata validate together. | Repository validation, architecture gate, distribution validation, and two-axis code review. | PASS: 179 tests, release architecture gate, deterministic render, distribution assembly/validation, version governance, Skill validation, and both review axes passed. |
| AC-004 | REQ-006, REQ-007 | One promoted formatter skill owns the mapping and delivery workflows consume its contract without duplicated language tables or illegal sibling dependencies. | Source inventory, focused integration tests, and architecture dependency validation. | PASS: inventory tests and release architecture gate verify one L2 owner, parent coordination, formal Ports/Event, and no copied workflow mappings. |
| AC-005 | REQ-009 | Existing target files, a non-empty incompatible directory, or a nested-project collision are detected before mutation and remain byte-for-byte unchanged while the workflow reports `BLOCKED` or follows discovered non-greenfield conventions. | Temporary-directory integration tests with before/after hashes and structured verdict assertions. | PASS: temporary-directory tests verify file, directory, nested-root, incompatible-root, and allowed-ancestor collisions with preserved hashes and no writes. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-001 | depends_on | DEC-002 |
| REQ-002 | depends_on | DEC-001 |
| REQ-003 | depends_on | DEC-001 |
| REQ-004 | depends_on | DEC-005 |
| REQ-005 | depends_on | DEC-003 |
| REQ-006 | depends_on | DEC-003 |
| REQ-007 | depends_on | DEC-004 |
| REQ-008 | depends_on | DEC-005 |
| REQ-009 | depends_on | DEC-005 |
| REQ-010 | depends_on | DEC-005 |
| REQ-011 | depends_on | DEC-005 |
| AC-001 | depends_on | DEC-001 |
| AC-001 | depends_on | DEC-002 |
| AC-002 | depends_on | DEC-005 |
| AC-004 | depends_on | DEC-003 |
| AC-004 | depends_on | DEC-004 |
| AC-005 | depends_on | DEC-005 |

## Out of Scope

- Replacing a non-greenfield repository's established formatter or style.
- Installing formatter dependencies into user projects without explicit authorization.
- Reformatting an existing repository as part of defining this skill policy.
- Adding runtime events, callbacks, queues, threads, device behavior, or performance claims.
- Publishing or releasing the plugin during this change set.

## Open Decisions

None.

## Routing/Gates

- Engineering risk routing: R2 governed change because a promoted module and workflow dependency are added.
- Grilling: PASS — project precedence, complete language mapping, workflow ownership, and missing-tool/scaffold behavior are confirmed.
- Clarify Improvement Proposals: Required before implementation.
- Govern Modular Event Architecture: Required; manifest, dependency, parent mapping, description views, and design gate must pass before product edits.
- Algorithm screening: Not applicable; formatter selection is a fixed language mapping and does not introduce a data-dependent product algorithm.
- Execution efficiency and runtime validation: Not applicable; no runtime execution unit, device behavior, timing, or performance claim changes.
- Skill Creator: Required for the new promoted skill.
- TDD: Required during implementation.
- Code review Standards/Spec axes: Required after implementation.
- Spec review: PASS — no uncovered requirements, unverified acceptance criteria, or scope creep.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-26 | Started formatter-governance decision work. |
| 2 | 2026-08-26 | Confirmed greenfield defaults and non-greenfield repository-style precedence. |
| 3 | 2026-08-26 | Confirmed the complete mainstream greenfield formatter mapping. |
| 4 | 2026-08-26 | Confirmed an independent formatter-governance skill and its delivery workflow ownership. |
| 5 | 2026-08-26 | Confirmed minimal-scaffold allowance, pre-product formatter gate, authorization boundary, and no-overwrite safety. |
| 6 | 2026-08-26 | Implemented formatter governance and recorded complete PASS evidence plus Standards and Spec review results. |
