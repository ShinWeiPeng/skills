# Governed entry gate

Before mutation or external action:

1. Inspect the task and invoke `$engineering-risk-routing`.
2. Preserve its risk class, matched hard triggers, required gates, status, and return target.
3. Stop with `BLOCKED` when a required skill is unavailable or a required gate lacks valid PASS evidence.
4. For R2/R3 work, do not mutate before `clarify-improvement-proposals` and `govern-modular-event-architecture` have passed. Existing projects without supported governance first require an as-is inventory and baseline.
5. Route physical-device or OS-native evidence only through `validate-on-device`. Builds and ordinary logs are not substitutes.
6. Respect the repository's authorization boundary. Diagnosis, planning, and review do not imply permission to fix, commit, push, publish, or perform destructive actions.

When returning to the original workflow, carry the `RoutingDecision` and all `GateResult` evidence forward.
