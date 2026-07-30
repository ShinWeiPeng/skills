---
name: validate-on-device
description: "Collect and evaluate bounded runtime evidence from physical devices and operating-system applications. Use for on-device validation, hardware tests, firmware boot/timing/peripheral checks, COM or TCP capture, Windows ETW/WPR, Linux perf/ftrace, iOS Instruments/XCTest, guided user-operated testing, structured VAL_* logs, statistical high-frequency evidence, capability probes, permission gates, and PASS/FAIL/BLOCKED evidence bundles. Do not invoke for ordinary unit tests, build-only checks, static code review, or code explanation without runtime validation. Invoke explicitly with $validate-on-device."
---

# Validate On Device

Use reproducible evidence instead of treating a successful build or an unstructured log excerpt as runtime proof.

## Select the evidence route

1. Read `validation/on-device.yaml` and the optional local binding `.codex/on-device.local.yaml`. Profile 1.1 may bind an architecture manifest hash and accepted Execution Profile.
2. Honor the profile's manually selected target platform and provider. Do not guess or silently change them.
3. For Windows, Linux, or iOS thread, scheduler, CPU, memory, I/O, or network criteria, require the selected native provider. Structured logs cannot pass these criteria. Read [references/providers.md](references/providers.md).
4. Use application events for domain behavior. Correlate native traces and application events with the same run ID and monotonic markers.
5. Use structured event logs for domain behavior and O(1) statistics for bare-metal/custom targets. Read [references/evidence-contract.md](references/evidence-contract.md).
6. When Codex cannot operate the product or platform tool, use the guided form-and-review workflow. Generate an immutable session, response template, and user guide. With connectivity, ask one step at a time, read the recorded fact back, and write JSON for the user. Offline, give the user the Markdown guide and schema-bound JSON template. Read [references/guided-testing.md](references/guided-testing.md).
7. Treat the final Markdown table as read-only review. The user confirms recorded facts once; only the runner assigns PASS, FAIL, or BLOCKED.

## Enforce safety before execution

- Treat `probe` and profile validation as passive.
- Require explicit approval for flash, reset, serial open that may toggle DTR/RTS, administrator/root tracing, actuators, erase, calibration writes, or irreversible actions.
- Use executable plus argv lists. Never execute a shell command string from a profile.
- Do not scan networks, modify firewalls, install drivers or packages, or elevate privileges automatically.
- Bound every capture by timeout and maximum bytes. Scope native traces to declared processes/providers when possible.
- Return `BLOCKED` with remediation when a required capability, permission, unique endpoint, trace export, cleanup, or complete evidence window is unavailable. Trace scenarios declare idempotent cleanup actions.

## Enforce the validation gates

1. Run `enablement` scenarios before product changes. Validate the profile, probe every required capability, generate a unique guided run, and prove the parser with synthetic PASS, FAIL, and BLOCKED fixtures.
2. Keep ordinary per-change unit, behavior, integration, protocol, schema, and static checks outside this runtime runner. Do not flash, capture runtime logs, or request user log upload for Fake Port, unit, or host integration tests; the native project test framework owns their assertions and exit codes. Run a `smoke` scenario only for risk milestones affecting hardware, transport, timing, event order, validation wiring, or a provider. Never cite smoke as final acceptance.
3. Run `acceptance` scenarios only with PASS bundles from every declared enablement prerequisite. Flow scenarios require trigger proof, required coverage, and the configured session-end reason. Statistical scenarios require a calculable or external-standard sample plan. Mixed scenarios require both.
4. After runtime acceptance, require a separate release acceptance report proving that test-only wiring and `VAL_*` symbols are absent and that release build, regression, architecture, analyzer, size, and safety checks pass. The runtime runner does not turn a validation image into release evidence.

## Run the deterministic tooling

Resolve a project-specified Python 3 runtime first, then another available runtime that imports the pinned requirements. Missing capability is `BLOCKED`; never embed a user-specific interpreter path.

```powershell
python scripts\validate_on_device.py validate-profile `
  --profile <project>\validation\on-device.yaml `
  --local <project>\.codex\on-device.local.yaml
```

Other subcommands are `probe`, `prepare-guided-session`, `finalize-guided-session`, `capture`, `run-action`, `evaluate`, `run`, and `summarize-gates`. Guided evaluation supplies the session, immutable response revision sequence, and recomputable review. Acceptance evaluation supplies PASS enablement bundles with `--prerequisite-result`. `summarize-gates` combines profile-bound runtime, structured per-change development, and release result documents and refuses to let smoke substitute for acceptance. It recomputes Gate 1 from change groups, checks, hashed evidence, external-Port contract coverage, and required profile-bound smoke results; it does not execute host tests. Read [references/development-gate.md](references/development-gate.md). Native evaluation supplies both normalized JSON (`--native-evidence`) and the original trace (`--native-source-trace`) so their SHA-256 linkage is verified. Run `--help` before using an unfamiliar command.

## Judge evidence

- `PASS`: the selected or allowed-fallback evidence is complete and every required criterion passes.
- `FAIL`: a proven trigger plus a complete bounded scenario misses required flow behavior, or complete evidence violates a hard limit, statistical threshold, or forbidden pattern.
- `BLOCKED`: evidence is incomplete, samples are insufficient, records were dropped, instrumentation exceeded its budget, or execution could not be proven.
- Overall precedence is `FAIL > BLOCKED > PASS`.
- Do not infer failure from a missing event when the trigger or complete observation window is not proven. Treat that case as `BLOCKED`.
- A user-uploaded raw log may produce full PASS when the profile permits it, but record `upload_verified_by_gpt: false`.
- A missing, pending, unconfirmed, mismatched, or blocked required guided step is `BLOCKED`; user confirmation never overrides criterion evidence.

## Explain each test to the user

Read [references/user-facing-reporting.md](references/user-facing-reporting.md) before presenting a runtime scenario or its result.

- Before operation, state the test name, purpose, criteria-backed test items, initial state, risks, user actions, and expected flow.
- During operation, show only the current action, completion signal, and timeout.
- After evaluation, lead with the runner verdict and follow every literal heading in the reference exactly once and in order. Do not omit, merge, or rename headings. Map every criterion to expected and observed evidence, identify the first difference, classify the problem, and link the evidence.
- Always show the expected flow. A passing one- or two-event flow must use an inline chain, not Mermaid. Use Mermaid for longer or ordering-sensitive flows and for `FAIL` or `BLOCKED` when it clarifies the evidence boundary.
- Use optional profile `title`, `purpose`, criterion `label`, and `description` fields when present. Otherwise use the reference's explicitly marked contract-derived fallback; never invent product intent.
- Never let presentation, user confirmation, or a raw-log interpretation override the runner verdict.
- Run the reference's response self-check before sending any pre-test brief or post-test result.

## Preserve the evidence bundle

Write under `.codex/evidence/on-device/<run-id>/` and include the raw evidence hash, profile snapshot, capability result, parser result, criterion results, actual argv/exit codes when available, evidence provider/fallback reason, actor, permission decisions, and final verdict. Never store literal secrets.

## Respect architecture governance

This Skill's runner is governed by its own standard/schema 1.1 manifest. For a target project governed by `$govern-modular-event-architecture`, profile 1.0 references Flow, Module, Port, or Event; profile 1.1 may additionally reference Workload, Execution Profile/Unit/Channel, Data Access Profile, or Microarchitecture Profile and must bind the manifest SHA-256. Keep test parsers and test wiring out of release composition roots.
