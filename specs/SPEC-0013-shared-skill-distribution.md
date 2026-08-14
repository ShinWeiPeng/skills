---
spec_version: 1
spec_id: SPEC-0013
revision: 40
status: confirmed
change_set: shared-skill-distribution
---

# Shared Skill Distribution

## Problem

The repository currently has a Claude plugin over the promoted source buckets and a separate Codex plugin containing 212 tracked files under its vendored and overlaid skill tree. ChatGPT web and local Codex therefore do not share one installation state, and skill content can diverge.

## Solution

Treat root `skills/engineering` and `skills/productivity` as the only editable Skill source. Move the six existing Codex-only governance and integration Skills into engineering. Keep only the Plugin manifest, versioning, release scripts, contract tests, and validation infrastructure under `plugins/governed-engineering-skills`; move formal architecture governance to repository root and remove tracked Plugin Skill copies. Deterministically assemble a complete ignored artifact at `dist/governed-engineering-skills`, copying the tracked shell and generating its `skills/` tree from the two promoted buckets.

After the existing stable-release gates pass, generate an installable Marketplace tree from that exact artifact and publish only the generated catalog and complete Plugin package to the `marketplace-release` branch of `https://github.com/ShinWeiPeng/skills.git`. The `main` branch remains the only editable source, `plugin-release/main` remains the Version Pull Request branch, and `marketplace-release` is a generated consumer branch that must never be edited manually.

The supported user path restores the `0.7.1` local one-click installer: it assembles the Plugin from the authoritative root Skills, installs the resulting local Marketplace for Codex Desktop and Codex CLI, and applies a local-only cachebuster without changing the formal release version. The generated `marketplace-release` branch may remain as an optional Codex distribution source, but it is not required for local installation. ChatGPT web does not expose Git Marketplace installation for this personal account and is not a supported distribution surface.

## User Stories

- As the maintainer, I want to edit each shared skill in one authoritative root location.
- As a contributor, I want Skill PRs to avoid duplicate generated-file diffs.
- As the owner of one personal account, I want Codex Desktop and Codex CLI to consume the same Git-backed Plugin release without claiming unsupported ChatGPT web installation.
- As a Windows user, I want the one-click installer to verify that its Python runtime is compatible before any Plugin assembly begins, so an old PATH entry produces actionable guidance instead of a Python syntax error.
- As a Windows user, I want a user-launched reinstall to recover safely when a prior ignored artifact was created by Codex's sandbox or another account, so cross-account ACLs do not block installation or hide the installed-version view.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Root `skills/engineering` and `skills/productivity` MUST be the authoritative editable source for all shared skills. |
| REQ-002 | Plugin skill trees MUST be generated reproducibly, and validation MUST reject source or inventory drift. |
| REQ-003 | One Git-backed Plugin release MUST provide the selected Skill set to Codex Desktop and Codex CLI for the same personal account. |
| REQ-004 | The shared plugin MUST include both promoted buckets and MUST exclude `misc`, `personal`, `in-progress`, and `deprecated`. |
| REQ-005 | The six governance and integration skills MUST move into root `skills/engineering` and follow promoted documentation and routing rules. |
| REQ-006 | The tracked plugin shell MUST remain directly maintainable while the complete assembled artifact and generated skill tree remain untracked under `dist/`. |
| REQ-007 | Installation, validation, and release commands MUST assemble the artifact before consuming it and MUST NOT install from an incomplete shell. |
| REQ-008 | Repository guidance, manifests, inventories, ADRs, and release documentation MUST describe the unified source and generated-artifact lifecycle. |
| REQ-009 | Formal architecture governance MUST cover every moved governance/integration production source without forbidden parent traversal or an ungoverned production gap. |
| REQ-010 | The repository MUST distinguish the primary local Codex Marketplace from the optional generated Git Marketplace and MUST NOT describe a local filesystem source as web-accessible. |
| REQ-011 | Local validation and optional `marketplace-release` publication MUST derive from the same formal assembled Plugin name, version, inventory, and content fingerprint before the local-only cachebuster is applied. |
| REQ-012 | When the optional Git Marketplace is generated, the release flow MUST validate a publication record containing repository URL, Git reference, catalog and Plugin paths, source tag/commit, version, fingerprint, installation steps, rollback reference, and evidence checklist. |
| REQ-013 | Codex compatibility validation MUST classify every packaged Skill with its host dependencies and MUST exercise representative engineering and productivity packaging plus invocation-policy contracts before release acceptance; signed-in Codex Desktop and CLI invocation remains post-install user acceptance. |

| REQ-014 | The repository MUST restore the one-click local installer, desktop launcher, installer contract tests, and user-facing local-install instructions from the `0.7.1` installation behavior while consuming the current assembled single-source Plugin. |
| REQ-015 | User-facing installation guidance MUST identify the local one-click installer as the primary Codex Desktop and Codex CLI path, MAY retain `marketplace-release` as an optional Codex source, and MUST state that ChatGPT web is unsupported. |
| REQ-016 | Formal architecture MUST restore a `local_install_adapter` that owns local Marketplace registration, Plugin installation, Codex page launch, and retry-safe failure handling. If Plugin installation fails after Marketplace registration, the adapter MUST report that the registration remains available for retry and MUST NOT request removal of a prior installed Plugin. `plugin_assembly_composition` MUST own artifact cache refresh and the boundary between formal version metadata and local-only cachebusters. |
| REQ-017 | When a promoted root Skill and the previously installed Codex Plugin Skill shared a name but differed in behavior, the unified root source MUST preserve the governed Codex workflow behavior so unification does not silently regress existing Codex use. |
| REQ-018 | Invocation metadata MUST have one deterministic two-harness contract: user-invoked Skills carry both Claude's `disable-model-invocation: true` and Codex's `policy.allow_implicit_invocation: false`; model-invoked Skills omit both restrictions and MUST NOT spell the default as `allow_implicit_invocation: true`. |
| REQ-019 | In a fresh task, the exact authorization phrase `開始執行`, optionally accompanied by an explicit canonical Spec path, MUST be classified as confirmed-Spec resume intent rather than a new generic modification request. One confirmed candidate proceeds to verification, multiple candidates require exactly one user selection, and no candidate fails closed with a specific remediation. |
| REQ-020 | The installed Plugin MUST remain the self-contained authority for automatic engineering routing. Repository `AGENTS.md` guidance MUST directly instruct Codex to read and follow the repository rules instead of relying on a bare filename pointer, but router correctness MUST NOT depend on `AGENTS.md`. |
| REQ-021 | Every engineering request MAY enter the model-invoked `ask-matt` router, but only repository-modifying requests or unresolved change-set decisions MUST enter `grilling`; factual explanation, diagnosis, and review remain read-only until modification intent is present. |
| REQ-022 | Personal Codex sharing MUST mean that Codex Desktop and Codex CLI install the same Git-backed Plugin source and release identity; ChatGPT web installation is outside the supported scope. |
| REQ-023 | The complete installable Marketplace tree MUST be generated from `main` into a dedicated publication branch in this repository after stable-release validation; the publication branch MUST NOT become an editable Skill source. |
| REQ-024 | The dedicated personal Marketplace publication branch MUST be named `marketplace-release` and MUST remain distinct from the existing Version Pull Request branch `plugin-release/main`. |
| REQ-025 | The rollback release MUST retain the implemented single-source assembly and governed routing behavior, restore the local installer, remove unsupported ChatGPT web claims and gates, and publish as `0.7.2` without reusing the immutable `0.7.1` tag. Failed automated `0.8.0` and `0.8.1` release tags MUST be removed only with separate explicit maintainer authorization, and remote absence of both tags MUST be verified before the corrected commit is pushed. |
| REQ-026 | The installer MUST assemble before installation, reject an incomplete or stale Plugin shell, preserve the current formal release version, apply any cachebuster only to the local installed manifest, and provide actionable recovery on partial failure. |
| REQ-027 | The supported Windows launcher MUST succeed when invoked without `-PythonCommand`, MUST resolve a Python application without colliding with the case-insensitive `PythonCommand` parameter, MUST report an actionable missing-runtime error instead of generic exit 99 when resolution fails, and MUST retain explicit command injection for tests and maintainers. The regression fix MUST ship as immutable patch release `0.7.3` without moving the `0.7.2` tag. |
| REQ-028 | Unless `-CodexCommand` is explicitly injected, the local installer MUST first select a PATH-discovered Codex application only after a side-effect-free execution probe succeeds; if the PATH candidate is absent or cannot execute, it MUST fall back to a usable Codex Desktop bundled runtime. It MUST report actionable failure when neither candidate is executable. |
| REQ-029 | Before Plugin assembly, the local installer MUST execute a side-effect-free Python capability probe and accept only Python 3.11 or newer. An explicit `-PythonCommand` remains authoritative and MUST pass the probe. Without explicit injection, the installer MUST first accept a compatible PATH `python`; otherwise it MUST ask the Windows Python Launcher for its highest Python 3 runtime, resolve that runtime to an absolute executable path, validate it, and use that same executable for every assembly and validation command. An absent, non-executable, malformed, or older runtime MUST stop before assembly and report the observed candidates plus actionable recovery. |
| REQ-030 | On Windows, the one-click installer MUST detect an existing `dist/governed-engineering-skills` artifact that the launching account cannot inspect or replace. Recovery MUST be limited to that exact repository-relative ignored artifact, MUST refuse repository roots, ancestors, symlinks/reparse targets, and any path outside the resolved repository `dist` directory, MUST first attempt ordinary inherited-access recovery, and MAY request UAC elevation only for a narrowly scoped ACL reset when ordinary recovery is denied. After recovery it MUST revalidate the artifact boundary and restart assembly; refusal, denied elevation, or failed recovery MUST stop before Codex registration and report actionable guidance. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Target a private OpenAI workspace plugin shared by ChatGPT Work web and Codex. |
| DEC-002 | Keep root `skills/` as the canonical source and generate plugin packaging trees. |
| DEC-003 | Include both promoted buckets, `engineering` and `productivity`, in the shared plugin. |
| DEC-004 | Move the six Codex-only governance and integration skills into root `skills/engineering`. |
| DEC-005 | Track the plugin shell but generate the complete artifact, including its skill tree, under ignored `dist/governed-engineering-skills`. |
| DEC-006 | Select whether formal architecture moves to repository root, narrows to packaging only, or retains the six governance skills inside the plugin project. |
| DEC-007 | Move formal architecture governance to repository root so one manifest covers root Skills, Plugin packaging, and assembly boundaries. |
| DEC-008 | Keep the local Marketplace as a development/test channel and add a separate private-Workspace distribution channel; neither channel owns an independent Skill copy. |
| DEC-009 | Keep Workspace publication and installation as administrator-controlled external actions. Repository tooling prepares and verifies the handoff but does not silently publish or enable the Plugin. |

