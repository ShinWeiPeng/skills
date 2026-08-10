---
spec_version: 1
spec_id: SPEC-0013
revision: 21
status: confirmed
change_set: shared-skill-distribution
---

# Shared Skill Distribution

## Problem

The repository currently has a Claude plugin over the promoted source buckets and a separate Codex plugin containing 212 tracked files under its vendored and overlaid skill tree. ChatGPT web and local Codex therefore do not share one installation state, and skill content can diverge.

## Solution

Treat root `skills/engineering` and `skills/productivity` as the only editable Skill source. Move the six existing Codex-only governance and integration Skills into engineering. Keep only the Plugin manifest, versioning, release scripts, contract tests, and validation infrastructure under `plugins/governed-engineering-skills`; move formal architecture governance to repository root and remove tracked Plugin Skill copies. Deterministically assemble a complete ignored artifact at `dist/governed-engineering-skills`, copying the tracked shell and generating its `skills/` tree from the two promoted buckets.

After the existing stable-release gates pass, generate an installable Marketplace tree from that exact artifact and publish only the generated catalog and complete Plugin package to the `marketplace-release` branch of `https://github.com/ShinWeiPeng/skills.git`. The `main` branch remains the only editable source, `plugin-release/main` remains the Version Pull Request branch, and `marketplace-release` is a generated consumer branch that must never be edited manually.

ChatGPT Work web and Codex Desktop each add and install the same Git Marketplace independently. Both use the same repository URL, `marketplace-release` Git reference, Marketplace catalog, Plugin name, semantic version, and content fingerprint. Automatic synchronization of installation or enablement state is outside the contract. The retained local Marketplace remains maintainer-only development tooling and is not a supported user installation path.

## User Stories

- As the maintainer, I want to edit each shared skill in one authoritative root location.
- As a contributor, I want Skill PRs to avoid duplicate generated-file diffs.
- As the owner of one personal account, I want independently installed ChatGPT Work web and Codex Desktop surfaces to consume the same Git-backed Plugin release.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Root `skills/engineering` and `skills/productivity` MUST be the authoritative editable source for all shared skills. |
| REQ-002 | Plugin skill trees MUST be generated reproducibly, and validation MUST reject source or inventory drift. |
| REQ-003 | One Git-backed Plugin release MUST provide the selected Skill set to independently installed ChatGPT Work web and Codex Desktop surfaces for the same personal account. |
| REQ-004 | The shared plugin MUST include both promoted buckets and MUST exclude `misc`, `personal`, `in-progress`, and `deprecated`. |
| REQ-005 | The six governance and integration skills MUST move into root `skills/engineering` and follow promoted documentation and routing rules. |
| REQ-006 | The tracked plugin shell MUST remain directly maintainable while the complete assembled artifact and generated skill tree remain untracked under `dist/`. |
| REQ-007 | Installation, validation, and release commands MUST assemble the artifact before consuming it and MUST NOT install from an incomplete shell. |
| REQ-008 | Repository guidance, manifests, inventories, ADRs, and release documentation MUST describe the unified source and generated-artifact lifecycle. |
| REQ-009 | Formal architecture governance MUST cover every moved governance/integration production source without forbidden parent traversal or an ungoverned production gap. |
| REQ-010 | The repository MUST distinguish the maintainer-only local Marketplace from the personal Git Marketplace and MUST NOT describe a local filesystem source as web-accessible. |
| REQ-011 | Local validation and the `marketplace-release` publication MUST consume the same assembled Plugin name, version, inventory, and content fingerprint. |
| REQ-012 | The release flow MUST generate and validate a personal Marketplace publication record containing repository URL, Git reference, catalog and Plugin paths, source tag/commit, version, fingerprint, installation steps, rollback reference, and evidence checklist. |
| REQ-013 | Cross-product compatibility validation MUST identify host-dependent Skills or resources and MUST prove representative engineering and productivity workflows on both ChatGPT Work web and Codex before release acceptance. |

