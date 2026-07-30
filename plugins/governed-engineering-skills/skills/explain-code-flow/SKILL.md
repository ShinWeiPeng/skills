---
name: explain-code-flow
description: Guide developers through an unfamiliar codebase using governed System and L0/L1 Parent views, developer reading routes, task indexes, end-to-end flows, and progressively deeper code explanations. Use when introducing a project or main entry point; navigating architecture modules, ports, events, source paths, entrypoints, or public symbols; tracing hardware, API, UI, file, database, message, event, timer, or scheduler data; selecting a Parent or Flow ID; or explaining a module, class, function, method, call chain, state change, side effect, error path, or code region. Require supported formal architecture governance for project-wide System and Parent guidance, and coordinate with $govern-modular-event-architecture when it is missing, stale, invalid, or unsupported.
---

# Governed iterative code-flow guidance

Guide a developer from the governed architecture to the implementation, then expand only the selected scope. Default to Traditional Chinese, preserve identifiers and technical terms, and assume the reader can program but does not know the project.

Treat `architecture/manifest.yaml` as the only editable architecture source of truth. Treat `architecture/ARCHITECTURE.md` and `architecture/generated/*.md` as derived views. Never create, edit, migrate, render, or approve governance artifacts under this skill; route that work to `$govern-modular-event-architecture`.

## Distinguish the two level systems

Never use architecture levels and reading levels interchangeably.

- **Architecture levels `L0`–`L3+`:** semantic module responsibility defined by governance.
- **Reading levels `Level 0`–`Level 3`:** depth of the current explanation.

| Reading level | Trigger | Result |
|---|---|---|
| Level 0 - System | Introduce the project, select the project root, or select `main` or another composition entry without explicitly requesting only that function | Produce the governed System view and developer navigation |
| Level 1 - Parent or Flow | Select an L0/L1 Parent ID, a Flow ID, or one end-to-end behavior | Produce the selected Parent view or expand the selected Flow |
| Level 2 - Module or symbol | Select a module, class, function, method, entrypoint, or public symbol | Explain its contract, mechanism, callers, dependencies, and architecture role |
| Level 3 - Code region | Select statements, branches, or a narrow implementation region | Explain control flow and data or state changes |

Expand one reading level per follow-up unless the user explicitly requests another depth. Preserve Parent IDs, Flow IDs, breadcrumbs, and coverage across turns.

## Apply the formal-governance gate

Apply this gate only to Level 0 System requests and Level 1 Parent requests. Do not apply it to a Flow, module, symbol, function, method, or code-region request.

### Check the project

Before producing a System or Parent view:

1. Locate `architecture/manifest.yaml` from the project root.
2. Read both `standard_version` and `schema_version`.
3. Match the pair against the supported capability matrix below.
4. Invoke `$govern-modular-event-architecture`, read its required schema and Description View references, and run the project-local checker in non-mutating validation mode.
5. Run the project-local deterministic renderer with `--check`. Require the checker and renderer to exit `0`; treat MUST violations, stale or missing generated views, and tool/configuration errors as blocking.
6. After governance validation passes, require `architecture/ARCHITECTURE.md`, `architecture/generated/system.md`, every renderer-owned L0/L1 Parent page, and every renderer-owned Execution page selected by the validated project to exist and be current. Let the governance checker and renderer own the expected-page inventory; do not independently reimplement that inventory from manifest fields.
7. Read the validated generated System or Parent view as the formal architecture input. Do not reinterpret the complete manifest schema or independently regenerate a competing formal view in this skill.
8. Verify implemented module paths, entrypoints, and public symbols against project-owned source. Run applicable governance language analyzers; C/C++ consistency requires complete AST evidence.

Do not claim a formal System or Parent view is ready unless every blocking check passes.

### Enforce the capability matrix

| Standard | Schema | Local code explanation | Formal System/Parent guidance |
|---|---|---|---|
| `2.0.2` | `2.0.2` | Supported | Supported after governance checker, deterministic renderer, generated-view, and applicable language-analyzer validation passes |
| Any other pair, including `1.x` | Any other pair | Supported only as source-level analysis with an architecture-context limitation | Block as unsupported by this explanation skill; do not conclude that the project itself is invalid |

Reject mismatched Standard/Schema pairs. Do not guess the semantics of a newer schema, ignore unknown fields, or present best-effort output as a formal view.

