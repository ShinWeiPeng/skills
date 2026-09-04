---
name: verification-ladder
description: Plan and govern module-contract, SIL, Adapter Contract, PIL, HIL, and System/Soak verification when engineering claims span host, target, hardware, or long-duration environments. Use for layered verification planning and evidence-authority decisions; use TDD for the implementation loop and validate-on-device for selected device execution.
---

# Verification Ladder

Select the lowest sufficient additive verification layers for the affected contracts
and claims. Do not force the complete ladder merely because a project is embedded,
and do not let evidence from a lower-authority environment substitute for the layer
that owns the claim.

Before planning, invoke `$engineering-risk-routing` and honor its architecture,
proposal, runtime-evidence, and review gates. Read the confirmed change-set SPEC,
`architecture/manifest.yaml`, `validation/verification-ladder.yaml`, and, when
referenced, `validation/on-device.yaml`. Resolve the target platform, runtime,
scheduler, topology, and acceptance values from repository evidence and governed
grilling; never assume ESP32 or copy example rates, batches, counters, or durations.

## Establish the project contract

Keep project bindings at `validation/verification-ladder.yaml`, conforming to
[the matrix schema](references/verification-ladder.schema.json). The skill owns the
stable taxonomy, additive hard triggers, layer order, evidence authority, and
fail-closed behavior. The project owns architecture IDs, platform/runtime facts,
thresholds, scenarios, evidence locations, and explicit non-applicability rationale.

References are links, not copies:

- Resolve Module, Port, Event, Flow, Workload, Execution Profile/Unit/Channel, Data
  Access Profile, Microarchitecture Profile, and platform-variant IDs from the
  architecture manifest.
- Resolve device scenario IDs and the selected Execution Profile from
  `validation/on-device.yaml`.
- Return `BLOCKED` for missing, stale, duplicated, mismatched, unknown, or unmapped
  references. Never guess a replacement.

For a new project, create the matrix only after project features, architecture,
platform facts, and validation thresholds are confirmed. For an existing project,
inventory actual contracts, test seams, adapters, execution mappings, runtime
profiles, and evidence first; do not relabel old tests as SIL, PIL, or HIL without
proving their composition.

Validate and plan with the public CLI:

```powershell
python skills/engineering/verification-ladder/scripts/verification_ladder.py validate `
  --matrix validation/verification-ladder.yaml `
  --architecture architecture/manifest.yaml `
  --on-device validation/on-device.yaml

python skills/engineering/verification-ladder/scripts/verification_ladder.py plan `
  --matrix validation/verification-ladder.yaml `
  --architecture architecture/manifest.yaml `
  --on-device validation/on-device.yaml `
  --contract-dimension state-transition `
  --execution-change core-mapping `
  --evidence-claim production-timing
```

Omit `--on-device` only when the matrix declares no device profile and no rule
references a device scenario or Execution Profile. Unknown or project-unmapped
triggers are `BLOCKED` even when a universal hard trigger already names a layer.

## Define each affected Module Contract

Before implementation acceptance, record for every affected module:

- input data, units, ranges, validity, timestamps, and sequence semantics;
- output values or events and delivery semantics;
- state transitions and mutation authority;
- legal call and lifecycle order;
- errors, timeouts, overflow, reset, and recovery behavior;
- maximum batch and queue/backlog behavior;
- applicable throughput, latency, memory, stack, CPU, power, or other resources;
- explicit PASS, FAIL, and BLOCKED thresholds plus evidence and stop conditions.

Use `$tdd` at the confirmed public seams to implement executable behavior in
vertical red-green slices. TDD is the implementation method; a passing host test is
not automatically proof of target cost, integrated timing, physical behavior, or
long-duration stability.

## Execute only the selected layers

### Module Contract Test

Exercise the module's public commands, queries, events, state transitions, ordering,
failure/reset behavior, boundary batches, conservation, backlog, and resource
assertions using native project test tools. Keep expected results independent from
the implementation.

### Software-in-the-Loop (SIL)

Run the production functional implementation on the host. Replace only hardware,
clock, transport, storage, or other external dependencies with Fake or Replay
Adapters. Exercise project-selected rates, time/sequence/pairing semantics, boundary
batches, conservation/backlog, failures, gaps, resets, and bounded-duration cases.

A simplified duplicate Processing model is not SIL. A separate mathematical or
reference-model test may provide an oracle, but it cannot replace execution of the
production implementation.

### Adapter Contract Test

The demand-side Port owner defines one reusable contract suite. Run that same suite
against every applicable Fake, Replay/Simulator, and real target Adapter. Cover
initialization/stop order, count semantics, data format and units, timeout, overflow,
reset, failure reporting, and bounded blocking. Adapter-specific tests may add
coverage but never replace the shared suite.

### Processor-in-the-Loop (PIL)

Compile and run production functional code on the project-confirmed target using
fixed vectors independent of real sensors or other physical inputs. PIL may measure
controlled operation cost, percentile/maximum execution time, pacing, batch time,
stack, queue, and target-resource high-water marks.

PIL cannot alone pass production latency or deadline claims affected by core
mapping, scheduling, interrupts, peripheral traffic, synchronization, or competing
workloads. For hard/soft real-time work, use PIL measurements as inputs to the
governed scheduling analysis.

### Hardware-in-the-Loop (HIL)

Use the real target composition and production execution profile: core/execution-unit
mapping, scheduler, interrupts, competing workloads, peripherals, buses, FIFOs,
transports, clocks, and applicable external client software. HIL owns production
timing/deadline acceptance when those conditions affect the result, plus physical
arrival patterns, bus latency, drift, compatibility, interference, restart,
disconnect, and recovery evidence.

### System/Soak Test

Run bounded project-selected end-to-end combinations for the justified duration.
Cover applicable load levels, client combinations, logging A/B, offline/rejoin,
recovery, and unchanged external clients. Declare forbidden watchdogs, unexpected
resets, unexplained loss, corruption, deadline violations, and queue overwrite.

## Delegate device execution

For every selected PIL, HIL, or System/Soak layer, invoke `$validate-on-device` after
Validation Enablement. Let it own permissions, provider probing, upload/reset,
bounded capture, native traces, evidence integrity, and PASS/FAIL/BLOCKED evaluation.
This skill owns why the layer is required and whether its evidence has sufficient
authority; it does not duplicate the runtime runner. Keep host Module Contract, SIL,
and Fake/Replay Adapter suites in the native project test framework.

Assess an evidence claim directly when needed:

```powershell
python skills/engineering/verification-ladder/scripts/verification_ladder.py assess-evidence `
  --claim production-timing `
  --passed-layer pil `
  --passed-layer hil
```

Host evidence remains valid for host-observable semantics. Controlled target-cost
evidence requires PIL; production timing and physical integration require HIL;
system stability requires System/Soak. Hard/soft real-time acceptance requires the
governed scheduling analysis plus selected PIL inputs and final HIL evidence.

## Report the result

For each layer report scope, triggered rule IDs, inputs, executable command or guided
steps, metrics and thresholds, evidence artifact, verdict, stop condition, and next
permitted layer. Mark an unselected layer `not applicable` only with the matrix's
project-specific rationale. Overall completion is `BLOCKED` while any selected layer
or required architecture/scheduling analysis lacks PASS evidence.
