# Governed Engineering Skills

## 0.5.0-beta.1

### Added

- Add repository-canonical change-set specifications and deterministic cross-task resolution.
- Add requirement-to-acceptance traceability and verified implementation evidence.

### Changed

- Require spec reconciliation, authorization, materialization, and verification before modifying workflows.
- Route confirmed specifications across tasks without repeating resolved grilling.

## 0.4.0-beta.1

### Added

- Add GuidedRouteDecision, ProjectStateAssessment, IntentAssessment, and repository-evidence contracts.

### Changed

- Make ask-matt the automatic entry for every software-engineering request.
- Add evidence-backed dual-axis ProjectState and ordered intent routing.
- Require one grilling interview before every repository-modifying change set.

## 0.3.0-beta.3

### Fixed

- Make release base-branch preparation idempotent and restrict automated Version PR updates to pull requests that are still open.

## 0.3.0-beta.2

### Fixed

- Allow the official Linux libclang archive to contain safe internal links without creating filesystem links or weakening traversal protection.
- Allow cumulative changesets in one prerelease group to retain their original SemVer bumps while validating the latest promotion independently.

## 0.3.0-beta.1

### Added

- Add a lock-pinned official Espressif Xtensa libclang provider with explicit install/verify commands and offline AST gate enforcement.

### Changed

- Require an explicit release intent to start a new major or minor prerelease group from an existing prerelease.
- Use clang 20.1.5 Python bindings and official esp-clang-libs 20.1.1_20250829 artifacts on Windows x64 and Linux amd64.

### Fixed

- Reject path-traversal and link entries when extracting libclang provider archives.

## 0.2.0-beta.2

### Fixed

- Require deterministic reading-level routing and complete Level 1 Flow guidance for code-understanding requests.

## 0.2.0-beta.1

### Breaking Changes

- Replaced the legacy public architecture commands with the single `architecture_cli.py` governance entrypoint.
- Upgraded the unpublished architecture contract to Schema 2.1.0 and rejected legacy RTOS-specific scheduling fields.

### Added

- Added workload-driven hard/soft real-time scheduling studies with RMA/RTA analysis and generated Markdown reports.
- Added Python AST coverage, composition-root validation, adoption readiness reports, release-zero baseline enforcement, and host/target assurance separation.
- Added an isolated SemVer lifecycle with alpha, beta, RC, stable, changelog, fingerprint, approval, and evidence gates.

### Changed

- Known legacy governance debt is remediated by default; only explicit non-AI temporary deferrals are allowed during development.
- Plugin release metadata now distinguishes compatibility version numbers from prerelease maturity and local Codex cachebusters.

### Fixed

- An empty legacy baseline no longer implies that architecture adoption, catalogs, composition, or analyzer evidence is complete.

## 0.1.0

### Added

- Initial local integration of engineering workflow, architecture governance, code-flow guidance, and runtime-evidence skills.