| REQ-014 | The repository MUST remove the one-click local installer, desktop launcher, installer-specific tests, and user-facing local-install instructions while retaining local Marketplace metadata for manual maintainer testing. |
| REQ-015 | User-facing installation guidance MUST identify the personal Git Marketplace on `marketplace-release` as the supported installation source and MUST explain that each surface installs it independently. |
| REQ-016 | Formal architecture MUST remove the `local_install_adapter`; manual developer Marketplace testing remains development tooling rather than a supported production installation module. |
| REQ-017 | When a promoted root Skill and the previously installed Codex Plugin Skill shared a name but differed in behavior, the unified root source MUST preserve the governed Codex workflow behavior so unification does not silently regress existing Codex use. |
| REQ-018 | Invocation metadata MUST have one deterministic two-harness contract: user-invoked Skills carry both Claude's `disable-model-invocation: true` and Codex's `policy.allow_implicit_invocation: false`; model-invoked Skills omit both restrictions and MUST NOT spell the default as `allow_implicit_invocation: true`. |
| REQ-019 | In a fresh task, the exact authorization phrase `開始執行`, optionally accompanied by an explicit canonical Spec path, MUST be classified as confirmed-Spec resume intent rather than a new generic modification request. One confirmed candidate proceeds to verification, multiple candidates require exactly one user selection, and no candidate fails closed with a specific remediation. |
| REQ-020 | The installed Plugin MUST remain the self-contained authority for automatic engineering routing. Repository `AGENTS.md` guidance MUST directly instruct Codex to read and follow the repository rules instead of relying on a bare filename pointer, but router correctness MUST NOT depend on `AGENTS.md`. |
| REQ-021 | Every engineering request MAY enter the model-invoked `ask-matt` router, but only repository-modifying requests or unresolved change-set decisions MUST enter `grilling`; factual explanation, diagnosis, and review remain read-only until modification intent is present. |
| REQ-022 | Personal cross-surface sharing MUST mean that ChatGPT Work web and Codex Desktop install the same Git-backed Plugin source and release identity independently; automatic synchronization of installation state is not required. |
| REQ-023 | The complete installable Marketplace tree MUST be generated from `main` into a dedicated publication branch in this repository after stable-release validation; the publication branch MUST NOT become an editable Skill source. |
| REQ-024 | The dedicated personal Marketplace publication branch MUST be named `marketplace-release` and MUST remain distinct from the existing Version Pull Request branch `plugin-release/main`. |

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

## Architecture Impact

- **Affected level and module:** retain the L0 `plugin_assembly_composition` owner and revise its purpose from Workspace handoff generation to personal Git Marketplace publication-tree generation and validation.
- **Technical release authority:** retain L3+ `plugin_release_governance_technical`; a publication candidate is admitted only after its stable SemVer, immutable tag intent, assembled inventory, and fingerprint pass existing release governance.
- **Ports, Events, Types, and State:** add architecture-description records for the synchronous distribution, integration, and release-validation outcomes plus the two existing JSON Schema contracts. These are CI/tooling contracts, not installed Plugin runtime ports; no mutable State Object, runtime dependency edge, execution unit, queue, callback, or public Plugin runtime contract is introduced.
- **Source and Description Views:** replace Workspace-specific validator and distribution-record paths in `architecture/manifest.yaml`; update `plugin_assembly_composition` paths, public symbols, side effects, invariants, System page, Parent page, and architecture overview; regenerate all marker-owned views deterministically.
- **Compatibility boundary:** preserve Plugin ID, bundled Skill paths, invocation policy, stable SemVer authority, immutable release tags, and root-only editable Skill ownership. Replace only the user distribution channel and its evidence schema.
- **ADR:** add `ADR-0014-personal-git-marketplace-publication.md` recording the selected same-repository generated branch and the rejected separate-repository and managed-Workspace alternatives. The user's selections in DISC-011 through DISC-013 are the human decision evidence; no architecture-rule exception is requested.

