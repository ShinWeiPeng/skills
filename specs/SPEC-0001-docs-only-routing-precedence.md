---
spec_version: 1
spec_id: SPEC-0001
revision: 4
status: implemented
change_set: docs-only-routing-precedence
---

# Docs-only routing precedence

## Problem

The workflow router treats a uniquely resolved confirmed specification as proof that
every modifying request resumes that specification. In a repository with durable
specification context but no implementation, this check runs before the
`grill-with-docs` ProjectState rule. A new or specification-changing request can
therefore skip the required interview and incorrectly enter `spec-governance`.

## Solution

Separate confirmed-spec discovery from confirmed-spec resume intent. A confirmed
specification continues to prove durable context, but only explicit
`resume_confirmed_spec` evidence permits the router to verify and resume it without a
new interview. The option defaults to `false`, is exposed through the Python and CLI
interfaces, and fails closed when it does not identify one valid confirmed spec.

## User Stories

- As a Codex user starting new work in a docs-only repository, I receive the
  `grill-with-docs` workflow even when the repository has one confirmed spec.
- As a Codex user explicitly continuing a confirmed change set, I can verify and
  resume it without repeating settled interview decisions.
- As a plugin maintainer, I can audit and regression-test the distinction between
  durable context and resume evidence.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | A modifying route with `resume_confirmed_spec=false` MUST apply ProjectState interview precedence even when one confirmed spec is resolved; implementation-absent and stateful-context-present repositories MUST select `grill-with-docs`. |
| REQ-002 | A modifying route with `resume_confirmed_spec=true` MUST select `spec-governance` only when exactly one valid confirmed spec is resolved, and MUST return `BLOCKED` for none, ambiguous, invalid, or implemented spec context. |
| REQ-003 | The Python routing interfaces and `guided_workflow_router.py` CLI MUST accept an optional `resume_confirmed_spec` input whose default is `false`, and the public routing contract MUST document the input. |
| REQ-004 | `ask-matt`, ordered workflow algorithm documentation, the architecture manifest, and generated Description Views MUST state that confirmed-spec discovery is durable context rather than resume evidence. |
| REQ-005 | The change MUST preserve empty-repository, implementation-present, read-only, diagnosis, wayfinder, risk-gate, and execution-redecision behavior outside the new resume distinction. |
| REQ-006 | The plugin MUST apply its release changeset as `0.5.0-beta.2` on a local feature branch, without publishing a tag, pull request, or remote release; the original marketplace path and launcher MUST install that branch version, and tracked source MUST contain no cachebuster. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use one explicit boolean named `resume_confirmed_spec`; default it to `false` at every public call boundary. |
| DEC-002 | Treat the boolean as caller-supplied evidence that the request continues the selected confirmed spec without new decisions or conflicts; discovering a unique confirmed spec alone is insufficient. |
| DEC-003 | Fail closed through `spec-governance` when resume evidence is incompatible with the resolved spec context. |
| DEC-004 | Keep execution-time discretionary-decision handling unchanged: it returns to general `grilling`. |
| DEC-005 | Update the existing `workflow_routing_domain` and `guided_workflow_router` ownership rather than adding a module, port, event, state object, or dependency edge. |
| DEC-006 | Screen algorithm impact as applicable to the existing deterministic workflow-selection algorithm `ALG-0003`; update that record, but do not create a new algorithm or ADR. |
| DEC-007 | Keep the work in the original repository on `fix/docs-only-routing-precedence`, apply the existing release intent there, and install through the original marketplace and launcher rather than a separate staging copy. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-005 | Empty repositories select `grill-me`; docs-only repositories select `grill-with-docs`; docs-only repositories with one confirmed spec and no resume evidence also select `grill-with-docs`. | Focused routing unit tests in `tests/test_guided_routing.py`. | PASS — focused fixtures and the complete 116-test suite cover all three states. |
| AC-002 | REQ-002, REQ-005 | A valid confirmed spec plus explicit resume evidence selects `spec-governance`, while resume evidence with none, ambiguous, invalid, or implemented context returns `BLOCKED`; implementation-present and execution-redecision fixtures remain unchanged. | Focused routing and CLI tests in `tests/test_guided_routing.py`. | PASS — routing and CLI regression fixtures cover valid resume, every fail-closed context, implementation-present, and execution redecision. |
| AC-003 | REQ-003 | Function signatures, CLI help, CLI behavior, and JSON Schema expose the optional input with a default of `false`. | Contract assertions plus CLI subprocess tests. | PASS — Python, CLI, schema, and documentation contract assertions pass with an optional default-false input. |
| AC-004 | REQ-004 | The source documents and manifest consistently describe precedence, and generated architecture pages exactly match the manifest. | Text assertions, architecture render check, and architecture development gate. | PASS — source assertions, rendered Description Views, design gate, and development gate pass. |
| AC-005 | REQ-001, REQ-005 | The `thesis-trace` fixture reports `implementation=absent`, `stateful_context=present`, and `selected_skill=grill-with-docs` for a new Proxmox/VM deployment decision. | Reproducible router invocation against `C:\Users\hugo_peng\skill\thesis-trace`, followed by a fresh Codex task after local reload. | PASS — direct invocation and fresh task `019fc73b-d5fe-7f22-b10a-987065a4c2a4` report absent/present/confirmed, no explicit resume evidence, and `grill-with-docs`. |
| AC-006 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 | Focused routing tests, the complete plugin test suite, integration validation, version governance, and the architecture development gate all exit 0. | Recorded commands, exit codes, and minimal raw output in the task handoff. | PASS — 116 unit tests, installer harness, 28-skill integration and vendor checks, version governance, architecture gates, and both code-review axes pass. |
| AC-007 | REQ-006 | Branch `fix/docs-only-routing-precedence` contains consistent `0.5.0-beta.2` package, plugin, changelog, and release-state metadata; the original launcher installs beta.2 from the original marketplace path; tracked source has no cachebuster; no tag, push, pull request, or remote release is created. | Branch and version-governance checks, Git inspection, original-launcher receipt, and fresh-task active-skill inventory. | PASS — branch and version checks pass; the original launcher installed `personal/governed-engineering-skills/0.5.0-beta.2`; fresh task `019fca3a-4c95-7e30-88b0-e3cb65709a56` loaded that root and returned `grill-with-docs`; no cachebuster, tag, push, PR, or remote release was created. |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |
| REQ-002 | depends_on | DEC-002 |
| REQ-002 | depends_on | DEC-003 |
| REQ-004 | depends_on | DEC-005 |
| REQ-004 | depends_on | DEC-006 |
| REQ-005 | depends_on | DEC-004 |
| REQ-006 | depends_on | DEC-007 |

