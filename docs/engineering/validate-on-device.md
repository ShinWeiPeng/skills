Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/validate-on-device)

## What it does

`validate-on-device` collects bounded runtime evidence from physical devices and operating-system applications and turns it into PASS, FAIL, or BLOCKED evidence. A build result or unstructured log is never treated as runtime proof.

## When to reach for it

Type `/validate-on-device`, or Codex reaches for it when acceptance depends on hardware, firmware, native tracing, serial or network capture, permissions, or guided user-operated testing.

## Prerequisites

The target device or operating-system application, required permissions, and a bounded validation profile must be available. Missing non-substitutable access remains BLOCKED.

## Bounded evidence

Its leading idea is **measure the claim**: each capture names the criterion, environment, time bound, evidence source, and verdict instead of collecting an open-ended log.

During an active scenario, every operation includes a concise higher-level purpose before the current action, completion signal, and timeout. The purpose explains how the result will be used and which failure or uncertainty it helps prevent, rather than merely restating the command. The complete pre-test brief still appears only once.

## Where it fits

This is the runtime-evidence gate after ordinary tests and architecture checks. [ask-matt](https://aihero.dev/skills-ask-matt) invokes it only when the task needs native or physical evidence.

Project verification requirements now follow the current specification across reloads and short continuation commands. The workflow distinguishes implementation progress from acceptance: missing hardware evidence cannot be replaced by host tests or a successful build. The shared validation plan records the applicable layers and their evidence sources.

## Test and evidence boundaries

Tests now have explicit Module or Flow ownership under `tests/`. Authored validation
plans stay under `validation/`; each execution keeps its own immutable run under
`artifacts/`. This keeps specifications readable and prevents later runs from
replacing the evidence they cite. Whole-project checks include existing files and
report misplaced files and broken references. Layout does not impose language
analysis, dependency or isolation proofs; independent architecture and runtime
verification requirements remain applicable; project-specific retention and Git ignore choices remain separate.