| DEC-010 | Remove the bundled one-click local installer and launcher, retain local Marketplace metadata only for manual maintainer testing, and make the private Workspace listing the sole supported user installation channel. |
| DEC-011 | Use the governed Codex Plugin overlay as the behavior baseline when reconciling duplicate promoted Skill names into their single authoritative root source. |
| DEC-012 | Treat exact `開始執行` in a fresh task as confirmed-Spec resume intent: automatically verify the sole confirmed candidate, ask one candidate-selection question when several exist, and fail closed when none exists. |
| DEC-013 | Keep invocation enforcement self-contained in the Plugin's model-invoked `ask-matt`; make `AGENTS.md` an explicit repository-onboarding pointer only, never a runtime dependency. |
| DEC-014 | Encode model-invoked behavior by omitting invocation policy, not by writing redundant `allow_implicit_invocation: true`; retain paired explicit restrictions only for user-invoked Skills. |
| DEC-015 | Define personal cross-surface sharing as two independent installations from one Git-backed Plugin source and the same release identity; do not require one surface to synchronize installation state to the other. |
| DEC-016 | Publish the generated Marketplace catalog and complete Plugin tree on a dedicated branch of `ShinWeiPeng/skills`, while retaining `main` root Skills as the only editable source. |
| DEC-017 | Name the generated installation branch `marketplace-release`; retain `plugin-release/main` exclusively for automated version-update Pull Requests. |
| DEC-018 | Supersede the personal ChatGPT-web interpretation of DEC-015 through DEC-017: retain `marketplace-release` only for Codex Desktop and Codex CLI distribution. |
| DEC-019 | Preserve the current single-source Skill assembly and governed router improvements rather than reverting the repository tree to the `0.7.1` tag. |
| DEC-020 | Publish the corrected rollback release as `0.7.2`; the existing immutable `0.7.1` tag remains unchanged and no `0.8.0` tag is created. |
| DEC-021 | Restore the `0.7.1` local one-click installation experience on top of the current single-source assembly; the remote Marketplace remains optional and ChatGPT web remains unsupported. |
| DEC-022 | Supersede DEC-020's assumption that no `0.8.0` tag was created: the failed release did create a remote tag, the maintainer explicitly authorized deleting it, and remote inspection MUST prove it absent before `0.7.2` is committed and pushed. |
| DEC-023 | Refine DEC-022 for the concurrent Version PR: after the first correction, automation merged `0.8.1` and created its tag; the maintainer separately authorized deleting `0.8.1`, retaining the latest remote `main` history, and resolving its version state to `0.7.2` without force-pushing. |
| DEC-024 | Repair the one-click installer in place by giving the auto-discovered Python command a distinct local variable, retaining optional `-PythonCommand` injection, adding a no-`PythonCommand` launcher regression fixture, and publishing the correction as `0.7.3` rather than rewriting immutable `0.7.2`. |
| DEC-025 | Resolve Codex with verified PATH-first precedence: honor an explicitly injected command, otherwise probe the PATH candidate without installation side effects and use it when executable; fall back to the Codex Desktop bundled runtime only when PATH is absent or unusable. |
| DEC-026 | Select automatic compatible-Python discovery: after an incompatible PATH `python`, query the Windows Python Launcher for its highest Python 3 runtime, normalize the selected runtime to its absolute executable path, and use that exact interpreter throughout installation. Do not download or silently install Python. Publish the correction as a new immutable patch release rather than rewriting `0.7.3`. |
| DEC-027 | Select bounded automatic Windows ACL recovery. Preserve Codex sandbox isolation globally, but allow the user-launched installer to restore inherited access only on the exact ignored `dist/governed-engineering-skills` artifact. Attempt non-elevated recovery first; request UAC only when required; refuse unsafe, redirected, or out-of-scope targets; and continue installation only after the repaired boundary is revalidated. |

## Architecture Impact

- **Affected level and module:** retain the L0 `plugin_assembly_composition` owner, restore the L3+ `local_install_adapter`, and keep remote Marketplace publication as an optional Codex-only channel.
- **Technical release authority:** retain L3+ `plugin_release_governance_technical`; a publication candidate is admitted only after its stable SemVer, immutable tag intent, assembled inventory, and fingerprint pass existing release governance.
- **Ports, Events, Types, and State:** restore the installer request/result and rollback outcome contracts. `plugin_assembly_composition` owns the ignored artifact and formal-version/local-cachebuster invariant; `local_install_adapter` owns Codex Marketplace registration and Plugin-installation side effects. No queue, callback, execution unit, or long-lived mutable runtime State Object is introduced.
- **Windows ACL recovery:** keep recovery inside `plugin_assembly_composition` before artifact replacement. It is a synchronous, bounded local filesystem operation on one exact ignored path; it introduces no new public Port, Event, Queue, Task, or persistent State Object. The existing blocked outcome gains unsafe-target, elevation-denied, and recovery-failed reasons.
- **Source and Description Views:** add the restored launcher and installer paths, entrypoint, public symbols, side effects, invariants, and failure outcomes to `architecture/manifest.yaml`; update System, Parent, and architecture overview pages and regenerate marker-owned views deterministically.
- **Compatibility boundary:** preserve Plugin ID, bundled Skill paths, invocation policy, stable SemVer authority, immutable release tags, and root-only editable Skill ownership. Replace only the user distribution channel and its evidence schema.
- **ADR:** revise `ADR-0014-personal-git-marketplace-publication.md` so the generated branch is a Codex distribution channel rather than a ChatGPT-web channel. DISC-014 and DISC-015 are the correcting human decision evidence; no architecture-rule exception is requested.

## Flow Execution Impact

- **As-is candidate:** local validation produces an ignored artifact, then release acceptance waits for a managed Workspace handoff and administrator evidence. This cannot satisfy the personal-account target and is rejected by functional admission.
- **Selected candidate:** the one-click launcher assembles and validates one formal artifact, applies a local-only cachebuster, registers the repository Marketplace, and installs it in Codex. Stable-release validation may additionally build and publish the identity-equivalent formal Marketplace tree to `marketplace-release`.
- **Rejected candidate:** publishing the generated tree to a second repository also satisfies functional delivery, but adds another repository authority, credential boundary, synchronization step, rollback reference, and deployment artifact without a selected access-isolation requirement.
- **Execution assurance:** `estimated`. The CI flow is best-effort and has no latency, throughput, memory, power, or real-time product budget. No new thread, queue, retry loop, serialization boundary, or target runtime is introduced. Functional publication and rollback evidence, not performance measurement, determines acceptance.
- **Failure policy:** validation, fingerprint mismatch, stale source tag, incomplete sparse tree, non-fast-forward publication race, or missing credentials blocks publication and leaves the previous `marketplace-release` commit available. A failed user installation is recorded separately from a failed release candidate.

## Evolution Impact

