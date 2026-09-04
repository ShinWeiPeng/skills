# Verification Ladder

Availability:

Install **Governed Engineering Skills**, then start a new Codex task so the new
skill inventory is loaded.

[Source](../../skills/engineering/verification-ladder/SKILL.md)

## What it does

`verification-ladder` selects the lowest sufficient additive evidence layers for
affected module contracts: Module Contract, production-code SIL, reusable Adapter
Contract suites, target-compiled PIL, production-composition HIL, and bounded
System/Soak acceptance.

The project stores architecture bindings, thresholds, scenarios, evidence paths,
and non-applicability rationale in `validation/verification-ladder.yaml`. Universal
hard triggers and evidence-authority rules remain stable across projects.

## TDD and model tests

TDD remains the red-green implementation loop at confirmed public seams. A
reference or mathematical model may provide an independent expected-result oracle,
but it does not become SIL unless the test executes the production functional
implementation and replaces only external dependencies.

## PIL versus HIL

PIL establishes controlled operation cost and resource evidence on the selected
target with fixed vectors. HIL is required for production timing or deadline claims
affected by actual core mapping, scheduler behavior, interrupts, peripherals,
synchronization, or competing workloads.

## Device execution

The ladder decides why PIL, HIL, or System/Soak is required. It delegates those
bounded runs, permissions, capture, native traces, and verdict artifacts to
`validate-on-device`. Host Module Contract, SIL, and Fake/Replay Adapter suites stay
with the project's native test runner.