## Flow Execution Impact

- **As-is candidate:** local validation produces an ignored artifact, then release acceptance waits for a managed Workspace handoff and administrator evidence. This cannot satisfy the personal-account target and is rejected by functional admission.
- **Selected candidate:** stable-release validation assembles one artifact, builds a deterministic Marketplace tree, verifies catalog-relative paths and identity, then atomically replaces `marketplace-release`. ChatGPT Work web and Codex Desktop independently fetch that same branch and install the same Plugin release.
- **Rejected candidate:** publishing the generated tree to a second repository also satisfies functional delivery, but adds another repository authority, credential boundary, synchronization step, rollback reference, and deployment artifact without a selected access-isolation requirement.
- **Execution assurance:** `estimated`. The CI flow is best-effort and has no latency, throughput, memory, power, or real-time product budget. No new thread, queue, retry loop, serialization boundary, or target runtime is introduced. Functional publication and rollback evidence, not performance measurement, determines acceptance.
- **Failure policy:** validation, fingerprint mismatch, stale source tag, incomplete sparse tree, non-fast-forward publication race, or missing credentials blocks publication and leaves the previous `marketplace-release` commit available. A failed user installation is recorded separately from a failed release candidate.

## Evolution Impact

- **Add or modify a Skill:** change only the root promoted bucket; assembly, catalog generation, tests, and the next stable publication carry it to both surfaces.
- **Add an adapter or bundled resource:** update the tracked Plugin shell or authoritative root Skill resource, then validate its generated inventory and relative references before publication.
- **Add another consumer surface:** reuse the same immutable release identity when the surface supports repo Marketplaces; add surface-specific installation evidence without creating another editable Skill tree.
- **Rollback:** repoint `marketplace-release` to the previously validated generated commit through an explicit workflow input, while retaining immutable version tags and leaving `main` untouched.
- **Platform variant:** no installed-runtime platform mapping changes; surface differences remain in the compatibility inventory and cross-surface evidence.

## Algorithm Impact

| Product feature | Owner | Screening result | Record |
|---|---|---|---|
| Plugin artifact assembly | `plugin_assembly_composition` | Not applicable: existing deterministic inclusion, normalization, inventory, and SHA-256 identity rules do not rank, tune, estimate, or select among data-dependent results. | Existing inventory entry remains sufficient. |
| Marketplace publication-tree generation | `plugin_assembly_composition` | Not applicable: exact path mapping and byte-for-byte identity checks have one prescribed result and no heuristic, statistical, scheduling, optimization, or fallback method choice. | No new `ALG-####` required. |

## Recommended Improvements

### Improvement 1: Generate a remote personal Marketplace tree

- **Change:** add a deterministic staging operation that writes `.agents/plugins/marketplace.json` plus the complete `plugins/governed-engineering-skills` tree from the validated artifact, with the catalog source set to `./plugins/governed-engineering-skills`.
- **Expected impact:** both product surfaces can resolve one web-accessible package instead of depending on a Windows path or managed Workspace listing.
- **Benefits:** one editable source, one release identity, no administrator publication dependency, and auditable branch contents.
- **Costs and disadvantages:** generated branch storage, workflow logic, and separate first-time installation on each surface.
- **Risks:** stale generated content, incorrect sparse paths, or accidental branch editing.
- **Mitigation:** exact inventory/fingerprint comparison, protected generated branch, clean temporary-repository tests, and fail-closed publication.

### Improvement 2: Replace Workspace release evidence with personal cross-surface evidence