- **Add or modify a Skill:** change only the root promoted bucket; assembly, catalog generation, tests, and the next stable publication carry it to Codex Desktop and Codex CLI.
- **Add an adapter or bundled resource:** update the tracked Plugin shell or authoritative root Skill resource, then validate its generated inventory and relative references before publication.
- **Add another consumer surface:** reuse the same immutable release identity when the surface supports repo Marketplaces; add surface-specific installation evidence without creating another editable Skill tree.
- **Rollback:** repoint `marketplace-release` to the previously validated generated commit through an explicit workflow input, while retaining immutable version tags and leaving `main` untouched.
- **Platform variant:** no installed-runtime platform mapping changes; Codex host differences remain in the compatibility inventory and acceptance evidence.

## Algorithm Impact

| Product feature | Owner | Screening result | Record |
|---|---|---|---|
| Plugin artifact assembly | `plugin_assembly_composition` | Not applicable: existing deterministic inclusion, normalization, inventory, and SHA-256 identity rules do not rank, tune, estimate, or select among data-dependent results. | Existing inventory entry remains sufficient. |
| Marketplace publication-tree generation | `plugin_assembly_composition` | Not applicable: exact path mapping and byte-for-byte identity checks have one prescribed result and no heuristic, statistical, scheduling, optimization, or fallback method choice. | No new `ALG-####` required. |
| Windows ACL recovery | `plugin_assembly_composition` | Not applicable: path admission, ordinary recovery, bounded elevation, revalidation, and refusal use one fixed safety order with no tunable, statistical, optimization, or data-dependent result selection. | No new `ALG-####` required. |

## Recommended Improvements

### Improvement 1: Generate a remote personal Marketplace tree

- **Change:** add a deterministic staging operation that writes `.agents/plugins/marketplace.json` plus the complete `plugins/governed-engineering-skills` tree from the validated artifact, with the catalog source set to `./plugins/governed-engineering-skills`.
- **Expected impact:** Codex users may choose a generated Git source without making it the primary installation dependency.
- **Benefits:** one editable source, one formal release identity, no administrator publication dependency, and auditable branch contents.
- **Costs and disadvantages:** generated branch storage, workflow logic, and an additional optional installation path.
- **Risks:** stale generated content, incorrect sparse paths, or accidental branch editing.
- **Mitigation:** exact inventory/fingerprint comparison, protected generated branch, clean temporary-repository tests, and fail-closed publication.

### Improvement 2: Replace unsupported web evidence with Codex installation evidence

- **Change:** retain repository/ref/path identity while replacing ChatGPT-web evidence with Codex Desktop and Codex CLI installation and invocation records.
- **Expected impact:** release acceptance measures supported Codex behavior instead of an unavailable personal-account web workflow.
- **Benefits:** evidence is tied to the current artifact and each product surface.
- **Costs and disadvantages:** the final four invocation records remain user-visible external checks and cannot be fabricated by repository tests.
- **Risks:** screenshots alone may not prove artifact identity.
- **Mitigation:** bind every record to Plugin name, version, source tag/commit, branch commit, fingerprint, surface, Skill, prompt, result, and evidence-file SHA-256.

### Improvement 3: Integrate publication with stable release governance

- **Change:** publish `marketplace-release` only from the release job after assembly, distribution, Plugin, architecture, version, and publication-record validation pass; never publish from Pull Request validation.
- **Expected impact:** consumers see only stable, validated generated trees.
- **Benefits:** existing SemVer/tag authority remains intact and rollback targets are identifiable.
- **Costs and disadvantages:** publication waits for all gates and requires GitHub Actions content-write permission.
- **Risks:** concurrent or partially completed publication.
- **Mitigation:** existing workflow concurrency, temporary staging, source-tag binding, one generated commit, and atomic branch update after all checks.

### Improvement 4: Recover only the exact inaccessible local artifact

- **Change:** add a Windows ACL preflight before assembly. Resolve and compare the repository root, `dist` parent, and expected Plugin artifact without traversing an inaccessible child; attempt ordinary inherited-access recovery first, then invoke a narrowly scoped elevated helper only when Windows denies the non-elevated repair. Revalidate the exact target before deletion or assembly.
- **Expected impact:** a user-launched reinstall recovers from artifacts created by Codex's sandbox, an administrator, or another account, then installs the current formal Plugin version instead of leaving the Marketplace preview state.
- **Benefits:** preserves sandbox isolation, restores the one-click contract, and prevents a stale inaccessible artifact from hiding the installed version.
- **Costs and disadvantages:** Windows-only recovery code, a possible UAC prompt, and additional ACL fixtures.
- **Risks:** privilege escalation against the wrong directory, reparse-point traversal, or continuing after a partial ACL repair.
- **Dependencies:** exact canonical path admission, Windows identity/ACL inspection, bounded elevation, and retry-safe assembly.
- **Alternatives considered:** fail with manual commands, or relocate all artifacts under `%LOCALAPPDATA%`.
- **Why this is recommended:** it addresses the observed cross-principal failure while changing permissions only on the one ignored artifact the installer already owns.

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-005 | Editing any shared skill requires changing only its root source directory; all six governance/integration skills exist under root engineering and no tracked plugin skill copy remains. | Source inventory, tracked-file inspection, promoted README and manifest checks. | PASS — 28 root Skills; no Plugin-shell Skill tree. |
| AC-002 | REQ-002 | Two clean assembly runs produce byte-equivalent skill inventories, and validation rejects missing, extra, or modified generated skills. | Automated deterministic-assembly and bounded drift-fixture tests. | PASS — deterministic and missing/extra/modified fixtures pass. |
| AC-003 | REQ-003 | One validated assembled release can be installed locally for Codex Desktop and Codex CLI and exposes representative explicit and implicit Skill invocations. | Run the restored installer, inspect the registered local Marketplace and installed manifest, then record matching identity plus invocation results in both Codex hosts. | POST-INSTALL USER ACCEPTANCE — repository fixtures prove the install contract; signed-in host evidence is collected after delivery. |
| AC-004 | REQ-004 | Generated inventory contains every promoted engineering and productivity Skill and no non-promoted Skill. | Compare generated paths against both promoted bucket inventories and negative-list fixtures. | PASS — exact 28-Skill inventory comparison. |
| AC-005 | REQ-005, REQ-008 | Promoted READMEs, top-level README, Claude manifest, router references, docs, and replacement ADR consistently describe all 28 root-source Skills. | Manifest and documentation inventory tests plus repository-wide stale-contract search. | PASS — docs, manifests, invocation metadata, and grouping checks pass. |
| AC-006 | REQ-006 | The tracked shell retains manifest and release infrastructure, while `dist/governed-engineering-skills` stays ignored and reproducible from a clean checkout. | Git-status assertions before and after clean assembly plus plugin artifact validation. | PASS — Git status is unchanged and Plugin ingestion passes. |
| AC-007 | REQ-007 | Every supported install, validation, and release entrypoint assembles first or fails clearly when the artifact is absent or stale. | Entrypoint tests covering clean, absent, current, and stale artifact states. | PASS — state fixtures and job-local release ordering pass. |
| AC-008 | REQ-008 | No active document states that the native Codex/OpenAI plugin is deferred or that packaged Skills are maintained as an independent vendored source. | Repository-wide contract search and documented-command verification. | PASS — active contracts describe root ownership and assembly. |
| AC-009 | REQ-009 | The selected architecture root and source sets validate every governed Python production path after the Skill migration, with no parent traversal and no missing moved source. | Architecture design/development gates and source-set inventory validation. | PASS — both architecture release gates are VERIFIED. |
| AC-010 | REQ-010, REQ-012 | User documentation identifies the one-click local installer as primary, while the optional publication record validates the Git repository, `marketplace-release` reference, catalog and Plugin paths, release identity, rollback, and Codex installation steps. | Rendered documentation review, Marketplace schema/path validation, and publication-record schema validation. | PASS — README and distribution guidance distinguish the local primary path and optional Git branch; malformed publication identities fail closed. |
| AC-011 | REQ-011 | The validated formal artifact and optional `marketplace-release` publication candidate have the same Plugin name, semantic version, complete file inventory, and SHA-256 content fingerprint before local cache localization. | Deterministic assembly, manifest validation, inventory comparison, checksum comparison, and LF/CRLF checkout-equivalence fixture. | PASS — Plugin 0.7.2 has 257 files; localize preserves the formal 0.7.2 prefix and refreshes inventory after adding the cachebuster; production fingerprints normalize text checkout newlines while preserving binary bytes exactly. |
| AC-012 | REQ-003, REQ-013 | The locally installed Plugin is visible in Codex Desktop and Codex CLI, and a new task/session can invoke one representative engineering Skill and one representative productivity Skill in each host. | One local installation followed by a four-case Codex-host invocation checklist with matching formal release identity. | POST-INSTALL USER ACCEPTANCE — not a repository release or push gate. |
| AC-013 | REQ-013 | Every packaged Skill is classified as Codex-compatible or blocked with a specific host-dependency reason. | Static compatibility inventory plus representative negative fixtures and packaging-policy tests. | PASS — all 28 packaged Skills are Codex-compatible with explicit host-dependency lists; malformed inventory fixtures fail. |

