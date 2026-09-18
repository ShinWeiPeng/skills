# ALG-0008: Layout classification and immutable runs

- Status: proposed
- Owner module: governance_workflow_domain (layout), verification_ladder_domain (run contract)
- Specification: SPEC-0028
- Approval: pending; no AI approval asserted.

## Inputs and observable success

Version 1 layout policy, architecture owner IDs, complete filesystem inventory,
language dependency evidence, explicit run references. Stable diagnostics include
rule, path, expected location and reason. All known invalid examples must not PASS.

## Selected algorithms

Enumerate project files in sorted order without consulting Git; validate safe paths,
match exactly one explicit role, validate owner and fixed root, then dependency edges
and run references. Only provenance-declared third-party/build trees may be pruned.
Unknown/ambiguous evidence is BLOCKED; proven violations FAIL; both block completion.
Sort diagnostics by path/rule/reason. Cost O(files * declarations + edges + bytes hashed).

Allocate artifacts/<kind>/<unique-id> with exclusive mkdir. Stage data inside the run,
compute hashes, publish terminal manifest atomically under an exclusive finalization
lock. Duplicate allocation and second finalization fail. Crash leaves no valid terminal
manifest. Validation rechecks identity, metadata, containment, file set and hashes.
Cost is linear in files and hashed bytes; no performance winner is claimed.

## Rejected alternatives and fault cases

Suffix-only classification confuses intentional fixtures with generated reports.
Changed-files-only scanning misses existing evidence in specs/. Fixed output overwrites
destroy reference identity. A database adds unnecessary external state.

AC-001/003/005: private helper cross-use, support back-edge, production test import,
unknown owner, ignored misplaced output, missing analyzer, unresolved dynamic import.
AC-002: parallel same/different IDs, interrupted write/finalize, corrupt or extra file,
traversal, symlink/junction, invalid metadata, terminal FAIL/BLOCKED retained.
AC-004/006/007: migration byte hashes, explicit acceptance refs and assembled consumers.
