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

Project verification requirements now follow the current specification across reloads and short continuation commands. The workflow distinguishes implementation progress from acceptance: missing hardware evidence cannot be replaced by host tests or a successful build. The shared validation plan records the applicable layers and their evidence sources.

## Test and evidence boundaries

Acceptance mappings can bind to the current criterion with `criterion_sha256`.
Changing a criterion while retaining its AC ID makes the old binding stale; update
the reviewed mapping before execution. Evidence text is excluded from this digest.

Tests now have explicit Module or Flow ownership under `tests/`. Authored validation
plans stay under `validation/`; each execution keeps its own immutable run under
`artifacts/`. This keeps specifications readable and prevents later runs from
replacing the evidence they cite. Whole-project checks include existing files and
report missing analyzer coverage. Fixture sharing and test-only hooks have explicit
boundaries; project-specific retention and Git ignore choices remain separate.
