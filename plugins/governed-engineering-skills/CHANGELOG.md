# Governed Engineering Skills

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