When `$govern-modular-event-architecture` adds or removes a supported schema version, require the same change to update this matrix, generated-view consumption contract, output contract, fixtures, and cross-skill forward tests. Do not declare a version supported until both governance validation and this skill's tests pass.

Distinguish capability from project validity:

- An absent, legacy, or unknown version is `explanation tool unsupported`; it is not evidence that the project itself is invalid.
- A mismatched Standard/Schema pair is an invalid governance configuration.
- A supported `2.0.2` project whose checker or renderer fails is invalid, stale, or blocked according to the reported diagnostic.
- A supported `2.0.2` project whose governance validation passes but whose applicable language analyzer lacks complete evidence retains valid formal governance; label implementation consistency incomplete and do not claim source conformance.

### Route a blocked request through governance

If the manifest is absent, legacy, unsupported, invalid, or stale:

1. Stop the requested formal System or Parent guidance. Do not substitute an inferred formal view.
2. State the exact blocking condition and observed version pair when available.
3. Invoke `$govern-modular-event-architecture` and follow its mode, clarification, migration, approval, rendering, baseline, ADR, and validation requirements.
4. For an existing project, map the actual architecture before proposing the governed state. Never present a desired design as the current implementation.
5. Resume the original Explain request only after the manifest, generated views, generic checker, and applicable language analyzer all report `PASS`.
6. Re-read the validated generated views and source before producing guidance; do not reuse an unconfirmed draft as formal architecture data.

Do not create a permanent discovery or handoff file. A confirmed bootstrap or migration spec may exist only as a governance workflow input; after adoption, the manifest remains the single shared format.

## Permit local explanation without formal governance

For a Flow, module, symbol, function, method, or code-region request, continue with static analysis even when the gate would fail.

At the beginning of the response, copy one of these labels verbatim. Treat the labels as output API strings; do not translate, abbreviate, or replace them with synonyms:

- `**正式架構脈絡：可用** — Standard/Schema: <validated pair>`; or
- `**正式架構脈絡：受限** — <missing, legacy, unsupported, invalid, or stale reason>`.

When context is limited, do not assign formal L0–L3+ ownership, Port/Event contracts, Parent relationships, or claim complete System coverage. Use source-derived terms and label architecture interpretations as `推論`.

## Establish implementation evidence

Use static inspection by default.

1. Run `rg --files` to inventory source, headers, manifests, build files, configuration, generated code, documentation, and tests.
2. Use `rg` to find composition roots, entrypoints, route and command registration, handlers, callbacks, events, tasks, schedulers, ports, symbols, configuration, and tests.
3. Use an available LSP, AST index, call hierarchy, or governance language analyzer to strengthen symbol and indirect-call evidence; keep `rg` as the portable baseline.
4. Cross-check validated generated-view claims and their declared program anchors against registration code, configuration, tests, and actual definitions.
5. Trace project-owned code far enough to establish sources, transformations, state, side effects, errors, and sinks.
6. Stop at framework, library, generated-code, driver, and external-service boundaries. Explain the exchanged data, purpose, and expected result without expanding third-party internals.
7. Do not modify source, execute the application, operate hardware, or invoke external systems merely to explain code. Ask before using dynamic evidence.
8. Record reflection, dependency injection, configuration-selected implementations, dynamic registration, callbacks, and unresolved dispatch as uncertainty.

Label important conclusions:

- `已確認`: directly supported by validated governance data and/or inspected implementation.
- `推論`: a reasoned interpretation not directly established.
- `待確認`: static evidence is missing, ambiguous, runtime-dependent, or unsupported by available analyzers.

Attach absolute clickable file-and-line links to architecture and implementation claims. Resolve source paths to representative implementation lines, entrypoints to definitions, and public symbols to declarations. If a symbol cannot be verified, link only the existing path and label `待確認／symbol 未驗證`; never invent a line number.

## Produce Level 0 in the fixed order

Use the validated generated System view and implementation evidence. Treat the following headings and table headers as a literal output contract. Copy them verbatim, in this order, and do not replace words such as `定位`, `架構地圖`, `導覽`, `完整資料流索引`, `開發任務索引`, `Coverage ledger`, `風險`, or `選項` with synonyms.

```markdown
## 1. 專案定位
## 2. 架構地圖
## 3. 開發者閱讀導覽
## 4. 完整資料流索引
## 5. 開發任務索引
## 6. Coverage ledger
## 7. 架構與資料流風險
## 8. 下一層導讀選項
```

