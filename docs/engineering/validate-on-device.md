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

## Where it fits

This is the runtime-evidence gate after ordinary tests and architecture checks. [ask-matt](https://aihero.dev/skills-ask-matt) invokes it only when the task needs native or physical evidence.
