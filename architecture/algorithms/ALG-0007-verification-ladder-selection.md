# ALG-0007: Verification ladder selection

## Metadata

- Status: proposed
- Owner module: `verification_ladder_domain`
- Product feature: Module-contract verification planning and evidence authority
- Flow IDs: `verification-ladder-planning`
- Related ADRs: none
- Source paths:
  - `skills/engineering/verification-ladder/scripts/verification_ladder.py`
  - `skills/engineering/verification-ladder/references/verification-ladder.schema.json`
- Test and benchmark paths: `skills/engineering/verification-ladder/tests/test_verification_ladder.py`
- Supersedes: none

## Problem and observable success

Select the lowest sufficient additive verification layers for a change without
letting host, controlled-target, or integrated-hardware evidence claim authority it
does not have. Success is a deterministic ordered plan, or `BLOCKED` with every
missing or stale mapping identified.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are a versioned project matrix, stable IDs from the governed architecture
manifest, scenario and execution-profile IDs from `validation/on-device.yaml`, and
sets of affected contract dimensions, execution/environment changes, and evidence
claims. Outputs are an ordered layer set, activated rule IDs, evidence-authority
requirements, and diagnostics. IDs are exact case-sensitive strings; project rates,
batch sizes, durations, time units, throughput, latency, RAM, and other thresholds
remain opaque project-authored criteria rather than universal constants.

## Constraints and quantitative acceptance thresholds

All requested trigger values must belong to the stable taxonomy and match at least
one project rule. All referenced architecture and on-device IDs must resolve
uniquely. Each selected layer must define scope, inputs, metrics, explicit
PASS/FAIL/BLOCKED thresholds, an evidence artifact, a stop condition, and the next
permitted layer. Any violation returns `BLOCKED`.

## Candidate methods and comparative evidence

- A fully fixed cross-project matrix is deterministic but incorrectly embeds
  platform-specific topology and thresholds.
- A fully project-defined matrix is flexible but can omit evidence-authority risks.
- The selected hybrid keeps universal taxonomy, hard triggers, ordering, and
  non-substitution rules in the skill while projects own bindings, thresholds,
  scenarios, and explicit non-applicability rationale.

The hybrid was selected in `SPEC-0018` after explicit user comparison.

## Selected method and reasons for rejecting alternatives

Normalize each requested trigger set, reject unknown values, activate every project
rule that intersects a requested trigger category, and union its layers with the
universal hard-trigger layers. Preserve canonical layer order. Reject any requested
trigger that activates no rule, any unresolved reference, and any claim whose
observed evidence layer is below its authority layer. This keeps project policy
additive without allowing it to weaken universal evidence boundaries.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

1. Parse and structurally validate the matrix and referenced documents.
2. Resolve every declared architecture, scenario, and profile reference exactly
   once.
3. For each requested trigger, find all matching project rules; zero matches blocks.
4. Compute `required = union(universal(trigger), rule.layers)`.
5. Sort by `module-contract`, `sil`, `adapter-contract`, `pil`, `hil`,
   `system-soak`; ordering never removes a layer.
6. When evidence is assessed, require the claim's authoritative layer to be present
   and passed; lower layers may remain supporting evidence only.

There is no score or tie-breaking winner because all activated layers are additive.

## Parameters, calibration, versioning, and compatibility

The matrix schema is versioned independently. Platform names, architecture IDs,
thresholds, and on-device scenarios are project-owned. Example sensor rates, batch
sizes, pairing rules, processor counters, and durations are never defaults.

## Time and space complexity and resource budgets

Validation and planning are linear in matrix rules plus referenced IDs and requested
triggers. Inputs are bounded repository configuration files; no runtime target RAM,
latency, or throughput claim is made by this host-side planner.

## Errors, degradation, fallback, and forbidden behavior

Malformed YAML, unknown taxonomy values, duplicate IDs, unresolved or stale
references, incomplete layer contracts, unmapped triggers, and lower-layer evidence
substitution are `BLOCKED`. The planner never guesses a target, invents a threshold,
silently marks a layer not applicable, executes device scenarios, or rewrites a
project's production Processing implementation.

## Validation cases and evidence

Behavioral tests cover host-only and target-platform fixtures, additive trigger
selection, different project bindings under one taxonomy, malformed and stale
references, duplicate ownership, unmapped claims, production-code SIL declarations,
Adapter contract suites, and PIL/HIL/System-Soak evidence authority. Distribution
and architecture gates verify integration.

## Risks and monitoring

The main risk is taxonomy drift between skill instructions, schema, and evaluator.
Contract tests use the same realistic fixtures through the public CLI and require
unknown values to fail closed. Project-specific evolution occurs in matrix rules,
not by adding platform examples to universal policy.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: `SPEC-0018`