## Out of Scope

- Sending a correction or follow-up to the original Proxmox tutorial task.
- Modifying the `thesis-trace` repository.
- Publishing a formal beta, RC, stable release, tag, or pull request.
- Changing canonical-spec resolution order or automatically inferring semantic
  continuity from prompt text.
- Adding modules, ports, events, runtime state, execution profiles, or real-time
  scheduling behavior.

## Open Decisions

None.

## Routing/Gates

- Grilling: PASS — prior task completed the decision tree and confirmed the complete
  implementation plan.
- Spec verification: PASS — revision 4 records implemented branch, install, and
  fresh-task evidence with no open conflicts.
- Clarify improvement proposal: PASS — the confirmed plan defines behavior,
  compatibility, risks, validation, local reload, and failure handling.
- Architecture authoring gate: PASS — manifest, algorithm record, and rendered views
  pass design and development validation.
- TDD: PASS — focused routing tests were added before the implementation was
  completed, and the full suite now passes.
- Code review Standards axis: PASS — no documented-standard violations; one
  non-blocking duplicated test-fixture smell remains a judgment call.
- Code review Spec axis: PASS — no uncovered requirements, unverified acceptance
  criteria, incorrect behavior, or scope creep.
- Spec review: PASS — revision 4 evidence is complete and traceable to REQ-001
  through REQ-006.

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-03 | Materialized the authorized, decision-complete routing precedence contract. |
| 2 | 2026-08-03 | Recorded implemented status and passing validation, review, reload, and fresh-task evidence. |
| 3 | 2026-08-04 | Replaced the staging-cache install approach with the authorized original-repository feature branch and formal beta.2 metadata workflow. |
| 4 | 2026-08-04 | Recorded the original-launcher beta.2 install and fresh-task active inventory and routing evidence. |