- **Change:** replace Workspace listing/admin schemas and validation with repository/ref/path identity, independent installation records, and four representative invocation records.
- **Expected impact:** release acceptance measures the user's actual goal instead of an unavailable managed-Workspace workflow.
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

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001, REQ-005 | Editing any shared skill requires changing only its root source directory; all six governance/integration skills exist under root engineering and no tracked plugin skill copy remains. | Source inventory, tracked-file inspection, promoted README and manifest checks. | PASS — 28 root Skills; no Plugin-shell Skill tree. |
| AC-002 | REQ-002 | Two clean assembly runs produce byte-equivalent skill inventories, and validation rejects missing, extra, or modified generated skills. | Automated deterministic-assembly and bounded drift-fixture tests. | PASS — deterministic and missing/extra/modified fixtures pass. |
| AC-003 | REQ-003 | One validated Git-backed release can be installed independently by the same personal account on ChatGPT Work web and Codex Desktop and exposes representative explicit and implicit Skill invocations. | Install the same `marketplace-release` candidate on both surfaces and record matching identity plus invocation results. | Expected external evidence pending publication and two-surface installation. |
| AC-004 | REQ-004 | Generated inventory contains every promoted engineering and productivity Skill and no non-promoted Skill. | Compare generated paths against both promoted bucket inventories and negative-list fixtures. | PASS — exact 28-Skill inventory comparison. |
| AC-005 | REQ-005, REQ-008 | Promoted READMEs, top-level README, Claude manifest, router references, docs, and replacement ADR consistently describe all 28 root-source Skills. | Manifest and documentation inventory tests plus repository-wide stale-contract search. | PASS — docs, manifests, invocation metadata, and grouping checks pass. |
| AC-006 | REQ-006 | The tracked shell retains manifest and release infrastructure, while `dist/governed-engineering-skills` stays ignored and reproducible from a clean checkout. | Git-status assertions before and after clean assembly plus plugin artifact validation. | PASS — Git status is unchanged and Plugin ingestion passes. |
| AC-007 | REQ-007 | Every supported install, validation, and release entrypoint assembles first or fails clearly when the artifact is absent or stale. | Entrypoint tests covering clean, absent, current, and stale artifact states. | PASS — state fixtures and job-local release ordering pass. |
| AC-008 | REQ-008 | No active document states that the native Codex/OpenAI plugin is deferred or that packaged Skills are maintained as an independent vendored source. | Repository-wide contract search and documented-command verification. | PASS — active contracts describe root ownership and assembly. |
| AC-009 | REQ-009 | The selected architecture root and source sets validate every governed Python production path after the Skill migration, with no parent traversal and no missing moved source. | Architecture design/development gates and source-set inventory validation. | PASS — both architecture release gates are VERIFIED. |
| AC-010 | REQ-010, REQ-012 | Maintainer documentation identifies local testing as development-only, while the personal publication record validates the Git repository, `marketplace-release` reference, catalog and Plugin paths, release identity, rollback, and user-owned installation steps. | Rendered documentation review, Marketplace schema/path validation, and publication-record schema validation. | PASS locally — both schemas reject malformed identities; user and maintainer channels are distinct in README and distribution guidance. |
| AC-011 | REQ-011 | The locally tested artifact and `marketplace-release` publication candidate have the same Plugin name, semantic version, complete file inventory, and SHA-256 content fingerprint. | Deterministic assembly, manifest validation, inventory comparison, and checksum comparison. | PASS locally — Plugin 0.7.1, 252 files, `sha256:b7b253e42eaa92029652ad3512a60d511474d16dd69a0496b01556cd5c40ed6a`; remote branch comparison awaits publication. |
| AC-012 | REQ-003, REQ-013 | The personal Git Marketplace is visible on ChatGPT Work web and Codex Desktop, and a new chat/task can invoke one representative engineering Skill and one representative productivity Skill on each surface. | Two independent personal-account installations followed by a four-case cross-surface invocation checklist with screenshots or exported task evidence and matching release identity. | Expected external evidence pending generated-branch publication and four auditable invocation records. |
| AC-013 | REQ-013 | Every packaged Skill is classified as cross-product, Codex-only, or blocked with a specific reason; release is blocked if a Skill advertised as shared depends on an unavailable local path, executable, tool, or permission on ChatGPT Work web. | Static portability inventory plus representative negative fixtures and cross-surface tests. | PASS locally — conservative inventory and negative fixtures pass. |

