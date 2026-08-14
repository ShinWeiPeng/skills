---
spec_version: 1
spec_id: SPEC-0014
revision: 16
status: confirmed
change_set: cross-platform-marketplace-install
---

# Cross-platform Marketplace installation

## Problem

Windows and Linux users need one automated path that bootstraps verified prerequisites, authenticates Codex, configures the Marketplace, and installs the Plugin without manual configuration edits.

## Solution

Provide PowerShell and POSIX-shell installers governed by shared contracts. Supported providers install prerequisites using native elevation, a verified manifest controls Codex compatibility, interactive runs launch device authentication when needed, and the installer configures `governed-engineering`, installs in place, and verifies identity.

## User Stories

- Supported users can bootstrap prerequisites, authenticate, and install or update the Plugin from one launcher.
- Interactive users receive native elevation and official device-auth flows.
- Automation never hangs on prompts or exposes credentials.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | The installation flow MUST support Windows and Linux through the generated Git Marketplace. |
| REQ-002 | The user MUST NOT need to edit Codex configuration files manually. |
| REQ-003 | The flow MUST install the `governed-engineering-skills` Plugin and provide a verifiable result. |
| REQ-004 | Windows MUST provide a double-clickable native launcher and Linux MUST provide a shell launcher, with both delegating to shared installation behavior. |
| REQ-005 | Repeated runs MUST add missing state, update the Marketplace, and reinstall only when source or version differs. |
| REQ-006 | Before Marketplace mutation, the installer MUST validate the platform and tools, install missing supported prerequisites, fail with remediation, and preserve existing Plugin state. |
| REQ-007 | PowerShell and POSIX-shell implementations MUST conform to shared state-transition contracts and fixtures without another installer runtime. |
| REQ-008 | The Marketplace MUST be `governed-engineering`; legacy `personal` MAY migrate only after exact source matching, and conflicts MUST stop. |
| REQ-009 | Repair MUST invoke `plugin add` without first removing an installed Plugin; unsuccessful replacement MUST retain the prior installation. |
| REQ-010 | Prerequisite installation MUST support Windows `winget`, Ubuntu/Debian `apt`, and Fedora/RHEL `dnf`; unsupported systems or missing selected providers MUST stop before mutation. |
| REQ-011 | A tracked provider manifest MUST declare verified Codex source, package identity, integrity, and minimum compatible version; missing or old Codex installs the manifest version and compatible newer versions are retained. |
| REQ-012 | Interactive execution MUST initiate native UAC or `sudo` only when required; `--non-interactive` MUST proceed only with sufficient privilege and non-interactive providers, otherwise stopping before mutation. |
| REQ-013 | The installer MUST check `codex login status`; an unauthenticated interactive run MUST launch `codex login --device-auth` and continue only after success, while a non-interactive run MUST require existing or caller-provided standard Codex authentication without reading, persisting, or logging credential values. |
| REQ-014 | On Windows PowerShell 5.1, every Codex native command MUST use its process exit code as the success criterion, MUST tolerate stderr output from a successful command, and MUST retain actionable output when the command fails. |
| REQ-015 | A source checkout MUST expose a distinct development Marketplace identity that cannot shadow the generated `governed-engineering` Git Marketplace; publication MUST deterministically rewrite the generated Marketplace to the formal identity and packaged Plugin path. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use the generated Git Marketplace as the shared distribution authority for Windows and Linux. |
| DEC-002 | Provide thin native launchers for Windows and Linux over one shared Marketplace installation core. |
| DEC-003 | Make installation idempotent and convergent, with conditional repair only for mismatches. |
| DEC-004 | Fail closed after comprehensive prerequisite checks and do not install operating-system dependencies. |
| DEC-005 | Implement the shared installation core in Python 3.11 or newer and keep the Windows and Linux launchers as thin adapters. |
| DEC-006 | Supersede the Python core with platform-native PowerShell and POSIX-shell implementations governed by shared behavior contracts and fixtures. |
| DEC-007 | Publish as Marketplace `governed-engineering` and migrate legacy `personal` state only after exact source-identity matching. |
| DEC-008 | Repair in place with `plugin add`, never pre-remove a usable Plugin, and fail safely when Codex cannot perform or verify replacement. |
| DEC-009 | Supersede the no-package-install portion of DEC-004 and automatically install prerequisites only through `winget`, `apt`, or `dnf` on the supported platform matrix. |
| DEC-010 | Install Codex from a tracked verified provider manifest only when missing or below the declared compatibility floor, and retain compatible newer versions without downgrade. |
| DEC-011 | Use native interactive elevation by default and permit non-interactive installation only with pre-existing privilege and fully non-interactive verified provider actions. |
| DEC-012 | Bootstrap authentication by execution mode: interactive device authentication when needed, and pre-existing or caller-provided standard Codex authentication for non-interactive runs without installer secret handling. |
| DEC-013 | Route every Windows Codex invocation through one PowerShell 5.1-compatible native-command wrapper that prevents stderr from becoming a terminating PowerShell error, evaluates `$LASTEXITCODE`, and returns captured output when callers need to parse it. |
| DEC-014 | Name the source-checkout Marketplace `governed-engineering-development`, retain `governed-engineering` only for generated `marketplace-release` publications, and make publication generation explicitly set the formal name and packaged Plugin source. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Installation succeeds on supported Windows and Linux. | Cross-platform integration tests. | Pending |
| AC-002 | REQ-002 | No manual Codex configuration edit is required. | Contract and docs review. | Pending |
| AC-003 | REQ-003 | Codex lists the expected Plugin. | Isolated CLI integration test. | Pending |
| AC-004 | REQ-004 | Each OS exposes its launcher and shared behavior. | Launcher contract tests. | Pending |
| AC-005 | REQ-005 | Install, rerun, update, repair, and interruption are deterministic. | State-machine tests. | Pending |
| AC-006 | REQ-006 | Prerequisites complete before Marketplace mutation and failure preserves Plugin state. | Failure-injection traces. | Pending |
| AC-007 | REQ-007 | Native implementations pass identical fixtures without another runtime. | Cross-platform contract suite. | Pending |
| AC-008 | REQ-008 | Dedicated identity installs and exact legacy state migrates without touching conflicts. | Migration fixtures. | Pending |
| AC-009 | REQ-009 | Repair never issues `plugin remove` and failed replacement preserves installed state. | Fake-Codex trace and fingerprints. | Pending |
| AC-010 | REQ-010 | Providers install only declared packages; unsupported systems make zero mutations. | Provider fixtures and OS matrix. | Pending |
| AC-011 | REQ-011 | Missing and old Codex install the verified version; compatible newer Codex stays; invalid metadata stops. | Version, schema, integrity, and trace tests. | Pending |
| AC-012 | REQ-012 | Interactive fixtures elevate only when required; non-interactive fixtures never prompt and make zero mutation when insufficient. | Elevation/provider traces with bounded timeout. | Pending |
| AC-013 | REQ-013 | Logged-in runs continue; interactive logged-out runs launch device auth once; non-interactive logged-out runs fail before mutation; logs and artifacts contain no credential values. | Fake-Codex auth state matrix, redaction scan, and command traces. | Pending |
| AC-014 | REQ-014 | A fake Codex command that exits zero after writing to stderr succeeds for login, Marketplace, and Plugin operations; a nonzero command still fails with actionable diagnostics. | Windows PowerShell 5.1 integration and fake-Codex regression tests. | Pending |
| AC-015 | REQ-015 | A main-branch checkout is discovered only as `governed-engineering-development`, while a generated publication is discovered as `governed-engineering` with its packaged Plugin present; Windows and Linux installers can add the formal Git Marketplace without a same-name local collision. | Source/publication manifest contract tests plus Windows and Linux installer integration fixtures launched from a source checkout. | Pending |

