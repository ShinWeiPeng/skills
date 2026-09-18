# Test and validation architecture (layout schema 1)

This contract applies to every governed project independently of its language,
Git tracking or ignore policy. Missing adoption is BLOCKED; migration is explicit.

## Fixed roots and ownership

- `tests/modules/<module-id>/` and `tests/flows/<flow-id>/` contain test source.
- Each target may own private `support/` fixtures, mocks and helpers. Other suites
  cannot import them. Shared support lives in `tests/support/<capability>/`, has one
  owner and never imports cases. Resolve target IDs from the architecture manifest.
- `validation/` contains authored plans, scenarios, acceptance mappings and
  `layout.yaml`. Device runner source is test source, not a validation definition.
- `artifacts/tests/<run-id>/` and `artifacts/validation/<run-id>/` contain generated
  reports, logs, captures, raw evidence and plan snapshots.
- `specs/` contains specifications and allowed history only. Reference a fixed run;
  never put evidence there. `spec-governance/` keeps discussion lifecycle records.
- Canonical generated architecture views keep their documented generator location.
  General development/build tools keep their declared role; they are not all tests.

No alternate test root is permitted, including existing projects. Migrate source,
fixtures, runner paths, references and source sets together. Curated fixture data
must declare provenance; a report-like suffix does not alone determine its role.

## Test contracts

Prefer public module contracts. A module's own tests may use a controlled test-only
hook owned by that module. Never arbitrarily mutate private product state. Flow
tests use participating module contracts. Test controls and wiring must be absent
from release composition, supported by capable analyzer/build/runtime evidence.

Each case owns mutable state, setup, reset and cleanup. Shared fixtures are readonly
by default. External resources declare per-case isolation or serialization and
cleanup. Validate order independence by rerunning/reordering/concurrent execution
where applicable. A static directory check cannot prove runtime isolation.
Development test functions do not require individual production L0-L3 catalogs;
independently shipped test-platform product code retains normal product governance.

## Policy and gates

`validation/layout.yaml` is explicitly pinned to `schema_version: 1`, separate from
architecture schema 2.2.0. `entries` declare include/exclude patterns, semantic role,
owner and intentional fixture/template/generated provenance. Every governed file
has exactly one role. Unknown/ambiguous role or owner blocks. Exclusions require
provenance and architecture source-set agreement; they cannot hide project sources.

The public architecture gate inventories filesystem scope, including unchanged,
ignored and untracked files. Gitignore never suppresses governance. Diagnostics
include rule, file and expected location. The checker never moves/deletes files.
Required missing language/build capabilities and unresolved dynamic dependencies
are BLOCKED. Layout coverage, language dependency coverage and runtime/release
evidence are reported separately; no blanket PASS for unsupported languages.
Python dependency assessment uses AST and source-hash-bound reviewed resolutions
for dynamic loading. C/C++ requires complete AST dependency coverage from its adapter.

## Run lifecycle

Allocate a unique run directory exclusively. Preserve a guided session's identity.
Never overwrite an existing ID. Collect outputs before publishing `manifest.json`
atomically. A terminal PASS, FAIL or BLOCKED run is immutable. A crash without a
valid terminal manifest is incomplete and cannot satisfy acceptance. Reruns use
new IDs. Writers check admission before effects; scanning also catches other writes.

Record schema, run ID/kind, target Module/Flow, scenario, UTC times, tool/version,
command, source revision/dirty digest, input hashes and artifact-relative paths and
hashes. Record SPEC/AC only when applicable. Validate metadata, identity, path
containment, symlinks/junctions, file set and hashes on read. Hashes prove integrity,
not authentic execution. Never guess the newest run or use mutable latest identity.

Authored acceptance mappings stay in validation/. Generated plans and evidence
belong in the selected run as `plan.snapshot.json` and `evidence.json`. Consumers
must resolve explicit fixed run references. Acceptance and release additionally
compare the governed source snapshot, plan/configuration digests, AC coverage and
explicit scenario set. Run-selection documents are validated separately and do not
change the source digest. Excluded directory trees may not hide reclassified owned
sources. Writer admission holds a shared exclusive operation lock through terminal
publication and rechecks terminal state after acquiring the lock. Retention and cleanup belong to each
project; no universal expiry or automatic deletion. Deleted referenced evidence
invalidates acceptance. Gitignore remains separately project-owned.

## Historical migration

Keep original bytes, SHA-256 and original path in a migration inventory under
artifacts/. Missing provenance remains unknown. Never invent historical run IDs,
rebind legacy results as new acceptance or rewrite implemented SPEC contracts.
Provide migration cross-references for historical paths and update active consumers.

Start from [the explicit example](validation-layout.example.yaml), inventory actual files,
and resolve every placeholder against the architecture manifest before adoption.