### 1. 專案定位

State purpose, runtime, deployment form, system boundary, external actors/interfaces, composition roots, and primary entrypoints.

### 2. 架構地圖

Include:

- a Mermaid System diagram containing all declared modules, architecture levels, and Parent relationships;
- a module summary with purpose, role, Parent, implementation status, and source path;
- a complete index of every L0/L1 Parent with purpose, direct children, owned Ports/Events, owned Flows, program anchors, and a selectable next command;
- a concise formal-source boundary summary covering production, generated-production, development, derived-documentation, and build-output classifications that are relevant to the visible architecture;
- the Type ownership, State ownership, and cross-module Boundary Mapping information exposed by the validated generated System view;
- declared-versus-implemented differences without silently correcting the manifest.

Do not fully expand every Parent in Level 0. Produce the complete index and expand a Parent only after the user selects it.

### 3. 開發者閱讀導覽

Build the route from System boundary and composition through L0/L1 orchestration, principal Flows, L2 components, L3+ adapters, state, errors, and tests.

Use exactly:

| 階段 | 閱讀目標 | 檔案／符號 | 為何現在讀 | 閱讀重點 | 完成判準 | 下一站 |
|---|---|---|---|---|---|---|

Make every stage actionable. Link files and symbols, state why the order matters, and provide an observable understanding checkpoint rather than vague advice such as "read this file."

### 4. 完整資料流索引

List every governed end-to-end Flow and any relevant coverage gap.

For schema 2.0.2, include the inherited execution contract for each Flow: Workload IDs, timing class, Execution Profile/Unit/Channel boundaries, Data Access and Microarchitecture Profile links, and platform variant. Do not infer missing execution mappings from Module boundaries.

| Flow ID | Owner | Trigger | 主要路徑 | 成功結果 | Error branches | 程式錨點 | 可深入節點 |
|---|---|---|---|---|---|---|---|

Do not invent additional formal Flow IDs for private L2 algorithms. Identify source-level subflows as non-governed implementation details.

### 5. 開發任務索引

Map common understanding and change tasks to governed architecture and implementation evidence.

Use exactly:

| 開發任務 | 相關 Flow ID | 從哪裡開始 | 關鍵檔案／符號 | 設定／資料 | 相關測試 | 修改風險 |
|---|---|---|---|---|---|---|

Derive tasks from external interfaces, public commands/events, owned Flows, configuration, tests, and observable system responsibilities. Do not imply that locating code authorizes changing it.

### 6. Coverage ledger

Use:

| 範圍 | 狀態 | 已檢查證據 | 缺口或限制 |
|---|---|---|---|

Allowed states are `已分析`, `待分析`, and `無法確認`. Include manifest/source consistency, generated-view freshness, symbol verification, dynamic dispatch, configuration variants, and uninspected source areas. Do not call coverage complete while a relevant area remains unchecked.

### 7. 架構與資料流風險

Report evidence-backed issues visible at this depth: manifest/source drift, hidden state, unclear ownership, blocking work in async or interrupt contexts, races, unchecked errors, ambiguous lifetime, lossy transformations, coupling, and discontinuous paths.

For each risk, state evidence status, affected Parent/Flow/module/symbol, likely impact, and source anchor. Do not propose redesign unless requested.

### 8. 下一層導讀選項

List exact Parent IDs, Flow IDs, modules, entrypoints, and public symbols available next. Give a short reason to choose each. Preserve the validated IDs across follow-ups.

For a large project, keep the System indexes complete and split detailed explanations by selected Parent or Flow. Never omit a Parent or Flow merely to shorten the response.

## Produce a Level 1 Parent view

For a selected L0/L1 Parent, read its validated generated Parent page, show its project-to-Parent breadcrumb, and include:

1. Parent purpose, architecture level, role, implementation status, paths, entrypoints, and public symbols.
2. A Mermaid structure diagram containing the Parent and direct children only.
3. A summary table for the visible modules.
4. One Module card for the Parent and every direct child.
5. Port cards owned by visible modules.
6. Event cards owned by visible modules.
7. Every end-to-end Flow owned by the selected Parent.
8. Relevant formal source classifications, Type/State ownership, and Boundary Mappings exposed by the generated Parent page.
9. Declared/implemented differences, risks, and the compact navigation block.

Use these card contracts without reproducing the full governance schema.

