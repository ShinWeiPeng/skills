## What it does

`verification-ladder` selects the lowest sufficient additive evidence layers for
affected module contracts: Module Contract, production-code SIL, reusable Adapter
Contract suites, target-compiled PIL, production-composition HIL, and bounded
System/Soak acceptance.

The project stores architecture bindings, thresholds, scenarios, evidence paths,
and non-applicability rationale in `validation/verification-ladder.yaml`. Universal
hard triggers and evidence-authority rules remain stable across projects.

## When to reach for it

Type `/verification-ladder`, or the agent selects it when engineering acceptance
needs host, target, hardware or long-duration evidence. Use
[TDD](https://aihero.dev/skills-tdd) for the implementation loop and
[validate-on-device](https://aihero.dev/skills-validate-on-device) for device runs.

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
report misplaced files and broken references. Layout does not impose language
analysis, dependency or isolation proofs; independent architecture and runtime
verification requirements remain applicable; project-specific retention and Git ignore choices remain separate.

## One source for acceptance

Acceptance definitions and methods are maintained in SPEC. The tool projection is
rebuildable and checked against that source before selecting verification layers.
Missing selections remain visible; generating definitions cannot count as passing
tests or device evidence. Existing legacy mappings remain readable during migration.

## Review the validation plan before confirming

The assistant prepares the readable validation methods and tool selections from
the same SPEC. Missing selections are listed together before confirmation, while
drafts can still be saved. A generated mapping is not a complete plan or passing
test evidence. Explicit user waivers are recorded with their scope and source and
shown separately from tests that passed; other evidence remains required.


## Complete modules on the host

Test production modules through their public interfaces and replace only external
dependencies with Fake or Replay. These module SIL cases verify I/O, state, event
order and recovery; add integration tests for coordination between modules. A host
regression suite can satisfy SIL when it runs this production code and preserves
actual commands, results, cases and source hashes. A build or architecture check
alone cannot complete functional validation. Selected PIL/HIL cases run after the
appropriate target build and flash, with their own recorded results.

## Where it fits

This is the verification-planning step inside delivery. It selects the evidence
layers; TDD executes host cases and validate-on-device executes selected device
cases. [ask-matt](https://aihero.dev/skills-ask-matt) routes engineering requests
into the appropriate workflow.