## Relationships

| Source | Relation | Target |
|---|---|---|
| SPEC-0014 | depends_on | SPEC-0013 |
| DEC-006 | supersedes | DEC-005 |
| DEC-006 | refines | DEC-002 |
| DEC-009 | supersedes | DEC-004 |

## Out of Scope

- ChatGPT web installation.
- Package managers outside `winget`, `apt`, and `dnf`.
- Downgrading compatible newer Codex.
- Destructive forced Plugin repair.
- Installer-managed storage or transmission of Codex credentials.

## Open Decisions

None.

## Discussion Context

### DISC-001: Automation surface
- **Situation:** Linux lacks the Windows launcher.
- **Question:** Which surface initiates installation?
- **Options and tradeoffs:** Native preserves UX; Python adds a prerequisite; Codex-only remains manual.
- **User answer:** 雙平台原生啟動器。
- **Explicit rationale:** The native option was selected.
- **Resulting impact:** DEC-002 governs REQ-004 and AC-004.

### DISC-002: Update behavior
- **Situation:** Installs may be clean, current, or stale.
- **Question:** How should reruns behave?
- **Options and tradeoffs:** Convergence updates; forced reinstall disrupts; install-only cannot update.
- **User answer:** 收斂到最新版。
- **Explicit rationale:** Convergence was selected.
- **Resulting impact:** DEC-003 governs REQ-005 and AC-005.