### Module card

Include purpose, architecture level, role, Parent, implementation status, input/output Ports, emitted Events, owned state, side effects, errors, invariants, source paths, entrypoints, and public symbols.

### Port card

Include owner, direction, kind, purpose, semantic data meaning, sync/async timing, immediate rejection conditions, implemented-by relation, and public symbols.

### Event card

Include owner, output Port, purpose, emitted-when condition, payload field types and meanings, intended consumers, delivery semantics, envelope, lifecycle, and idempotency requirements.

## Produce a Level 1 Flow view

Preserve the governed Flow ID and show its project-to-Parent-to-Flow breadcrumb. Include:

1. owner, description, trigger, source data meaning, and entrypoint;
2. a Mermaid sequence diagram across participating modules;
3. an exact ordered-step table;
4. success result and committed state;
5. every declared error branch and handling outcome;
6. timing, task/thread/interrupt/queue/callback boundaries;
7. schema 2.0.2 inherited workload, execution-unit, channel, working-set, cache-sensitive layout, branch/SIMD, compiler, and platform-variant evidence when declared;
8. implementation links and core function roles;
9. risks and compact navigation.

Use:

| # | Module | Action | Receives | Emits | State changes | Side effects | 程式錨點 |
|---|---|---|---|---|---|---|---|

Summarize private branches outside the Flow instead of turning them into artificial governed Flows.

## Produce Level 2 for a module or symbol

Show the project/Parent/Flow breadcrumb when available. Distinguish:

- **做什麼:** responsibility and observable result.
- **如何使用:** callers, inputs, outputs, preconditions, lifecycle, and contract.
- **如何實作:** important branches, delegated calls, algorithms, state, and errors.
- **為何在這一層:** architecture role and relationship to governed Parent/Ports/Events/Flows.

Include parameter and return semantics, immediate rejection versus accepted-work failure, side effects, concurrency assumptions, callers, callees, and linked declarations/definitions. Fully explain the selected main path and summarize adjacent helpers.

## Produce Level 3 for a code region

Keep only enough upper context to orient the reader. Explain incoming values and state; conditions, loops, early returns, and dispatch; conversions and mutations; calls and side effects; and outgoing values, state, errors, and next location.

Relate the region to its containing symbol and Flow when validated context exists. Preserve uncertainty for macros, generated code, runtime configuration, and indirect calls.

## Append compact navigation to Levels 1-3

End every Level 1-3 response with the following literal block. Copy the heading and bold labels verbatim; do not substitute synonyms such as `閱讀位置`, `資料如何抵達`, `下一步`, or `所屬 Flow`.

```markdown
### 精簡導覽

- **目前所在層級與 breadcrumb：** <reading level and path>
- **資料或呼叫從哪裡來：** <immediate upstream source with links>
- **建議接著閱讀的節點：** <selectable Parent, Flow, module, symbol, or branch>
- **可返回的上層 Flow ID：** <owning or nearest Flow ID, or 無／正式架構脈絡受限>
```

Avoid repeating the complete Level 0 overview. Update coverage only when new evidence is inspected.

## Validate the response contract before returning

Perform a final self-check and rewrite the response before returning if any applicable item fails:

- A Level 0 response contains all eight literal level-2 headings exactly once and in the required order.
- The developer reading guide uses exactly `階段｜閱讀目標｜檔案／符號｜為何現在讀｜閱讀重點｜完成判準｜下一站`.
- The task index uses exactly `開發任務｜相關 Flow ID｜從哪裡開始｜關鍵檔案／符號｜設定／資料｜相關測試｜修改風險`.
- A Level 1-3 response begins with one literal `正式架構脈絡` status and ends with the literal `精簡導覽` block.
- A blocked System/Parent response reports `BLOCKED`, the observed version or missing artifact, and the governance next action; it does not emit any of the eight formal Level 0 sections.
- An unsupported-version response identifies an explanation-tool capability limitation and does not claim that the project itself is invalid.
- A supported 2.0.2 response distinguishes formal-governance validity from incomplete AST or symbol consistency evidence.
- Every file/symbol claim has a valid link or an explicit `待確認／symbol 未驗證` label.

## Save only on explicit request

Return guidance in the conversation by default. If the user asks to save it, require a destination before writing Markdown. Never write into `architecture/` under this skill; official architecture documentation remains owned by `$govern-modular-event-architecture`.