| AC-014 | REQ-014, REQ-015 | The repository contains no one-click local installer, launcher, or installer-specific test, and no user-facing document advertises local installation; the retained local Marketplace manifest still passes schema and path validation for manual maintainer use. | Tracked-file inventory, stale-reference search, Marketplace validation, and rendered documentation review. | PASS — installer removed; maintainer Marketplace targets assembled artifact. |
| AC-015 | REQ-016 | The repository-root architecture contains no `local_install_adapter` module, entrypoint, public symbol, or generated Description View reference after migration. | Architecture manifest diff, deterministic rendering, and the single development/release architecture gate. | PASS — no local installer module remains. |
| AC-016 | REQ-017 | Existing governed router, spec, architecture, runtime-evidence, and review contracts remain present after duplicate Skill reconciliation, and all Plugin contract tests pass against the assembled root-derived artifact. | Assembled Plugin integration validation, invocation-policy checks, and Plugin contract suite. | PASS — integration validation and 157 Plugin contract tests pass. |
| AC-017 | REQ-018 | Every promoted source Skill and assembled Plugin Skill passes a classification matrix proving that manual restrictions are paired, automatic restrictions are omitted, redundant `true` policy is absent, and OpenAI assembly removes only Claude-specific frontmatter. | Source/artifact metadata matrix tests with positive and negative fixtures. | PASS — source/artifact matrix, all three invalid metadata fixtures, and body-content preservation fixture pass in `tests.test_shared_skill_distribution`. |
| AC-018 | REQ-019, REQ-021 | Fresh-task routing tests prove exact `開始執行` with one, many, or zero confirmed Specs; an explicit Spec path; negated or quoted phrases; ordinary read-only discussion; and a modifying request that must enter `grilling`. | Deterministic guided-router unit and integration tests asserting selected Skill, status, candidate evidence, and resume target. | PASS — exact phrase one/many/zero/path, specific zero-candidate remediation, exactly-one selection instruction, and negative phrase fixtures pass; the complete 161-test Plugin suite preserves read-only and modifying routes. |
| AC-019 | REQ-020 | `AGENTS.md` directly instructs Codex to load repository rules, while an assembled-Plugin test with no repository `AGENTS.md` still routes a modifying engineering request through `ask-matt` and the governed decision gate. | Repository instruction-content assertion plus isolated assembled-Plugin routing test. | PASS — repository instruction assertion and isolated assembled-Plugin modifying route pass without consumer `AGENTS.md`. |
| AC-020 | REQ-022 | The personal account can install the same Plugin release identity from the same Git Marketplace source independently in ChatGPT Work web and Codex Desktop; no assertion depends on automatic synchronization of installation state. | Two-surface installation record plus matching Plugin name, version, source reference, content fingerprint, and representative invocation evidence. | Expected evidence pending implementation and cross-surface testing. |
| AC-021 | REQ-023 | A validated stable release produces a dedicated-branch Marketplace tree containing `.agents/plugins/marketplace.json` and the complete `plugins/governed-engineering-skills` package, and regeneration from the same source tag is byte-equivalent. | CI publication fixture, clean-checkout assembly, branch-tree inventory, manifest/path validation, fingerprint comparison, and mutation rejection. | PASS locally — repeated candidates have identical Git tree IDs; unsafe output, mutation, stale fingerprint, stale tag, and branch-commit mismatch fail closed. Actual branch publication remains an external release action. |
| AC-022 | REQ-024 | Marketplace documentation, workflow fixtures, and user evidence consistently use `marketplace-release`, while version-governance fixtures continue to use `plugin-release/main` only for the Version Pull Request. | Repository-wide structured search and workflow contract tests. | PASS locally — structured search and release/version workflow contracts preserve the two distinct branch identities. |

