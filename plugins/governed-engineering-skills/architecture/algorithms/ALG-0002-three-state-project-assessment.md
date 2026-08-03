# ALG-0002: Three-state ProjectState assessment

## Metadata

- Status: proposed
- Owner module: `workflow_routing_domain`
- Product feature: Evidence-backed greenfield and codebase classification
- Flow IDs: `governed-engineering-route`
- Related ADRs: `ADR-0010`
- Source paths:
  - `skills/engineering-risk-routing/scripts/project_state.py`
  - `skills/engineering-risk-routing/scripts/repository_evidence.py`
- Test and benchmark paths: `tests/test_guided_routing.py`
- Supersedes: none

## Problem and observable success

Determine independently whether implementation and durable stateful context exist.
Success means an empty repository is `absent / absent`, non-empty formal documents
affect only context, empty formal documents remain ambiguous, source affects
implementation, and weak scaffold evidence never becomes a silent yes or no.

## Inputs, outputs, and assumptions

Input is a bounded list of normalized tracked and non-ignored untracked artifacts:
project-relative path, tracking state, byte size, and nullable exclusion reason. Output is one
`ProjectStateAssessment` with `present | absent | indeterminate` on each axis and the
classified evidence. Filesystem discovery excludes Git metadata, ignored
dependencies, caches, build output, generated artifacts, and symbolic links. It
records safely enumerable exclusions without reading a symbolic-link target.

## Exact behavior and tie-breaking

1. Recognized non-empty source or test suffixes set implementation to `present`.
2. Non-empty formal context paths set stateful context to `present`.
3. Empty formal context paths add context ambiguity; empty source placeholders add
   implementation ambiguity.
4. Generic scaffolds make both axes indeterminate only when no strong source or
   formal-context evidence exists.
5. Strong evidence on an axis outranks ambiguity on that axis, and strong evidence
   on either axis prevents unrelated weak artifacts from making the other axis
   indeterminate.
6. Excluded evidence never changes either axis.

## Complexity, errors, and forbidden behavior

Classification is `O(n)` artifacts and read-only. Git query failure, unreadable roots,
or malformed evidence are validation errors. It is forbidden to mutate Git, consult
ignored artifacts, follow symbolic links, or treat a README/template alone as a
codebase.

## Validation

`tests/test_guided_routing.py` covers empty, README-only, doc-only, source-only,
ignored artifacts, empty placeholders, and untracked source. All cases must pass.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