### DISC-003: Original prerequisite policy
- **Situation:** Missing dependencies can cause partial state.
- **Question:** Stop or install dependencies?
- **Options and tradeoffs:** Fail-closed avoids mutation; automation needs privilege; minimal checks fail late.
- **User answer:** Initially stop without package installation.
- **Explicit rationale:** This was later revised.
- **Resulting impact:** DEC-004 was partially superseded by DEC-009; REQ-006 retains sequencing.

### DISC-004: Initial runtime
- **Situation:** Platforms lack a common runtime.
- **Question:** Which runtime should be shared?
- **Options and tradeoffs:** Native duplicates thin logic; Python adds a prerequisite; binaries add release work.
- **User answer:** Python, later corrected.
- **Explicit rationale:** Python was initially selected.
- **Resulting impact:** DEC-005 was superseded by DEC-006.

### DISC-005: Runtime correction
- **Situation:** The Python choice was corrected.
- **Question:** Python or native implementations?
- **Options and tradeoffs:** Native avoids runtime dependency; Python centralizes; binaries add artifacts.
- **User answer:** Native implementations with shared contracts.
- **Explicit rationale:** The prior answer was corrected.
- **Resulting impact:** DEC-006 governs REQ-007 and AC-007.

### DISC-006: Marketplace identity
- **Situation:** `personal` can collide.
- **Question:** Which identity and migration policy?
- **Options and tradeoffs:** Dedicated naming is readable; owner naming couples ownership; retaining `personal` keeps risk.
- **User answer:** `governed-engineering` with exact-match migration.
- **Explicit rationale:** Dedicated identity was selected.
- **Resulting impact:** DEC-007 governs REQ-008 and AC-008.

### DISC-007: Plugin repair
- **Situation:** Remove-then-add can destroy a usable Plugin.
- **Question:** How should repair behave?
- **Options and tradeoffs:** In-place preserves; rollback is uncertain; removal accepts outage.
- **User answer:** In-place, never pre-remove.
- **Explicit rationale:** Preservation-first was selected.
- **Resulting impact:** DEC-008 governs REQ-009 and AC-009.

### DISC-008: Automatic prerequisites
- **Situation:** The user requires automatic prerequisites.
- **Question:** Which provider matrix?
- **Options and tradeoffs:** Bounded is testable; wider costs more; best-effort is unpredictable.
- **User answer:** `winget`, `apt`, and `dnf`.
- **Explicit rationale:** The bounded matrix was selected.
- **Resulting impact:** DEC-009 changes REQ-006 and governs REQ-010 and AC-010.