## Alternatives Comparison

| Alternative | Observable result | Benefits | Costs and risks | Decision |
|---|---|---|---|---|
| Generated `marketplace-release` branch in this repository | Both surfaces install from one repository/ref and matching Plugin identity. | One repository authority; no second editable tree or extra credential boundary. | Generated branch must be protected and publication tested. | Selected. |
| Separate generated distribution repository | Both surfaces install from a clean consumer-only repository. | Stronger repository/access isolation. | Extra repository, credentials, rollback reference, and synchronization state. | Rejected because no isolation requirement exists. |
| Commit the assembled Plugin tree on `main` | The current default branch becomes directly installable. | Simplest consumer URL. | Duplicates generated Skills in normal source history and reintroduces source drift. | Rejected by root-only ownership and ignored-artifact requirements. |
| Managed private Workspace listing | Administrator publishes once for a managed workspace. | Central workspace policy and listing. | Does not match the selected personal-account scope and requires unavailable admin/listing evidence. | Superseded. |

## Implementation Order

1. Replace Workspace-specific schemas, validators, documentation, and architecture declarations with personal Marketplace publication contracts while preserving stable IDs and release identity rules.
2. Add deterministic Marketplace-tree assembly and temp-repository contract tests before changing the release workflow.
3. Extend the release workflow to build and validate the generated tree, then publish `marketplace-release` only after every local release gate passes.
4. Regenerate architecture Description Views, run the complete local validation matrix, and confirm the generated branch tree from a clean checkout.
5. Add the Git Marketplace independently on ChatGPT Work web and Codex Desktop using repository `https://github.com/ShinWeiPeng/skills.git`, ref `marketplace-release`, and sparse paths `.agents/plugins` plus `plugins/governed-engineering-skills`.
6. Record matching identity and four representative invocation results; only then accept the cross-surface release.

## Validation and Acceptance Gates

| Gate | Validation method and reproducible step | Expected observable output | Pass condition | Evidence format |
|---|---|---|---|---|
| Validation Enablement | Assemble into a temporary directory, generate a Marketplace tree, import it into a temporary Git repository, and run positive plus missing-path, traversal, stale-fingerprint, wrong-ref, and mutation fixtures. | Deterministic tree and explicit fail-closed errors without contacting the production branch. | Positive fixture passes twice byte-equivalently; every negative fixture fails for its intended reason. | Test log with command, exit code, generated inventory, tree hash, and fixture verdicts. |
| Per-change Development Validation | Run `python -m unittest tests.test_shared_skill_distribution -v`, Plugin contract tests, distribution validation, artifact validation, schema checks, documentation/link checks, and a clean Git-status assertion. | All focused tests pass; no generated tree appears as an editable `main` source. | Every command exits `0`, expected negative fixtures fail closed, and Git status changes only in intended tracked files. | CI logs plus hashed test/result artifacts. |
| Final Cross-surface Acceptance | Install the same branch independently on ChatGPT Work web and Codex Desktop; in a fresh chat/task invoke one engineering and one productivity representative on each surface. | Both installations report the same Plugin name, version, repository/ref, branch commit, and fingerprint; all four invocations follow the selected Skill. | Four invocation records pass and every identity field matches the current publication candidate. | Repository-contained Markdown/JSON records with screenshot or exported-task file paths and SHA-256 hashes. |
| Release Acceptance | Rebuild the release composition; run `python tools/architecture/architecture_cli.py gate --phase release --manifest architecture/manifest.yaml --adoption architecture/adoption.yaml --baseline architecture/baseline.yaml`, deterministic render comparison, full regression, version checks, publication-record validation, and generated-branch tree comparison before branch update. | Release gates pass; no Workspace-admin/listing contract remains active; `marketplace-release` contains only the expected catalog, Plugin tree, and publication metadata bound to the stable source tag. | Every required command exits `0`; architecture and generated views are current; branch commit identity equals the validated candidate; previous branch commit remains a documented rollback target. | Separate validation-build and release/publication evidence with command, exit code, minimal raw output, commit IDs, tag, fingerprint, and PASS/FAIL/BLOCKED verdict. |