| AC-014 | REQ-014, REQ-015 | The restored launcher and installer assemble the current root-owned Plugin, register a local Marketplace, refresh the local Plugin cache, and present actionable success or failure guidance without advertising ChatGPT-web support. | Temp-profile installer integration tests, tracked-file inventory, Marketplace validation, and rendered documentation review. | PASS — the repaired PowerShell suite and actual no-argument launcher cover automatic Python discovery, assembly, registration, installation, cache refresh, exact installed tree, repeated use, and actionable failures. |
| AC-015 | REQ-016 | The repository-root architecture contains a governed `local_install_adapter` module with declared installer entrypoint, public symbols, local filesystem side effects, retry-safe outcomes, and generated Description View references. | Architecture manifest diff, deterministic rendering, installer failure fixtures, and development/release architecture gates. | PASS — Plugin assembly owns cache refresh; the adapter owns Codex registration, installation, page launch, and explicit retry guidance; the Plugin-failure fixture preserves the prior installed tree; generated views are current; both architecture release gates are VERIFIED. |
| AC-016 | REQ-017 | Existing governed router, spec, architecture, runtime-evidence, and review contracts remain present after duplicate Skill reconciliation, and all Plugin contract tests pass against the assembled root-derived artifact. | Assembled Plugin integration validation, invocation-policy checks, and Plugin contract suite. | PASS — integration validation and 162 Plugin contract tests pass. |
| AC-017 | REQ-018 | Every promoted source Skill and assembled Plugin Skill passes a classification matrix proving that manual restrictions are paired, automatic restrictions are omitted, redundant `true` policy is absent, and OpenAI assembly removes only Claude-specific frontmatter. | Source/artifact metadata matrix tests with positive and negative fixtures. | PASS — source/artifact matrix, all three invalid metadata fixtures, and body-content preservation fixture pass in `tests.test_shared_skill_distribution`. |
| AC-018 | REQ-019, REQ-021 | Fresh-task routing tests prove exact `開始執行` with one, many, or zero confirmed Specs; an explicit Spec path; negated or quoted phrases; ordinary read-only discussion; and a modifying request that must enter `grilling`. | Deterministic guided-router unit and integration tests asserting selected Skill, status, candidate evidence, and resume target. | PASS — exact phrase one/many/zero/path, specific zero-candidate remediation, exactly-one selection instruction, and negative phrase fixtures pass; the complete 161-test Plugin suite preserves read-only and modifying routes. |
| AC-019 | REQ-020 | `AGENTS.md` directly instructs Codex to load repository rules, while an assembled-Plugin test with no repository `AGENTS.md` still routes a modifying engineering request through `ask-matt` and the governed decision gate. | Repository instruction-content assertion plus isolated assembled-Plugin routing test. | PASS — repository instruction assertion and isolated assembled-Plugin modifying route pass without consumer `AGENTS.md`. |
| AC-020 | REQ-022 | The personal account can install the same Plugin release identity in Codex Desktop and Codex CLI, with no ChatGPT-web availability assertion. | Two-host installation record plus matching Plugin name, formal version, source reference, and representative invocation evidence. | POST-INSTALL USER ACCEPTANCE — not a repository release or push gate. |
| AC-021 | REQ-023 | A validated stable release produces a dedicated-branch Marketplace tree containing `.agents/plugins/marketplace.json` and the complete `plugins/governed-engineering-skills` package, and regeneration from the same source tag is byte-equivalent. | CI publication fixture, clean-checkout assembly, branch-tree inventory, manifest/path validation, fingerprint comparison, and mutation rejection. | PASS locally — repeated candidates have identical Git tree IDs; unsafe output, mutation, stale fingerprint, stale tag, and branch-commit mismatch fail closed. Actual branch publication remains an external release action. |
| AC-022 | REQ-024 | Marketplace documentation, workflow fixtures, and user evidence consistently use `marketplace-release`, while version-governance fixtures continue to use `plugin-release/main` only for the Version Pull Request. | Repository-wide structured search and workflow contract tests. | PASS locally — structured search and release/version workflow contracts preserve the two distinct branch identities. |
| AC-023 | REQ-025 | Version metadata, changelog, release state, and Plugin manifest identify `0.7.2`; `0.7.1` remains bound to its existing tag; failed remote `0.8.0` and `0.8.1` tags are absent; no active documentation or gate claims ChatGPT web can add the Git Marketplace. | Version-governance checks, remote tag inspection, stale-contract search, focused distribution tests, and clean Git diff. | PASS — formal metadata identifies 0.7.2; the immutable 0.7.1 tag remains; each destructive deletion received explicit maintainer authorization; subsequent `git ls-remote --tags` queries returned no 0.8.0 or 0.8.1 ref. |
| AC-024 | REQ-026 | Positive, repeated-install, missing-runtime, incomplete-artifact, stale-cache, and simulated partial-failure fixtures prove assembly-first installation, idempotence, formal-version preservation, local-only cachebusting, and recovery guidance. | Isolated temporary-home PowerShell integration tests with fake Codex CLI fixtures and exact installed-tree assertions. | PASS — the complete suite covers injected and automatic runtime resolution, repeated refresh, duplicate Marketplace, missing runtime, incomplete artifact, cachebuster replacement, assembly and CLI failures, recovery logs, and exact copied inventory. |
| AC-025 | REQ-027 | A regression fixture invokes the repository-root installer without `-PythonCommand`, reproduces the `Source`-property exit-99 failure before repair, and passes after repair while the explicit-injection, missing-Python, repeated-install, exact-tree, and real user-launched installer paths remain valid. Formal metadata and the new immutable tag identify `0.7.3`; `0.7.2` remains unchanged. | RED/GREEN PowerShell integration fixture, direct launcher acceptance, full installer suite, version-governance checks, remote tag inspection, and GitHub Actions Windows matrix. | PASS locally — RED reproduced exit 99; GREEN passes without `-PythonCommand`; the launcher fixture now uses automatic Python discovery, the missing-Python fixture returns actionable exit 13, and the complete installer suite passes. Remote tag and CI evidence remain pending until push. |
| AC-026 | REQ-028 | Installer fixtures prove that an executable PATH Codex wins over an available Desktop runtime, an absent or non-executable PATH candidate falls back to a usable Desktop runtime, explicit `-CodexCommand` injection remains authoritative, and no executable candidate fails with actionable recovery guidance. | Isolated temporary-home PowerShell integration tests with fake PATH and Desktop runtimes, side-effect-free probe assertions, command-selection logs, and exit-code checks. | PASS locally — RED selected the inaccessible Desktop runtime and returned exit 12 despite a usable PATH CLI; GREEN probes `--version`, performs no installation side effect during the probe, prefers executable PATH, falls back to Desktop after a failed PATH probe, preserves explicit injection, and returns actionable exit 11 when neither candidate works. |
| AC-027 | REQ-029 | Installer fixtures prove that a compatible explicit command remains authoritative, compatible PATH Python wins, incompatible PATH Python falls back to the Python Launcher's highest compatible Python 3 runtime, the selected absolute interpreter performs both assembly and validation, and Python 2.x/3.10 plus malformed/non-executable candidates stop before assembly with actionable recovery. | Isolated PowerShell tests with fake Python commands, launcher/runtime mappings, an assembly-call sentinel, exact selected-path assertions, and the complete installer contract suite on Windows. | PASS locally — RED returned exit 30 after sending the Python 3.10 PATH candidate directly to assembly; GREEN proves compatible PATH never invokes the launcher, rejects explicit Python 2.7 plus malformed/non-executable probes before artifact/Codex side effects, resolves `py -3` to one exact absolute selected command, records that same command executing re-probe/assemble/validate/localize, and the 211-second exact-tree installer suite exits 0. |
| AC-028 | REQ-030 | Windows fixtures reproduce an artifact owned by a different principal with no launching-user access, prove non-elevated recovery when inheritance is sufficient, prove a bounded elevation request only for the exact expected artifact when required, and reject repository roots, ancestors, sibling paths, reparse targets, denied UAC, and partial recovery before Codex registration. A successful recovery reassembles and installs formal version `0.7.4` and the installed detail view exposes that formal prefix. | Isolated Windows ACL integration fixtures using disposable temporary repositories and principals where available; mocked elevation contract tests for CI; exact path, owner/access, Codex-call sentinel, artifact inventory, installed manifest, and UI-facing metadata assertions. | PARTIAL locally — RED failed because no recovery helper existed; GREEN recursively validates every descendant, checks effective `Delete` or parent `DeleteChild` permission on every existing entry, and rejects root/dist/sibling/outside/root-or-nested-reparse targets. ACL repair walks breadth-first, admits each non-reparse entry before resetting only that entry, and a junction fixture proves the destination ACL remains byte-for-byte unchanged. Fixtures prove ordinary-before-elevated ordering, deny readable-but-not-replaceable existing children, block denied/partial recovery before Codex, and install an exact inventory whose manifest begins `0.7.4+codex.` after mocked recovery. Formal assembly normalizes inherited Windows ACLs before atomic replacement; the resulting 268-file `0.7.4` artifact grants the interactive `Hugo` account FullControl while retaining sandbox ownership. Automated suites and gates pass, but a real second-principal/UAC run plus user-visible Codex detail-page confirmation remain post-install acceptance before AC-028 can be marked PASS. |

