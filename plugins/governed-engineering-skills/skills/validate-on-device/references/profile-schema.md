# On-device profile contract

Profile version `1.1` extends 1.0 with an `architecture` mapping:

```yaml
version: "1.1"
architecture:
  manifest: architecture/manifest.yaml
  manifest_sha256: "<64 lowercase hex characters>"
  execution_profile: target-platform-profile
```

For schema 1.2 manifests, `execution_profile` must resolve to an accepted profile and match the selected target platform/provider boundary. Scenario `architecture_refs` may name Flow, Module, Port, Event, Workload, Execution Profile, Execution Unit, Execution Channel, Data Access Profile, or Microarchitecture Profile IDs. Missing/stale hashes, unresolved IDs, or a non-accepted selected profile are `BLOCKED`.

The tracked `validation/on-device.yaml` contains no machine-specific secrets. The optional local file supplies endpoint bindings and tool paths. Profile version `1.0` uses the contract below; profiles using the former implicit scenario timeout/minimum-sample fields are invalid and must be rewritten.

```yaml
version: "1.0"
target:
  platform: bare-metal
  provider: structured-log
  native_max_bytes: 4294967296
transport:
  type: serial
  binding: primary
  baud: 115200
  dtr: false
  rts: false
  timeout_seconds: 120     # transport safety limit, not acceptance duration
  max_bytes: 1048576
actions:
  build-validation:
    executable: C:/path/build.exe
    args: [validation]
    cwd: .
    risk: build
    timeout_seconds: 300
    max_output_bytes: 1048576
scenarios:
  - id: parser-loopback
    phase: enablement
    evidence_mode: flow
    max_duration_ms: 5000
    prerequisites: []
    actions: [build-validation]
    cleanup_actions: []
    architecture_refs: [FLOW-VALIDATION-001]
    completion:
      trigger_criteria: [started]
      required_criteria: [initialized]
      session_end_reason: complete
    forbidden_patterns: ["ASSERT", "watchdog"]
    criteria:
      - id: started
        type: event_sequence
        events: [validation_started]
      - id: initialized
        type: event_sequence
        events: [validation_started, system_initialized]
  - id: steady-load
    phase: acceptance
    evidence_mode: statistical
    max_duration_ms: 60000
    prerequisites: [parser-loopback]
    architecture_refs: [FLOW-LOAD-001]
    completion:
      trigger_criteria: [load-started]
      required_criteria: [latency]
      session_end_reason: complete
    criteria:
      - id: load-started
        type: event_sequence
        events: [load_started]
      - id: latency
        type: statistic
        metric: latency_us
        method: percentile
        percentile: 0.95
        operator: <=
        threshold: 50
        max_duration_ms: 60000
        sample_plan:
          basis: calculated
          model: distribution
          confidence: 0.95
          absolute_error: 0.05
```

Supported phases are `enablement`, `smoke`, and `acceptance`. Supported evidence modes are `flow`, `statistical`, and `mixed`. Every scenario requires a positive `max_duration_ms` and a `completion` mapping with non-empty `trigger_criteria`, non-empty `required_criteria`, and `session_end_reason`. Completion IDs must name criteria in the same scenario. Flow/mixed scenarios require a flow criterion; statistical/mixed scenarios require a statistic or native metric. Acceptance scenarios require one or more prerequisite scenario IDs, and every prerequisite must name an enablement scenario.

The scenario duration is derived from the slowest legal flow or sampling plan. There is no default. Transport and action timeouts remain independent safety limits. Serial/TCP capture may stop early only after a matching run/scenario `VAL_SESSION_END` with the configured reason.

Supported platforms are `windows`, `linux`, `ios`, `bare-metal`, and `custom`. Supported providers are `etw-wpr`, `perf-ftrace`, `instruments-xctest`, and `structured-log`. Windows/Linux/iOS scheduler, CPU, memory, I/O, and network criteria use `native_metric` and require the selected native provider. Structured logs may carry correlated domain events but cannot pass those resource criteria. Bare-metal/custom targets may select structured logs and O(1) statistics.

The optional local file is not a policy overlay. It may contain only endpoint identity under `bindings` (`port`, `host`, `device`, `udid`, `process`, or `pid`) and `actions.<name>.executable` paths for actions already declared in the tracked profile. It cannot change risks, argv, DTR/RTS, limits, scenarios, criteria, providers, or cleanup policy.

When `architecture.manifest` is present, every scenario requires `architecture_refs`, and every reference must resolve to a declared Flow, Module, Port, or Event.

Actions use an executable plus argv. Risks are `passive`, `build`, `trace`, `serial-open-reset`, `flash`, `reset`, `actuate`, and `irreversible`. Trace record actions require a bounded artifact, maximum artifact bytes, and idempotent cleanup. Literal secret fields are rejected.

Criterion types are:

- `event_sequence`: ordered domain events.
- `observation`: a structured user observation.
- `hard_limit`: a complete aggregate field compared with a threshold; a single violation may fail.
- `statistic`: a structured-log aggregate evaluated only after sample sufficiency.
- `native_metric`: a normalized OS metric correlated to application evidence and its source trace.

Every `statistic` and `native_metric` declares one sampling plan:

```yaml
sample_plan:
  basis: calculated
  model: proportion | mean | distribution
  confidence: 0.95
  absolute_error: 0.05
  expected_proportion: 0.5  # proportion only
  estimated_stddev: 1.0     # mean only
```

or:

```yaml
sample_plan:
  basis: external-standard
  reference: IEC-or-project-standard-section
  min_samples: 1000
```

The runner uses the normal proportion error formula, normal mean confidence interval, or Dvoretzky-Kiefer-Wolfowitz distribution bound to recompute calculated sample counts. Unsupported industry methods use a stable external reference. Insufficient samples are `BLOCKED`.

Statistic methods remain `field`, `mean`, `mean_upper_ci`, `percentile`, and `wilson_upper`. Timing statistics also require instrumentation budgets and clock identity. Warm-up distributions use `phase=steady`; hard limits span all phases. Native metrics require a complete native window, zero trace loss, source-trace SHA-256, sample/semantic binding, and run-ID/monotonic correlation.

`guided_steps` is optional. When present, IDs are unique and ordered; each step requires `instruction` and `expected_observation`, with optional `required`, `evidence_required`, and `observation_code`. Users record facts only. The runner owns PASS/FAIL/BLOCKED.

Acceptance evaluation receives every declared enablement `result.json` through `--prerequisite-result`; the scenario, phase, PASS verdict, and profile SHA-256 must match. Use `summarize-gates` after runtime acceptance with all runtime results plus profile-bound external documents for `Per-change Development Validation` and `Release Acceptance`. The development document uses the structured change-group contract in [development-gate.md](development-gate.md); the runner recomputes its verdict and matches any required smoke scenario. The release document continues to require `gate`, `verdict`, `profile_sha256`, and non-empty evidence references. Missing gates or scenarios are `BLOCKED`, and smoke never satisfies final runtime acceptance.
