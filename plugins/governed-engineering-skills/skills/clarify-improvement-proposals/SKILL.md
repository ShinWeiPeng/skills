---
name: clarify-improvement-proposals
description: "Clarify every unresolved ambiguity before producing an improvement proposal, then present rendered Markdown with explicit impacts, tradeoffs, and evidence-backed validation. Invoke implicitly for 改善方案、改進方案、優化方案、重構方案、架構改善、設計改善、改善建議、優化建議、方案比較、方案評估、技術選型、提出建議、怎麼改比較好, and equivalent English requests to propose, compare, review, optimize, refactor, or plan improvements. Do not invoke for a direct copyedit, translation, or wording-only change that does not ask for a proposal or design decision. Invoke explicitly with $clarify-improvement-proposals."
---

# Clarify Improvement Proposals

Separate discovery from recommendation. Resolve every ambiguity before treating an improvement proposal as final.

## Clarify first

1. Inspect available code, files, documentation, configuration, tests, and conversation context.
2. Resolve discoverable facts from evidence instead of asking the user.
3. Maintain an exhaustive ambiguity ledger covering goals, success criteria, scope, users, product features, behavior, constraints, compatibility, architecture, algorithm screening, candidate methods, data assumptions, quantitative quality thresholds, delivery, and validation.
4. Ask about every unresolved decision. Re-evaluate the ledger after each answer because answers can introduce new ambiguities.
5. Use the structured choice tool whenever it is available. Batch questions only to respect the tool limit; never treat the batch size as a total-question limit.
6. Stop after each batch and wait for the user. Do not produce a final proposal with unresolved decisions.

For every choice, state why it matters, offer mutually exclusive options, explain impacts and tradeoffs, and mark a recommendation only when evidence supports it. Preserve dependencies between decisions.

## Screen product algorithms

Screen every product feature, not only features that already use the word
algorithm. When method choice can change observable results, involves
data-dependent or tunable behavior, is constrained by compute or timing, affects
safety or other quality risks, or needs fallback behavior, treat the feature as
algorithm-bearing.

For an architecture proposal, invoke `$govern-modular-event-architecture` and
read its `references/algorithm-design.md`. Record the screening conclusion for
every feature. A triggered feature requires a proposed Algorithm Design Record
owned by its implementing L1 or L2 module. A non-triggered feature requires a
specific `not applicable` reason.

Do not treat the proposal as decision-complete while the selected method,
quantitative acceptance thresholds, data assumptions, or a risk-required
prototype or benchmark remains unresolved.

## Enforce mode checkpoints

Before clarification, verify that the surface provides a structured choice tool. If unavailable, do not replace it with Markdown questions and do not produce the proposal. Tell the user to switch to Plan mode with `/plan` or `Shift+Tab`, invoke this skill again, and wait.

After all decisions are resolved:

1. Produce the confirmed proposal in Markdown.
2. Do not implement while in Plan mode.
3. Tell the user to switch to Default mode or another named execution-capable mode.
4. Ask the user to send `Implement the confirmed plan.`
5. Begin implementation only after the mode change and explicit confirmation can be verified.

If the user explicitly requests a preliminary proposal, label every assumption and unresolved decision. Do not present it as final.

## Integrate architecture governance

When the proposal creates a software project; adds, splits, merges, or reorganizes modules; changes data flow, events, callbacks, ports, adapters, or dependency direction; or otherwise affects architecture:

1. Invoke `$govern-modular-event-architecture` and read its required references.
2. Inspect `architecture/manifest.yaml`, `architecture/ARCHITECTURE.md`, accepted ADRs, and `architecture/baseline.yaml` when present.
3. Add an `Architecture impact` section identifying affected levels, modules, ports, events, dependency edges, and compatibility boundaries.
4. Describe the expected manifest diff without writing it in Plan mode.
5. Add a `Description Views impact` subsection covering changed module, Port, Event, source path, entrypoint, public-symbol, System/Parent page, and L0/L1 Flow descriptions. State which generated pages are expected to change.
6. Identify required ADRs. Keep them proposed until the user explicitly approves them; never let Codex approve its own exception.
7. Add the single `architecture_cli.py gate` entry, deterministic generated-view comparison, adoption readiness, and every applicable language analyzer to the validation matrix. Do not present partial internal-script results as a complete governance PASS.
8. Add an `Algorithm impact` section listing each product feature's screening result, owning module, required `ALG-####` record, evidence status, and whether the algorithm changes public architecture contracts.
9. Add an `Execution efficiency impact` section for schema 1.2 projects. Identify affected Workloads, Execution Profiles/Units/Mappings/Channels, Data Access Profiles, Microarchitecture Profiles, and platform variants. Never equate Modules with Tasks.
10. Require human confirmation of platform, CPU, runtime, compiler, cache topology, and scheduler capabilities before accepting execution or microarchitecture decisions. Treat missing confirmation as unresolved/`BLOCKED`.
11. Require Tier 1 analysis for hard-real-time workloads. Tier 2 layout, tiling, branch, SIMD, PGO, LTO, scheduling, or fixed tuning changes require a portable/as-is baseline, representative candidate benchmarks, and full-Flow non-regression criteria.
12. For every hard/soft real-time workload, read the governance skill's `references/realtime-scheduling-analysis.md` before finalizing Task count, activation rate, priority, core allocation, Queue/notification, synchronization, scheduler method, deadline, or soft SLO decisions. Require at least two structurally different candidates, scheduler-compatible provisional analysis, a generated human-readable Markdown study report, and explicit non-AI selection before implementation. RTOS alone does not trigger RMA; timing class triggers the study and scheduler compatibility selects the method.

For an existing project without governance files, propose an as-is inventory followed by remediation of every discovered violation. A baseline is not the default migration result: include one only for exact items a non-AI developer explicitly chooses to defer, with a review date and removal condition. Release requires the temporary baseline to be empty. For a new project, propose confirmed bootstrap inputs and generated governance artifacts.

## Render the final proposal

Use GitHub-flavored Markdown and include applicable sections:

```markdown
# Improvement proposal

## Goals and success criteria
## Current state and problems
## Confirmed decisions
## Architecture impact
## Execution efficiency impact
## Algorithm impact
## Recommended improvements

### Improvement 1: Descriptive name
- **Change:**
- **Expected impact:**
- **Benefits:**
- **Costs and disadvantages:**
- **Tradeoffs:**
- **Risks:**
- **Dependencies:**
- **Alternatives considered:**
- **Why this is recommended:**

## Alternatives comparison
## Implementation order
## Validation and acceptance criteria
## Remaining uncertainties
```

For every improvement, explain affected users and systems, existing behavior and compatibility, implementation and migration costs, maintenance, user experience, performance, reliability, security, schedule, gains, sacrifices, and the consequence of not adopting it. Name conflicting goals when no option dominates.

## Require evidence-backed validation

Map every improvement and acceptance criterion to at least one validation row containing:

- validation method;
- executable command or reproducible steps;
- expected observable output;
- explicit pass condition;
- evidence format.

Prefer focused automated tests, followed by integration, end-to-end, regression, build, type, lint, or static checks according to risk. Do not use a build alone to prove runtime behavior when stronger evidence is available.

For documentation and workflows, require rendered output, schema or link checks, structured diffs, or a manual checklist recording observer, steps, observation, and pass condition. Explain why manual validation is necessary when automation is unavailable.

In Plan mode, label results as expected evidence and never imply that validation has run. Require the execution phase to report actual commands, exit codes, minimal raw output, and `PASS`, `FAIL`, or `BLOCKED`. Do not declare completion unless every required criterion has valid `PASS` evidence.

## Require four validation gates

For product work with runtime, integration, operating-system, firmware, or hardware risk, organize validation in this order and make every gate explicit in the proposal:

1. **Validation Enablement:** before product changes, define the tracked profile and local binding boundary; probe build, upload, reset, trigger, capture, native export, and parser capabilities; dry-run synthetic or loopback evidence with a unique run ID, matching session begin/end, continuous sequence, zero drops, and deterministic PASS/FAIL/BLOCKED fixtures. Missing capability is `BLOCKED`, not product failure.
2. **Per-change Development Validation:** map each change group to its risks, focused unit/behavior/integration/protocol/schema/static tests, commands, and expected evidence. Require on-device smoke only after changes to hardware adapters, transports, DMA/interrupts, timing, event ordering, validation wiring, or native providers. Smoke proves boot, basic control/observation, complete capture, and absence of immediate hard faults; it never substitutes for final flow or statistical acceptance.
3. **Final Runtime Acceptance:** use separate validation-build scenarios with independent run IDs, initial states, triggers, completion contracts, bounded time/bytes, and raw evidence. Select only project-relevant nominal, fault/recovery, load/stress, and platform-resource scenarios.
4. **Release Acceptance:** rebuild the release composition after runtime acceptance; prove test-only commands, adapters, injections, validation flags, and `VAL_*` symbols are absent; run the release build, full regression, architecture checker, deterministic renderer, applicable analyzers, size/resource limits, and project safety checks. Keep validation-build and release-build evidence separate.