## Alternatives Comparison

| Alternative | Observable result | Benefits | Costs and risks | Decision |
|---|---|---|---|---|
| Generated `marketplace-release` branch in this repository | Codex Desktop and Codex CLI install from one repository/ref and matching Plugin identity. | One repository authority; no second editable tree or extra credential boundary. | Generated branch must be protected and publication tested. | Selected. |
| Separate generated distribution repository | Codex hosts install from a clean consumer-only repository. | Stronger repository/access isolation. | Extra repository, credentials, rollback reference, and synchronization state. | Rejected because no isolation requirement exists. |
| Commit the assembled Plugin tree on `main` | The current default branch becomes directly installable. | Simplest consumer URL. | Duplicates generated Skills in normal source history and reintroduces source drift. | Rejected by root-only ownership and ignored-artifact requirements. |
| Managed private Workspace listing | Administrator publishes once for a managed workspace. | Central workspace policy and listing. | Does not match the selected personal-account scope and requires unavailable admin/listing evidence. | Superseded. |

## Implementation Order

1. Restore the `0.7.1` launcher, PowerShell installer, and isolated installer fixtures, adapting them to assemble from the current root-owned Skills before installation.
2. Restore the governed `local_install_adapter` architecture declaration and regenerate Description Views.
3. Remove unsupported ChatGPT-web instructions and release-evidence requirements; retain `marketplace-release` only as an optional Codex distribution artifact.
4. Reconcile package, Plugin manifest, changelog, release state, and release intent to `0.7.2` without moving the immutable `0.7.1` tag.
5. Run the complete installer, distribution, Plugin, version, architecture, and regression validation matrix from a clean temporary profile.
6. Commit and push the validated 0.7.2 implementation; then let the user run the delivered installer and record optional signed-in Codex Desktop/CLI acceptance evidence.
7. Add a RED regression fixture that omits `-PythonCommand`, repair the case-insensitive variable collision without moving discovery into the CMD launcher, and retain explicit command injection.
8. Advance formal release metadata to `0.7.3`, rerun all installer and release gates, publish a new immutable tag, and prove the existing `0.7.2` tag did not move.
9. Add a RED cross-principal ACL fixture, implement exact-target non-elevated/elevated recovery before assembly, preserve refusal and UAC-denied outcomes, and rerun installation to prove `0.7.4` reaches the installed detail view.

## Validation and Acceptance Gates

| Gate | Validation method and reproducible step | Expected observable output | Pass condition | Evidence format |
|---|---|---|---|---|
| Validation Enablement | Assemble into a temporary directory, generate a Marketplace tree, import it into a temporary Git repository, and run positive plus missing-path, traversal, stale-fingerprint, wrong-ref, and mutation fixtures. | Deterministic tree and explicit fail-closed errors without contacting the production branch. | Positive fixture passes twice byte-equivalently; every negative fixture fails for its intended reason. | Test log with command, exit code, generated inventory, tree hash, and fixture verdicts. |
| Per-change Development Validation | Run `python -m unittest tests.test_shared_skill_distribution -v`, Plugin contract tests, distribution validation, artifact validation, schema checks, documentation/link checks, and a clean Git-status assertion. | All focused tests pass; no generated tree appears as an editable `main` source. | Every command exits `0`, expected negative fixtures fail closed, and Git status changes only in intended tracked files. | CI logs plus hashed test/result artifacts. |
| Final Codex Acceptance | After delivery, run the restored local installer, then use the installed Plugin in Codex Desktop and Codex CLI; in a fresh task/session invoke one engineering and one productivity representative in each host. | Both hosts report the same formal Plugin version; the installed manifest may contain only the governed local cachebuster; all four invocations follow the selected Skill. | User acceptance is recorded after install and does not block the repository commit or push. | Installer log plus optional exported-task or terminal evidence. |
| Release Acceptance | Rebuild the release composition; run installer integration tests, `python tools/architecture/architecture_cli.py gate --phase release --manifest architecture/manifest.yaml --adoption architecture/adoption.yaml --baseline architecture/baseline.yaml`, deterministic render comparison, full regression, and version checks before commit and push. | Release gates pass; the installer consumes the assembled `0.7.3` Plugin; no ChatGPT-web contract remains active; optional Marketplace publication remains identity-equivalent when generated. | Every required command exits `0`; architecture and generated views are current; direct launch succeeds without `-PythonCommand`; `0.7.1` and `0.7.2` tag identities are unchanged. | Separate validation and release evidence with command, exit code, minimal raw output, installed inventory, version, fingerprint, and PASS/FAIL/BLOCKED verdict. |
| Windows ACL Recovery Acceptance | In a disposable Windows repository, create the expected artifact under a different principal or equivalent restrictive ACL, launch the public installer as the normal user, exercise ordinary recovery, bounded UAC acceptance, UAC denial, unsafe-path, and reparse-path fixtures, then inspect the installed manifest. | Only the exact ignored artifact can be repaired; unsafe or denied cases stop before Codex side effects; the positive case installs the current `0.7.4` formal prefix. | Every positive fixture exits `0`; every negative fixture returns its specified recovery code and message; no ACL outside the disposable artifact changes; installed manifest and cache inventory match the rebuilt candidate. | Before/after ACL export, resolved paths, installer log, Codex sentinel, artifact inventory, installed manifest, exit codes, and PASS/FAIL verdicts. |

No physical-device, scheduler, OS-native trace, real-time, performance, or resource validation applies. The external product-surface checks are necessary because repository tests cannot prove that the signed-in ChatGPT account actually lists, installs, and invokes the Plugin on either product surface.

## Relationships

| Source | Relation | Target | Rationale |
|---|---|---|---|
| DEC-005 | refines | SPEC-0011 | Extend portable plugin governance with a single root Skill source and assembled Codex Plugin artifact. |
| DEC-007 | supersedes | DEC-006 | Resolve the reopened architecture-root choice in favor of one repository-root governed system. |

| DEC-010 | refines | DEC-008 | Preserve a manual developer test source while removing the supported one-click local installation lane. |
| DEC-011 | refines | DEC-002 | Define how duplicate Skill bodies are reconciled while retaining root ownership. |
| DEC-012 | refines | DEC-011 | Make the preserved governed router deterministic for fresh-task execution authorization. |
| DEC-013 | refines | DEC-009 | Preserve explicit authorization and governance without coupling installed Plugin behavior to repository-local instructions. |
| DEC-014 | refines | DEC-011 | Make the invocation classification inherited from the governed baseline unambiguous across both harnesses. |
| DEC-015 | supersedes | DEC-001 | Replace the earlier managed private-Workspace target with personal, independent installation from one Git-backed source. |
| DEC-016 | refines | DEC-005 | Publish the existing deterministic assembled artifact without making its generated tree editable on `main`. |
| DEC-016 | refines | DEC-015 | Provide both independent surface installations from one repository-controlled publication source. |
| DEC-017 | refines | DEC-016 | Give the installable publication branch an unambiguous user-facing identity that does not collide with version-PR automation. |
| DEC-015 | supersedes | DEC-009 | Replace administrator-controlled Workspace installation with user-owned independent installation on each personal-account surface. |
| DEC-016 | supersedes | DEC-008 | Replace the private-Workspace lane with a generated Git Marketplace branch while retaining maintainer-only local testing. |
| DEC-016 | supersedes | DEC-010 | Make the personal Git Marketplace, rather than a private Workspace listing, the supported user installation source. |
| DEC-018 | supersedes | DEC-015 | Correct the unsupported assumption that a personal Git Marketplace can be added from ChatGPT web. |
| DEC-018 | refines | DEC-016 | Retain the generated branch as a Codex-only distribution source. |
| DEC-019 | refines | DEC-011 | Preserve the unified governed Skill behavior while removing only the unsupported surface contract. |
| DEC-020 | refines | SPEC-0007 | Apply an explicit pre-tag rollback release without reusing an immutable tag. |
| DEC-021 | supersedes | DEC-010 | Restore the supported one-click local installation lane after the cross-surface premise proved false. |
| DEC-021 | refines | DEC-018 | Make local installation primary while keeping any remote Marketplace Codex-only and optional. |
| DEC-021 | refines | DEC-019 | Restore installation behavior without discarding the unified Skill source or governed router. |
| DEC-022 | supersedes | DEC-020 | Correct the disproven no-0.8.0-tag assumption with an explicitly authorized remote-tag deletion and verification. |
| DEC-022 | refines | SPEC-0007 | Preserve immutable release governance by recording and verifying the authorized correction before the 0.7.2 release. |
| DEC-023 | refines | DEC-022 | Extend the authorized correction to the independently created 0.8.1 tag while retaining remote history. |
| DEC-023 | refines | SPEC-0007 | Resolve the latest remote version state through a normal descendant commit rather than rewriting `main`. |
| DEC-024 | refines | DEC-021 | Preserve the selected one-click user experience while correcting only its Python discovery implementation and test seam. |
| DEC-024 | refines | SPEC-0007 | Publish the correction as the next immutable patch release instead of moving the existing `0.7.2` tag. |
| DEC-025 | refines | DEC-021 | Preserve the one-click Codex installation experience while selecting an actually executable local runtime. |
| DEC-025 | refines | DEC-024 | Add the runtime-selection contract exposed while validating the focused Python-discovery repair. |
| DEC-026 | refines | DEC-024 | Preserve the one-click installer while validating and normalizing its Python runtime before assembly. |
| DEC-026 | refines | SPEC-0007 | Deliver the correction as the next immutable patch release instead of rewriting `0.7.3`. |
| DEC-027 | refines | DEC-021 | Preserve the selected one-click installation experience when a previous ignored artifact belongs to another Windows principal. |
| DEC-027 | refines | REQ-026 | Extend actionable partial-failure recovery with bounded exact-target ACL repair before assembly. |