### DISC-009: Codex version policy
- **Situation:** Latest can drift and exact pins can downgrade.
- **Question:** How should versions be controlled?
- **Options and tradeoffs:** Verified floor preserves newer versions; latest drifts; exact pinning downgrades.
- **User answer:** Minimum compatible version plus provider manifest.
- **Explicit rationale:** The recommended policy was selected.
- **Resulting impact:** DEC-010 governs REQ-011 and AC-011.

### DISC-010: Elevation behavior
- **Situation:** Packages may require UAC, `sudo`, licenses, or non-interactive flags.
- **Question:** How should privilege and consent work?
- **Options and tradeoffs:** Native prompts plus restricted unattended mode balance UX and safety; accepting everything hides terms; pre-elevation breaks one-click.
- **User answer:** Interactive native elevation plus restricted unattended mode.
- **Explicit rationale:** The recommended policy was selected.
- **Resulting impact:** DEC-011 governs REQ-012 and AC-012.

### DISC-011: Authentication bootstrap
- **Situation:** Codex can be installed but unauthenticated, and unattended runs cannot complete an interactive account challenge.
- **Question:** How should authentication be established?
- **Options and tradeoffs:** Mode-aware device auth completes interactive setup and fails unattended runs safely; always launching auth hangs CI; never handling auth leaves setup incomplete.
- **User answer:** 1（依執行模式自動處理）。
- **Explicit rationale:** The user selected the recommended mode-aware authentication policy.
- **Resulting impact:** DEC-012 adds authentication bootstrap and secret-handling boundaries in REQ-013 and AC-013.

### DISC-012: Windows native-command error handling

- **Situation:** Windows PowerShell 5.1 promotes stderr from `codex.cmd` into a terminating error when `$ErrorActionPreference` is `Stop`, even when Codex exits successfully.
- **Question:** Should the compatibility repair cover only login status or every Codex native command?
- **Options and tradeoffs:** A shared wrapper removes the same failure mode from login, Marketplace, and Plugin operations with broader regression coverage; a login-only exception changes less code but leaves identical failures elsewhere.
- **User answer:** 1 (apply the shared fix to every Codex native command).
- **Explicit rationale:** The user selected the comprehensive compatibility repair.
- **Resulting impact:** DEC-013 governs REQ-014 and AC-014.

### DISC-013: Development and publication Marketplace identities

- **Situation:** Codex discovers a cloned main-branch Marketplace globally as `governed-engineering`, even outside the checkout directory. The source manifest points to ignored `dist/` output, shadows the formal Git Marketplace, cannot be removed as a configured source, and leaves the Plugin unavailable.
- **Question:** How should source checkouts avoid shadowing the generated Git Marketplace?
- **Options and tradeoffs:** Separating development and publication names removes the collision while retaining local discovery; a clone-free bootstrap avoids the common path but leaves the collision; installing from generated local `dist/` abandons the requested remote Marketplace authority.
- **User answer:** 1 (separate development and publication Marketplace names).
- **Explicit rationale:** Preserve `governed-engineering` as the formal remote identity while making source-checkout discovery visibly developmental and non-conflicting.
- **Resulting impact:** DEC-014 governs REQ-015 and AC-015, and refines DEC-001 and DEC-007.

## Routing/Gates

- Route: grilling -> spec-governance -> tdd -> code-review
- Required gates: tdd, code-review

## Revision History

- Revisions 1-9: Established the Marketplace installer.
- Revision 10: Reopened for automatic prerequisites and bounded providers.
- Revision 11: Selected verified Codex provider policy.
- Revision 12: Selected native elevation and restricted unattended execution.
- Revision 13: Selected mode-aware authentication bootstrap.
- Revision 14: Reopened after Windows PowerShell 5.1 treated successful Codex stderr as a terminating error.
- Revision 15: Reopened after a cloned source Marketplace shadowed the generated Git Marketplace and proved that changing only the installer working directory was insufficient.
- Revision 16: Selected distinct development and formal publication Marketplace identities.
