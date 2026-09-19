# SPEC-0029 implementation and validation report

Canonical revision 17 remains confirmed; overall acceptance is BLOCKED. Source and tests are implemented locally. No commit, publication, installed plugin replacement, or hook trust change was performed.

## Changes
Engineering discussion ownership starts at entry. The existing working Markdown/journal retains sourced discussions and candidate decisions. Host hooks establish turn obligations, guard configured tool paths, and check the prepared reply against actual Stop text. One repair budget survives continuation/restart; exhausted turns cannot be exempted or reuse old replies. Windows launcher preserves Chinese text and checks its Python runtime. Skills, docs, routing contracts and architecture are synchronized.

## Verified host results
562 Python tests passed; 2 POSIX-only tests skipped on Windows. The 292 plugin tests include 21 new discussion-entry cases. Windows installer and ACL contracts passed. Release architecture/layout, formatting, distribution/integration checks and isolated 0.17.0 release rehearsal passed. The installable source candidate remains 0.16.0 with a pending minor changeset; the rehearsal did not publish a release.

Standards review: both reported issues fixed (Windows encoding and unbounded nested candidate fields); bounded re-review found no remaining findings.
Spec review: both reported issues fixed (exhausted repair reusing old reply and old turn completing current turn); bounded re-review found no remaining findings.

## Acceptance limits
AC-003/005/007/008 have recorded host module-contract and SIL evidence: mixed/short/read-only discussions, lifecycle recovery, pure-discussion completion and candidate non-adoption tests. Remaining ACs retain BLOCKED rows conservatively; passing synthetic tests do not establish real desktop behavior.
AC-001/002/004/006/009/010/011 still need original-case and independent real desktop traces, including omission, one repair, persistent failure, actual tool coverage and capability gaps. AC-012 currently has original-turn budget invariant tests, but actual combined SPEC-0030 implementation/revalidation has not been exercised in this change.

Hook capability: host support was inspected separately; this exact candidate's trust, loading and actual desktop firing are NOT established. No host-wide interception is claimed. Current config covers Bash/apply_patch/Edit/Write; other tools, streamed text and interrupts are not fully covered. The task cwd must match the router project root. Windows needs Python 3.11+ through GOVERNED_ENGINEERING_PYTHON or its provisioned project venv.

## Desktop continuation
Use an isolated candidate task whose cwd is the repository root, arrange the documented runtime, and review the exact bundled hooks through the host trust UI. Then capture actual prompt/resume/pre-tool/Stop traces for the acceptance cases; never auto-trust the candidate. Keep SPEC confirmed until required evidence and managed completion pass. No repeat implementation authorization is needed for the already approved scope.

## Test-environment corrections
Earlier failed immutable runs are retained. Their causes were fixed or isolated: three owner bugs reproduced by failing tests, Windows process-global pipeline encoding, old contract fixtures, Git index environment leakage into child fixture repositories, Python 2.7 on PATH, incompatible PowerShell module search path, and release temporary directories accidentally inheriting the parent Git repository. Final successful runs below supersede those results for their stated scope.

## Recorded runs
- spec0029-architecture-unit: PASS; original run artifacts/tests/da7a0800c45d445a970f7806e9d044da/manifest.json
- spec0029-governance-contracts: PASS; original run artifacts/tests/516cafc8bb8142e698bec0f9921e4b60/manifest.json
- spec0029-verification-contracts: PASS; original run artifacts/tests/e4d8d663c0dc420e87184a55db9de132/manifest.json
- spec0029-ladder-contracts: PASS; original run artifacts/tests/75926bf80fef4d48840d8035aa58d62a/manifest.json
- spec0029-device-contracts: PASS; original run artifacts/tests/12cc724f3bbe4ba19e490922f59f4326/manifest.json
- spec0029-isolated-plugin-contracts: PASS; original run artifacts/tests/402b8ba379b44e21a29962fe31d25e70/manifest.json
- spec0029-final-distribution-contracts: PASS; original run artifacts/tests/8c66a81e05ec46b7b5edc1fcb40450c4/manifest.json
- spec0029-isolated-windows-install: PASS; original run artifacts/tests/4687c6064ac34579a7448193f98cc8ba/manifest.json
- spec0029-isolated-windows-artifact: PASS; original run artifacts/tests/d13634f7b0b34b6fab45712d70155c38/manifest.json
- spec0029-final-rehearsal: PASS; original run artifacts/tests/fdfac3e08a854557906f2e7d663c1132/manifest.json
- spec0029-final-architecture: PASS; original run artifacts/tests/072e9974fda64d84a9951ffe03d1dfe4/manifest.json
- spec0029-isolated-integration: PASS; original run artifacts/tests/180154c946374087a468d6c59ac09ed6/manifest.json
- spec0029-isolated-distribution: PASS; original run artifacts/tests/8c73a38db4bc46598205ac060138caed/manifest.json