## Out of Scope

- Submitting the Plugin to OpenAI's universal public Plugin Directory.
- Shipping `misc`, `personal`, `in-progress`, or `deprecated` skills.
- Installing or enabling the Plugin without an explicit user-launched installer action.
- Treating the local Marketplace or local Plugin cache as a synchronization mechanism for ChatGPT Work web.

- Requiring installation or enablement state to synchronize automatically between ChatGPT Work web and Codex Desktop.
- Publishing this private Plugin to the universal public Plugin Directory.
- Supporting installation of the private Git Marketplace in ChatGPT web.
## Open Decisions

None.

## Discussion Context

### DISC-001: Select distribution scope

- **Situation:** The repository could unify only local maintenance, distribute privately to a workspace, or publish publicly.
- **Question:** Which distribution scope should the change target?
- **Options and tradeoffs:** Local-only leaves web installation separate; private workspace distribution avoids public review; public distribution adds review and compatibility obligations.
- **User answer:** 2
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-001, REQ-003, AC-003.

### DISC-002: Select authoritative source layout

- **Situation:** Root bucketed Skills and the Codex plugin contained separate copies.
- **Question:** Which repository layout should own editable Skill content?
- **Options and tradeoffs:** Root ownership preserves buckets; plugin ownership disrupts existing docs; independent packages add migration complexity.
- **User answer:** 1
- **Explicit rationale:** The user wanted to understand engineering and productivity and previously recognized only engineering.
- **Resulting impact:** DEC-002, REQ-001, REQ-002, AC-001, AC-002.

### DISC-003: Select promoted bucket scope

- **Situation:** Engineering workflows reuse productivity Skills such as `grilling`.
- **Question:** Include both promoted buckets, engineering only, or separate plugins?
- **Options and tradeoffs:** Both preserves dependencies; engineering-only requires refactoring; separate plugins create two installation states.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-003, REQ-004, AC-004.

### DISC-004: Select governance Skill source

- **Situation:** Six Codex governance/integration Skills were outside the root promoted buckets.
- **Question:** Move them into engineering, retain external vendoring, or remove them?
- **Options and tradeoffs:** Moving gives all Skills one source; vendoring retains a second source; removal breaks the governed router flow.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-004, REQ-001, REQ-005, AC-001, AC-005.

### DISC-005: Select generated artifact lifecycle

- **Situation:** The plugin shell contains meaningful infrastructure while its tracked Skill tree duplicates more than two hundred source files.
- **Question:** Commit the full artifact, generate everything, or retain a tracked shell with an ephemeral Skill tree?
- **Options and tradeoffs:** Full commits simplify direct installation but create duplicate diffs; full generation hides manifest behavior; a tracked shell preserves inspectability and removes Skill duplication.
- **User answer:** 3
- **Explicit rationale:** The user requested detailed comparison and then selected the tracked-shell approach.
- **Resulting impact:** DEC-005, REQ-006, REQ-007, AC-006, AC-007.

### DISC-006: Select the formal architecture root

- **Situation:** The Plugin-root manifest cannot reference governance production sources moved to root Skills because parent traversal is forbidden.
- **Question:** Move formal architecture to repository root, maintain two architecture projects, or keep the six governance Skills inside the Plugin project?
- **Options and tradeoffs:** A root architecture preserves one governed system with a larger migration; two projects split validation and cross-project ownership; retaining the six Skills minimizes change but abandons the selected root-only source layout.
- **User answer:** 1
- **Explicit rationale:** The user wants to understand why an assembly build is necessary and how the complete development flow works.
- **Resulting impact:** DEC-007 supersedes DEC-006; REQ-009 selects repository-root architecture governance validated by AC-009.

### DISC-007: Separate local testing from Workspace distribution

- **Situation:** The existing installer registers a local filesystem Marketplace for Codex, while the confirmed goal requires the same Plugin Skills in ChatGPT Work web and Codex.
- **Question:** Should the modification proposal add a Workspace-accessible publication lane instead of treating local Plugin installation as cross-product distribution?
- **Options and tradeoffs:** Keeping only the local Marketplace cannot satisfy the web requirement; replacing local installation would weaken development feedback; retaining local testing and adding a separate private-Workspace lane preserves both while adding administrator-controlled release work.
- **User answer:** Requested a modification proposal.
- **Explicit rationale:** The user observed that the existing Plugin installation still does not make the same Skills available on web and desktop and requested a modification proposal.
- **Resulting impact:** DEC-008, DEC-009, REQ-010 through REQ-013, and AC-010 through AC-013.

### DISC-008: Decide the remaining local-install scope

- **Situation:** The proposal retained a local-development installation lane, but the user stated that the local installer does not need to remain.
- **Question:** Remove only the one-click installer while retaining manual Marketplace testing, or remove all local Marketplace support?
- **Options and tradeoffs:** Keeping Marketplace metadata without an installer preserves maintainer testing and removes the user-facing local path; removing all local support simplifies the repository further but prevents local Plugin installation tests before Workspace publication.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-010 refines DEC-008; REQ-014 through REQ-016 and AC-014 through AC-015.

### DISC-009: Reconcile duplicate Skill behavior

- **Situation:** Root and Codex Plugin copies shared names but some Plugin copies contained newer governed routing, spec, architecture, and validation behavior.
- **Question:** Which behavior should remain when each duplicate becomes one root-owned Skill?
- **Options and tradeoffs:** Keeping the older root bodies would simplify the diff but regress currently installed Codex workflows; preserving the governed Plugin behavior requires updating existing promoted Skills but yields one non-regressing source.
- **User answer:** Start executing the selected unified Plugin plan.
- **Explicit rationale:** The requested outcome is the same Skill behavior on desktop and web; unification must not silently downgrade the existing Codex workflows.
- **Resulting impact:** DEC-011 refines DEC-002; REQ-017 and AC-016 make the reconciliation explicit.

### DISC-010: Classify fresh-task execution authorization

- **Situation:** A fresh Codex task can receive the exact authorization phrase `開始執行` without conversational state, while the repository may contain zero, one, or several confirmed canonical Specs. Treating the phrase as an ordinary modification term can start the wrong interview or select the wrong change set.
- **Question:** Should fresh-task `開始執行` resume a confirmed Spec, start a new generic modification interview, or require an explicit Spec path every time?
- **Options and tradeoffs:** Confirmed-Spec resume preserves the established authorization boundary and asks only when candidate identity is ambiguous; generic modification is simpler but confuses execution with proposal creation; mandatory explicit paths are deterministic but impose unnecessary user burden when there is only one valid candidate.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-012; REQ-019 and REQ-021; AC-018.

### DISC-011: Define personal cross-surface sharing

- **Situation:** The personal account exposes a Git Marketplace form, but official OpenAI documentation does not guarantee that installation state synchronizes between ChatGPT Work web and Codex Desktop.
- **Question:** Must one installation automatically synchronize to the other surface, or may each surface install independently from the same source?
- **Options and tradeoffs:** Independent installation uses one source and release identity without depending on undocumented synchronization; best-effort synchronization adds a capability probe and fallback; mandatory synchronization blocks delivery when the product does not provide it.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-015 supersedes DEC-001; REQ-022 and AC-020 define the new personal cross-surface acceptance boundary.

### DISC-012: Select the Git publication topology

- **Situation:** The complete Plugin tree is generated under ignored `dist/` and therefore is absent from the GitHub `main` branch consumed by the personal Marketplace form.
- **Question:** Should the generated Marketplace tree live on a dedicated branch in this repository or in a separate distribution repository?
- **Options and tradeoffs:** A dedicated branch keeps one repository and one release authority but must be protected from manual editing; a separate repository provides stronger distribution isolation but adds repository, credential, and synchronization maintenance.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-016 refines DEC-005 and DEC-015; REQ-023 and AC-021 require a generated same-repository publication branch.