Do not declare the work complete unless all four gates are `PASS`. If required user-operated or physical evidence is pending, report overall `BLOCKED`.

## Plan Gate 1 through inverted Ports

Treat ordinary Gate 1 checks as host-side development tests. Do not plan flash, Serial/TCP capture, `VAL_SESSION_BEGIN/END`, user log upload, or GPT log interpretation for a unit test, Fake Port test, or host integration test. Let the project test framework determine PASS/FAIL from assertions and exit codes; let Codex execute the command and preserve structured evidence.

For every change group:

1. Name the affected Module, Port, Event, and Flow references, risks, and test boundary.
2. Test L0/L1 parent orchestration with Fake child Ports and captured child Events, including routing, ordering, rejection, and failure propagation.
3. Test L2 functional components by injecting Fake dependency Ports and a Capture output Port, including state changes and emitted Events.
4. For every external-technology Port implemented by an L3+ Adapter, require a demand-owned reusable contract suite and run it against the applicable Fake, Simulator, and Real Adapter implementations.
5. Record the executable, argv, exit code, verdict, and hashed result artifacts for every check.
6. Declare whether on-device smoke is required and why. Require it only when hardware Adapters, transports, DMA/interrupts, real timing, event ordering, validation wiring, or native providers are affected.

Plan Gate 2 by governed end-to-end Flow with the real composition and risk-relevant real Adapters. Do not rerun every layer's Gate 1 tests as separate runtime acceptance scenarios. A smoke result can support Gate 1 but cannot satisfy Gate 2.

## Establish validation capability before product changes

For runtime, integration, operating-system, firmware, or hardware acceptance criteria, add a `Validation Enablement` phase before product implementation:

1. Define the tracked `validation/on-device.yaml`, local binding boundary, selected target platform/provider, allowed fallback, permissions, scenarios, and evidence locations.
2. Probe whether Codex or the user can build, upload, reset, trigger, capture, export, and parse the required evidence.
3. Identify which steps Codex performs and which require guided user operation. Do not wait until final validation to discover that no executable path exists.
   For user-operated steps, require a guided form for ordered fact collection and a generated read-only summary table for one-time confirmation. Keep PASS/FAIL/BLOCKED ownership in the runner; provide Markdown plus schema-bound JSON for offline operation.
4. Implement and dry-run the validation runner, parser, synthetic/loopback fixtures, and permission gates before changing product behavior.
5. Route execution through `$validate-on-device`. If that Skill or a required provider is unavailable, report `BLOCKED` with remediation rather than substituting a build or an unstructured log excerpt.

For projects where the OS schedules threads, require an OS-native evidence provider for scheduler/resource criteria: ETW/WPR on Windows, perf/ftrace on Linux, and Instruments/XCTest on iOS. Use application events for domain semantics and correlate sources with a run ID and monotonic marker. Missing required native evidence is `BLOCKED`; structured logs cannot pass supported-OS scheduler/resource criteria.

## Require on-device evidence

When a proposed change can affect physical hardware, firmware timing, peripherals, connectivity, boot, power, sensors, actuators, or device state, include a bounded on-device log protocol:

- initial device state;
- trigger scenario;
- expected events, order, values, and tolerances;
- success condition and forbidden error patterns;
- a scenario-specific maximum duration derived from the slowest legal flow or sampling plan; never invent a universal 30-second acceptance window;
- build, flash, reset, and bounded serial capture steps;
- existing log framework and a release-disabled log level or compile-time diagnostic flag.

Also require:

- tagged, machine-parseable session begin/end, run ID, monotonic time, continuous sequence, record count, dropped count, and bounded observation window;
- guided user steps when Codex cannot upload or control the product; user-only observations must enter the same evidence through a test-only command;
- an explicit `upload_verified_by_gpt` field when the user performs upload;
- O(1), allocation-free device-side aggregation instead of per-sample logging on high-frequency paths;
- hard limits for any single forbidden drop, overflow, watchdog, reset, corruption, or deadline violation;
- a calculable sampling plan or stable external-standard reference, maximum duration, warm-up window, confidence/error target, and instrumentation overhead budget for statistical criteria;
- `BLOCKED` rather than product `FAIL` when the trigger, complete window, sample sufficiency, trace loss, log loss, or measurement validity is unproven.

Do not claim physical validation occurred in Plan mode. Route execution through `$validate-on-device` when available.
