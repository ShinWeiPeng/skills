# Project-bound validation

The existing verification-ladder skill owns this protocol; no new skill is installed.

The guided router rereads architecture/adoption.yaml, architecture/manifest.yaml,
validation/verification-ladder.yaml and validation/on-device.yaml. Each file has a
presence/validity state and SHA-256. Keyword routing adds to project requirements.
Unknown obligations block dependent acceptance rather than becoming exemptions.

## AC mapping and plan

Store `validation/acceptance-SPEC-####.json` using
[project-validation.schema.json](project-validation.schema.json). Map every AC to
evidence_claims, optional contract_dimensions/execution_changes, and a rationale.
For selected device layers, map scenario_layers to the activated matrix scenarios,
declare the current build_artifact, and copy enablement_scenarios from the profile's
acceptance prerequisites. Only one accepted execution profile may be selected per AC.
Host-only decisions must explicitly explain why their contracts need no device layer.
Formal module `host-semantics` selects module-contract plus SIL. An exemption
based only on "no separate simulated integration" is invalid. Reuse existing
production-module cases, add the missing matrix contract/report, and recompute the
plan explicitly; do not relabel or mutate historical results.
Legacy host projects without validation policy/matrix retain their host behavior;
missing governed mappings require explicit migration and cannot provide hardware PASS.

Run the following public CLI with the confirmed SPEC:

```powershell
python skills/verification-ladder/scripts/project_validation.py --project-root <project> --spec specs/SPEC-####-feature.md --write-plan
python skills/verification-ladder/scripts/project_validation.py --project-root <project> --spec specs/SPEC-####-feature.md --phase enablement
python skills/verification-ladder/scripts/project_validation.py --project-root <project> --spec specs/SPEC-####-feature.md --phase acceptance
```

In the source checkout the skill lives under skills/engineering/verification-ladder.
The generated plan is artifacts/validation/<run-id>/plan.snapshot.json. It binds exact SPEC
bytes/revision, relevant source documents and selected skill code/version. Recompute
after changes, retain historical evidence, and do not silently rebind old results.
Unchanged recomputation is deterministic and does not mutate execution authorization.

## Evidence bundle

Store artifacts/validation/<run-id>/evidence.json with schema_version=1, plan_sha256 and a
results array. Each row names ac, layer, scenario (null for host), purpose
(enablement, acceptance or release), verdict, complete, and artifacts. Each artifact
has a project-relative path and SHA-256. Device rows additionally bind
execution_profile and build_sha256, and reference a runner_result artifact from
validate-on-device. The runner verdict, scenario, phase and canonical profile hash
must agree. Preserve raw/native trace artifacts where required by that runner.

All selected layers and their scenario mappings must pass; higher layers do not
silently replace lower-layer requirements. Smoke cannot serve as acceptance.
Required enablement must pass before implementation admission; final device evidence
is required at completion rather than preventing implementation that produces it.
Release assessment also requires separate release results; runtime acceptance alone
never proves release wiring or stability. The actual native runner retains ownership
of criterion evaluation and raw evidence integrity.

Managed delivery accepts operation=complete with phase=acceptance or release and the
same task/SPEC/working reference. SPEC lifecycle tools run the same assessment before
writing AC PASS, including a confirmed evidence-only update. An unchanged host test
result remains valid host evidence but cannot approve a physical claim.

## Trust and limits

The packet and artifacts are caller-supplied, not authenticated observations.
Hashes detect mismatches, not fabricated inputs. The managed paths enforce these
checks; arbitrary model prose, manual edits and out-of-band tools are not intercepted.
No validation assessment grants device-operation permission.

## Composed project validation entrypoint

For a governed project, run existing commands through the composition wrapper so
the demand-owned validation callable is injected:

```powershell
python skills/implement/scripts/project_validation_workflow.py spec -- <spec_contract arguments>
python skills/implement/scripts/project_validation_workflow.py managed -- --project-root <root> --request <request.json>
python skills/implement/scripts/project_validation_workflow.py admission -- <spec_delivery arguments>
```

Use skills/engineering/implement in a source checkout. This is an internal CLI,
not a new skill. Library callers pass validation_assessor explicitly. Without it,
direct governed library/CLI calls fail closed with a remediation message; legacy
host projects with no governance markers retain their previous behavior.

Device release rows reference the original native `phase=acceptance` PASS result;
the native runner does not have a release phase. They additionally name a distinct
hashed release_report with gate `Release Acceptance`, plan_sha256, build_sha256,
verdict and checks: test_only_wiring_absent, release_build, regression, architecture,
analyzer, size and safety. Each check is PASS/FAIL/BLOCKED; recompute the report verdict
with FAIL > BLOCKED > PASS. Preserve the supporting release-check artifacts alongside
the report. Release does not relabel the native runtime result.

## Fixed run selection

`--write-plan` exclusively allocates a run, publishes its terminal manifest and
returns its fixed path. `validation/run-references-SPEC-####.json` is an authored
selection with schema_version=1, plan_manifest and evidence_manifests. Plan renewal
explicitly clears previous evidence selection; it does not mutate any old run.
Every consumer validates the selected manifests, identity, exact file set and
hashes. Evidence rows must belong to that run and terminal outcome must agree with
the rows. No newest-file lookup or historical evidence rebind is permitted.

The composed router/delivery adapter also reports the whole-project layout gate.
Planning and enablement may authorize remediation of existing layout debt; they
do not claim overall compliance. Acceptance and release require layout PASS.


## Executed module SIL report

Use [sil-execution.schema.json](sil-execution.schema.json) for the report shape.
Every SIL row references a hashed JSON `runner_result` alongside its captured test
output. The report has `layer: sil`, `ac`, current `plan_sha256`, `verdict`,
`complete: true`, actual argv `command`, integer `exit_code` (zero for PASS) and
nonempty `modules`. Each module identifies an activated architecture module `id`,
nonempty `public_interfaces`, executed `cases`, and `production_sources` containing
project-relative `path` plus SHA-256. `external_dependencies` is an array of
`interface` and `mode` (`fake`, `replay` or `real`); use an empty array if none.
All activated modules must be covered. Production paths must belong to the named
module in the bound architecture manifest; test/fixture or other-module files cannot
substitute for production sources. Preserve production algorithms/state
machines and the original execution output. A plan or a bare PASS log is not an
execution report. Missing, mismatched or stale reports keep acceptance BLOCKED;
complete failed execution remains FAIL. Reports remain caller-attested evidence.

Planning selects layers and leaves `functional_validation_complete: false`. The
planner reports SIL harness/coverage execution requirements with `NOT_RUN`; it does
not probe or certify runner capability. Supply or implement the missing harness
and execute it before claiming functional acceptance.

## SPEC and validation-document input

Canonical SPECs use a dedicated chunked reader: acceptance parsing uses the body
outside the embedded audit, while the plan hash still covers every original byte,
including history. A SPEC is not rejected solely for exceeding 1 MiB or 5 MB.
Malformed audit markers, invalid encoding, nonregular/redirected files and observed
changes during the read remain BLOCKED. The specification owner still verifies
history, sources, evidence and execution authority.

Finite JSON/YAML policy and evidence readers, including run manifests, architecture
owner catalogs and layout evidence, accept at most 5,000,000 bytes (decimal 5 MB).
Oversize diagnostics include the path, observed bytes and limit. This document
policy does not change capture quotas, managed patch limits or hash buffer sizes.