### DISC-013: Name the Marketplace publication branch

- **Situation:** The repository already reserves `plugin-release/main` for automated version-update Pull Requests, so a similarly named installation branch would be easy to confuse with release-authoring state.
- **Question:** Which stable Git reference should users enter in the personal Marketplace form?
- **Options and tradeoffs:** `marketplace-release` clearly describes installable catalog content; `plugin-release` is shorter but collides conceptually with `plugin-release/main`; `personal-marketplace` is explicit today but unnecessarily limits future sharing.
- **User answer:** 1
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-017 refines DEC-016; REQ-024 and AC-022 reserve `marketplace-release` for installation while preserving `plugin-release/main` for Version Pull Requests.

### DISC-014: Correct the unsupported ChatGPT-web channel

- **Situation:** The user's ChatGPT web interface exposes MCP Plugin creation but no Git Marketplace source, and official OpenAI documentation limits repo/personal Marketplace availability by surface.
- **Question:** Should the project target the public Plugin Directory, Codex-only distribution, or managed Workspace publication?
- **Options and tradeoffs:** Public submission enables cross-surface discovery but makes the Plugin public and requires review; Codex-only retains private Git distribution but drops web support; Workspace publication requires an unavailable managed Workspace.
- **User answer:** Codex Desktop and Codex CLI only.
- **Explicit rationale:** The user chose to continue using the old private Codex installation approach.
- **Resulting impact:** DEC-018 supersedes the web interpretation of DEC-015; REQ-003, REQ-013, REQ-015, REQ-022, AC-003, AC-012, AC-013, and AC-020 are narrowed to Codex hosts.

### DISC-015: Select the rollback depth and release version

- **Situation:** A full rollback to the `0.7.1` tag would discard the single-source assembly and governed router work, while a targeted rollback removes only unsupported web distribution claims. The immutable `0.7.1` tag cannot identify a new commit.
- **Question:** Revert the complete repository tree or preserve current engineering improvements and remove only the unsupported web channel?
- **Options and tradeoffs:** Full rollback recreates the old tree but discards 366-file improvements; targeted rollback preserves the improvements and requires focused contract changes. A new `0.7.2` release avoids reusing the existing tag.
- **User answer:** Option 2 — targeted rollback.
- **Explicit rationale:** No additional rationale was stated.
- **Resulting impact:** DEC-019 and DEC-020; REQ-025 and AC-023.

### DISC-016: Select the Codex installation experience

- **Situation:** The targeted rollback could retain the newer Git Marketplace command or restore the `0.7.1` user-launched local installer and desktop launcher.
- **Question:** Which installation path should be the supported Codex Desktop/CLI experience?
- **Options and tradeoffs:** The local installer restores the familiar one-click flow and avoids a remote branch dependency but requires filesystem/cache integration tests; the Git Marketplace command has less installer code but does not match the requested previous experience.
- **User answer:** Option 1 — restore the local one-click installer.
- **Explicit rationale:** The user wants to return to the previous installation method.
- **Resulting impact:** DEC-021; REQ-014, REQ-015, REQ-016, REQ-025, REQ-026, AC-003, AC-012, AC-014, AC-015, AC-024.

### DISC-017: Authorize correction of the failed 0.8.0 release tag

- **Situation:** Remote inspection found `governed-engineering-skills@0.8.0` even though Marketplace publication failed, contradicting DEC-020 and blocking a governed 0.7.2 release.
- **Question:** May the failed remote 0.8.0 tag be deleted before committing and pushing the corrected 0.7.2 release?
- **Options and tradeoffs:** Deleting the tag restores the selected 0.7.x release line but is an irreversible external correction; retaining it requires a monotonically newer formal version and abandons the selected 0.7.2 identity.
- **User answer:** `同意刪除遠端 governed-engineering-skills@0.8.0 標籤`.
- **Explicit rationale:** The user explicitly authorized the destructive remote correction after its consequences were explained.
- **Resulting impact:** DEC-022 supersedes DEC-020; REQ-025 and AC-023 require verified remote absence before commit.

### DISC-018: Authorize correction of the concurrent 0.8.1 release tag

- **Situation:** After the 0.8.0 tag was deleted, the already-running Version PR #31 merged into remote `main`, advanced formal metadata to 0.8.1, and created `governed-engineering-skills@0.8.1`; Git correctly rejected the pending non-fast-forward push.
- **Question:** May the new remote 0.8.1 tag be deleted and the latest remote history be resolved to the selected 0.7.2 state?
- **Options and tradeoffs:** Deleting 0.8.1 and replaying the corrected commit preserves remote history while restoring the selected version; retaining 0.8.1 requires abandoning 0.7.2; force-pushing would rewrite shared history and is rejected.
- **User answer:** `同意刪除遠端 governed-engineering-skills@0.8.1 標籤，並將遠端版本修正為 0.7.2`.
- **Explicit rationale:** The user separately authorized deletion of the newly created tag and reaffirmed the 0.7.2 target.
- **Resulting impact:** DEC-023 refines DEC-022; REQ-025 and AC-023 now require both 0.8.x tags absent and a normal descendant push.

### DISC-019: Select the one-click installer regression repair

- **Situation:** Directly launching `Install Governed Engineering Skills.cmd` without parameters reaches the root orchestrator's Python discovery branch. PowerShell treats the typed `$PythonCommand` parameter and local `$pythonCommand` assignment as the same case-insensitive variable, coerces the discovered application object to a string, and then fails when reading `.Source`. Existing fixtures always supplied `-PythonCommand`, so they did not exercise the user path they claimed to cover.
- **Question:** Apply a focused in-place repair, move Python discovery into the CMD launcher, or require users to supply a Python path?
- **Options and tradeoffs:** The focused repair preserves the one-click contract and keeps discovery in one owner with a new regression fixture; CMD discovery duplicates orchestration policy across layers; mandatory path input removes the requested one-click experience.
- **User answer:** Option 1.
- **Explicit rationale:** The user selected the focused repair after confirming earlier versions did not exhibit the regression.
- **Resulting impact:** DEC-024; REQ-027 and AC-025 require no-argument discovery coverage and immutable `0.7.3` publication.

### DISC-020: Select Codex runtime precedence

- **Situation:** The focused Python-discovery repair exposed a separate Windows environment issue: `Get-Command codex` resolves an inaccessible WindowsApps alias while Codex Desktop provides a usable bundled runtime. A provisional Desktop-first change made the real installer pass, but code review found that it changes the selection policy and may ignore a maintainer's intentionally configured PATH CLI.
- **Question:** When both locations exist, which Codex executable should the installer use?
- **Options and tradeoffs:** A verified PATH-first policy respects an intentionally configured CLI and falls back to Desktop when the PATH candidate cannot execute; Desktop-first is most direct for desktop users but overrides a usable PATH selection; PATH-only preserves the prior policy but leaves this user's one-click installation broken.
- **User answer:** Option 1 — PATH first with execution validation, then Desktop fallback.
- **Explicit rationale:** After clarifying that PATH only locates a candidate and does not prove it executable, the user selected the recommended policy that retains an intentional PATH CLI while recovering from an inaccessible WindowsApps candidate.
- **Resulting impact:** DEC-025; REQ-028 and AC-026 define verified PATH-first resolution and Desktop-runtime fallback. OD-001 is resolved.

### DISC-021: Select Python compatibility handling

- **Situation:** A second Windows computer resolves `python` from PATH, but that runtime is too old to parse the assembler's f-string syntax. The installer currently checks only whether a command exists, so assembly begins and exposes a raw `SyntaxError` instead of a prerequisite message.
- **Question:** After detecting that the PATH `python` is older than 3.11, should the installer stop with recovery instructions or automatically search the Windows Python Launcher for an installed compatible runtime?
- **Options and tradeoffs:** Immediate stop is the smallest and most predictable change but rejects a computer that already has Python 3.11+ installed under `py`; automatic discovery preserves one-click installation and handles stale PATH configuration, but requires deterministic precedence and more fixtures. Bundling Python would remove the prerequisite but substantially increases package size, security maintenance, and release complexity.
- **User answer:** Automatically find the installed Python version and use the corresponding compatible command for installation.
- **Explicit rationale:** A computer may already contain a compatible Python even when PATH points to an older runtime; the one-click installer should select and consistently use the compatible interpreter it finds.
- **Resulting impact:** DEC-026 resolves OD-002; REQ-029 and AC-027 require compatible PATH-first discovery, Python Launcher fallback, absolute-path normalization, and same-interpreter execution.

### DISC-022: Select cross-account Windows ACL recovery