No physical-device, scheduler, OS-native trace, real-time, performance, or resource validation applies. The external product-surface checks are necessary because repository tests cannot prove that the signed-in ChatGPT account actually lists, installs, and invokes the Plugin on either product surface.

## Relationships

| Source | Relation | Target | Rationale |
|---|---|---|---|
| DEC-005 | refines | SPEC-0011 | Extend portable plugin governance with a single root Skill source and assembled cross-product artifact. |
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

## Out of Scope

- Submitting the Plugin to OpenAI's universal public Plugin Directory.
- Shipping `misc`, `personal`, `in-progress`, or `deprecated` skills.
- Automatically installing or enabling the Plugin on either product surface.
- Treating the local Marketplace or local Plugin cache as a synchronization mechanism for ChatGPT Work web.

- Supporting one-click or user-facing local Plugin installation.
- Requiring installation or enablement state to synchronize automatically between ChatGPT Work web and Codex Desktop.
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

## Routing/Gates

- Grilling: PASS; personal cross-surface semantics, same-repository publication topology, and the `marketplace-release` branch identity are selected.
- Architecture proposal and implementation: PASS; `plugin_assembly_composition` remains the owner, JSON Schema types and validation outcomes are cataloged, generated Description Views are current, and development/release gates return `PASS: VERIFIED`.
- TDD: PASS; RED recorded before Marketplace generation/evidence implementation, followed by deterministic Git-tree, unsafe-output, mutation, malformed-schema, stale-tag, and branch-identity GREEN fixtures.
- Development and release validation: PASS locally; distribution assembly/validation, 29 shared-distribution tests, 161 Plugin contract tests, version governance, and both architecture gates exit `0`.
- Cross-surface acceptance: BLOCKED until `marketplace-release` exists and the four personal-account invocation records are captured.
- Spec and Standards review: PASS; final independent reviews report no uncovered requirement, scope creep, documented-standard violation, or actionable baseline smell.

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
| 12 | 2026-08-10 | Removed the one-click local installer from the proposal while retaining manual maintainer Marketplace testing. |
| 13 | 2026-08-10 | Reconciled the implemented repository-root architecture, maintainer-only artifact testing, conservative per-Skill portability inventory, and schema-governed Workspace publication handoff. |
| 14 | 2026-08-10 | Recorded governed Plugin behavior as the non-regressing baseline for duplicate Skill reconciliation. |
| 15 | 2026-08-10 | Recorded local acceptance evidence and retained external Workspace checks as explicit release blockers. |
| 16 | 2026-08-10 | Reopened to reconcile invocation metadata and fresh-task engineering decision routing; selected confirmed-Spec resume semantics for exact `開始執行`. |
| 17 | 2026-08-10 | Implemented and locally verified invocation metadata enforcement, exact fresh-task resume routing, explicit repository onboarding, and Plugin-only router authority. |
| 10 | 2026-08-10 | Reopened to separate Codex-local testing from private Workspace publication, add cross-product acceptance requirements, and normalize legacy answer markers. |
| 18 | 2026-08-10 | Reopened before clarification: User changed the target from a private managed Workspace listing to one personal account shared across ChatGPT Work web and Codex Desktop. |
| 19 | 2026-08-10 | Selected independent per-surface installation from one public Git repository, a generated same-repository publication branch, and the `marketplace-release` reference. |
| 20 | 2026-08-10 | Confirmed the personal Git Marketplace design and authorized implementation. |
| 21 | 2026-08-10 | Implemented and locally verified deterministic Marketplace publication, fail-closed release evidence, stale-tag protection, architecture governance, documentation, and two-axis review while retaining external cross-surface acceptance blockers. |
