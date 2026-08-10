# Per-change Development Validation contract

Gate 1 is a host-side development gate. Run unit, behavior, integration, protocol, schema, static, Fake Port, and host contract tests with the project's native test tools. Do not use the on-device runner to flash a device, capture `VAL_*` logs, or ask a user to upload logs for these ordinary checks. Assertions and process exit codes determine each check verdict; Codex records structured evidence.

Pass one or more Gate 1 documents to `summarize-gates` together with the runtime and release results:

```yaml
schema_version: "1.0"
gate: Per-change Development Validation
profile_sha256: <current-profile-hash>
source_revision: <commit-or-worktree-snapshot-id>
change_groups:
  - id: control-domain-clock-change
    architecture_refs: [control_domain, control.clock]
    risks: [timeout-calculation, event-ordering]
    checks:
      - id: control-domain-unit
        kind: unit
        test_boundary: FakeClockPort
        command:
          executable: <test-runner>
          args: [<argument>]
        exit_code: 0
        verdict: PASS
        evidence:
          - path: <result-file>
            sha256: <64-digit-hex-digest>
    on_device_smoke:
      required: false
      reason: Functional calculation changed; hardware adapter and timing wiring are unchanged.
verdict: PASS
```

Every change group requires a unique ID, non-empty architecture references, risks, checks, and an explicit smoke decision. Every check requires a unique ID, kind, test boundary, executable plus argv, integer exit code, PASS/FAIL/BLOCKED verdict, and one or more path/SHA-256 evidence references. PASS requires exit code zero. The runner recomputes each change group and the Gate 1 verdict with `FAIL > BLOCKED > PASS`; a mismatched author-supplied verdict blocks the document.

When a target profile points to an architecture manifest, `summarize-gates` identifies L3+ Adapter module IDs and Ports implemented by those Adapters. A change group referencing one of those IDs must contain `kind: port-contract`. Use the demand-owned Port contract suite against the applicable Fake, Simulator, and Real Adapter implementations. Internal Ports remain risk-based.

For a required smoke, add the declared profile scenario ID:

```yaml
on_device_smoke:
  required: true
  reason: HardwareTimerAdapter and interrupt timing changed.
  scenario: timer-smoke
```

Supply that scenario's separate `phase: smoke` result to `summarize-gates`. The profile hash and scenario ID must match. Missing smoke is BLOCKED; FAIL or BLOCKED smoke propagates into Gate 1. Smoke is supporting evidence only and never satisfies Final Runtime Acceptance.