- **Situation:** The validated `0.7.4` artifact was assembled inside the Codex sandbox and inherited an ACL owned by `CodexSandboxOffline` without access for the interactive `Hugo` account. The public installer selected compatible Python successfully but failed with `WinError 5` before installing `0.7.4`, leaving Codex on the Marketplace preview page where no installed version is shown.
- **Question:** Should the installer repair only the exact inaccessible ignored artifact automatically, stop with manual commands, or relocate all local artifacts to a per-user directory?
- **Options and tradeoffs:** Bounded automatic recovery preserves one-click installation but may require one UAC prompt and strict path guards; manual recovery is most conservative but requires terminal work; relocation avoids cross-account repository ACLs but changes established assembly, testing, release, and Marketplace paths.
- **User answer:** Option 1.
- **Explicit rationale:** No additional rationale was stated; the selected recommended option restores the one-click flow while retaining Codex sandbox isolation and limiting elevated permission changes to the exact ignored artifact.
- **Resulting impact:** DEC-027; REQ-030 and AC-028 require exact-target admission, ordinary recovery before UAC, unsafe-target refusal, post-repair revalidation, and no Codex side effects on recovery failure.

## Routing/Gates

- Grilling: PASS; bounded exact-target Windows ACL recovery is selected after the compatible-Python decision.
- Architecture proposal and implementation: PASS; `plugin_assembly_composition` owns artifact assembly and local cache identity mutation, `local_install_adapter` owns Codex registration and installation, JSON Schema types and validation outcomes are cataloged, generated Description Views are current, and development/release gates return `PASS: VERIFIED`.
- TDD: PASS; RED proved the recovery helper absent, and GREEN covers exact-path admission, reparse refusal, ordinary-before-elevated repair, denied/partial recovery, pre-assembly orchestration, zero Codex side effects on failure, staging ACL inheritance, exact installed tree, and the formal `0.7.4` prefix.
- Development and release validation: PASS locally; formal assembly produces 268 files at version `0.7.4`, distribution and integration validators pass, the complete installer suite passes in 245 seconds, 32 shared-distribution tests, 163 Plugin tests, and 105 architecture tests pass, version governance is consistent, and the release architecture gate returns `PASS: VERIFIED`. Normal-user detail-page confirmation remains post-install acceptance.
- Cross-platform release fingerprint: PASS; the LF/CRLF equivalence regression fixture passes, binary content remains byte-sensitive, and Windows plus Git-archive checkout calculations agree.
- Codex-host acceptance: post-install user acceptance; no ChatGPT-web or external evidence gate blocks repository delivery.
- Remote release identity: PASS; the maintainer separately authorized deletion of failed `governed-engineering-skills@0.8.0` and `@0.8.1` tags, subsequent remote ref queries proved both absent, and the correction is rebased onto the latest remote `main` without rewriting it.
- Spec and Standards review: pending final two-axis review of DEC-027 / REQ-030 / AC-028.

## Revision History

| Revision | Date | Summary |
|---|---|---|
| 1 | 2026-08-10 | Started the shared Skill distribution decision. |
| 2 | 2026-08-10 | Selected private workspace distribution. |
| 3 | 2026-08-10 | Selected root Skills as canonical. |
| 4 | 2026-08-10 | Included both promoted buckets. |
| 5 | 2026-08-10 | Moved governance and integration Skills into root engineering. |
| 6 | 2026-08-10 | Selected a tracked plugin shell with an ignored assembled distribution artifact. |
| 7 | 2026-08-10 | Normalized canonical schema fields and traceability without changing decisions. |
| 8 | 2026-08-10 | Reopened after the architecture root could not legally reference moved root production sources. |
| 9 | 2026-08-10 | Selected repository-root formal architecture governance. |
| 10 | 2026-08-10 | Reopened to separate Codex-local testing from private Workspace publication, add cross-product acceptance requirements, and normalize legacy answer markers. |
| 12 | 2026-08-10 | Removed the one-click local installer from the proposal while retaining manual maintainer Marketplace testing. |
| 13 | 2026-08-10 | Reconciled the implemented repository-root architecture, maintainer-only artifact testing, conservative per-Skill portability inventory, and schema-governed Workspace publication handoff. |
| 14 | 2026-08-10 | Recorded governed Plugin behavior as the non-regressing baseline for duplicate Skill reconciliation. |
| 15 | 2026-08-10 | Recorded local acceptance evidence and retained external Workspace checks as explicit release blockers. |
| 16 | 2026-08-10 | Reopened to reconcile invocation metadata and fresh-task engineering decision routing; selected confirmed-Spec resume semantics for exact `開始執行`. |
| 17 | 2026-08-10 | Implemented and locally verified invocation metadata enforcement, exact fresh-task resume routing, explicit repository onboarding, and Plugin-only router authority. |
| 18 | 2026-08-10 | Reopened before clarification: User changed the target from a private managed Workspace listing to one personal account shared across ChatGPT Work web and Codex Desktop. |
| 19 | 2026-08-10 | Selected independent per-surface installation from one public Git repository, a generated same-repository publication branch, and the `marketplace-release` reference. |
| 20 | 2026-08-10 | Confirmed the personal Git Marketplace design and authorized implementation. |
| 21 | 2026-08-10 | Implemented and locally verified deterministic Marketplace publication, fail-closed release evidence, stale-tag protection, architecture governance, documentation, and two-axis review while retaining external cross-surface acceptance blockers. |
| 22 | 2026-08-11 | Reopened before clarification: Official product-surface evidence disproves personal Git Marketplace installation on ChatGPT web; user selected Codex Desktop/CLI-only distribution and requested a 0.7.x rollback. |
| 23 | 2026-08-11 | Selected a targeted rollback: retain single-source governance, narrow the private Git Marketplace to Codex Desktop/CLI, remove unsupported ChatGPT-web gates, and release as 0.7.2. |
| 24 | 2026-08-11 | Reopened before clarification: User selected restoration of the 0.7.1 local one-click installer instead of Git Marketplace installation. |
| 25 | 2026-08-11 | Restored the local one-click installer as the primary Codex Desktop/CLI path while preserving single-source assembly and optional Codex Marketplace output. |
| 26 | 2026-08-11 | Reconciled Codex-only post-install acceptance, assembly-owned cache refresh, isolated exact-tree installer fixtures, and verified 0.7.2 delivery evidence. |
| 27 | 2026-08-11 | Recorded explicit authorization and verified deletion of the failed remote 0.8.0 tag, superseding DEC-020's disproven external-state assumption. |
| 28 | 2026-08-13 | Recorded separate authorization and verified deletion of the concurrently created 0.8.1 tag, retaining remote history while resolving the current version to 0.7.2. |
| 29 | 2026-08-13 | Normalized textual checkout newlines in production fingerprints after Linux CI exposed Windows CRLF drift; added portable regression evidence without changing the selected release contract. |
| 30 | 2026-08-13 | Reopened before clarification: User selected focused repair for the no-argument one-click installer regression and an immutable 0.7.3 patch release. |
| 31 | 2026-08-13 | Recorded RED/GREEN coverage for automatic Python discovery and Codex Desktop runtime precedence, plus successful real no-argument installation of local Plugin 0.7.3. |
| 35 | 2026-08-14 | Implemented the selected verified PATH-first Codex resolution contract with side-effect-free probing, Desktop fallback, launcher-level Python discovery, and actionable missing-runtime fixtures. |
| 36 | 2026-08-14 | Reconciled complete local validation and real installation evidence; retained GitHub Actions and immutable remote tag creation as post-push evidence. |
| 37 | 2026-08-14 | Reopened before clarification: 另一台電腦的 PATH python 不支援 f-string；安裝器應在組裝前驗證 Python 3.11+，並決定是否自動尋找相容 runtime。 |
| 38 | 2026-08-14 | Selected automatic compatible-Python discovery, absolute interpreter normalization, same-interpreter execution, and a new immutable patch release. |
| 39 | 2026-08-14 | Implemented Python 3.11+ preflight and Windows Launcher fallback, published local version metadata as 0.7.4, and recorded passing installer, distribution, Plugin, and architecture evidence. |
| 40 | 2026-08-14 | Reopened before clarification: Clarify cross-account Windows ACL recovery after a Codex sandbox-owned dist artifact blocked local Plugin assembly and hid the installed-version view. |
| 41 | 2026-08-14 | Selected bounded automatic ACL recovery for only the exact ignored Plugin artifact, with ordinary recovery before UAC, unsafe-target refusal, and post-repair revalidation. |
| 42 | 2026-08-14 | Implemented bounded exact-target Windows ACL recovery, sandbox-staging ACL inheritance, public-installer failure isolation, and passing 0.7.4 local validation evidence. |
| 43 | 2026-08-14 | Corrected recursive partial-recovery validation, moved Windows ACL and Python process bindings behind L3+ adapters, and retained real cross-principal/UI confirmation as pending user acceptance. |
| 44 | 2026-08-14 | Added effective existing-entry replaceability checks and reparse-safe breadth-first ACL repair after final Spec and Standards review findings. |
