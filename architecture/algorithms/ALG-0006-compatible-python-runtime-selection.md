# ALG-0006: Compatible Python runtime selection

## Metadata

- Status: accepted
- Owner module: `python_runtime_selection_domain`
- Product feature: Windows one-click Plugin installation
- Flow IDs: `local-plugin-installation`
- Related ADRs: `architecture/decisions/ADR-0013-continuous-stable-plugin-versioning.md`
- Source paths:
  - `scripts/python-runtime-selection-policy.ps1`
  - `scripts/python-runtime-selection.ps1`
- Test and benchmark paths:
  - `plugins/governed-engineering-skills/tests/test_install_local.ps1`
- Supersedes: none

## Problem and observable success

Windows may resolve a `python` command that exists but is too old to parse the
Plugin assembler. The installer must select one Python 3.11-or-newer interpreter
before any artifact mutation, use that same interpreter throughout the local
installation flow, and replace raw syntax failures with bounded recovery guidance.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are an optional explicit Python command, the first PATH `python`
application, and the Windows Python Launcher's highest Python 3 runtime. A
side-effect-free probe returns major, minor, micro, and `sys.executable` values.
The accepted range is `major > 3` or `major == 3 and minor >= 11`.

The output is one validated absolute interpreter path or a fail-closed diagnostic
listing the candidates and versions observed. Probe output is untrusted until its
marker, integer version fields, executable path, exit status, and minimum version
all validate.

## Constraints and quantitative acceptance thresholds

- Python 3.11 is the minimum accepted runtime.
- Explicit `-PythonCommand` is authoritative and never silently replaced.
- Automatic discovery checks compatible PATH Python before the Windows Launcher.
- The selected absolute interpreter performs assembly, distribution validation,
  and cache localization.
- Failure occurs before `dist` mutation or Codex invocation.

## Candidate methods and comparative evidence

1. **Accept any PATH `python`:** rejected because command existence did not prevent
   the observed Python syntax failure.
2. **Fail immediately after an old PATH Python:** safe but rejected because it
   breaks one-click installation when a compatible Python is already registered
   with the Windows Launcher.
3. **PATH-first validation with Windows Launcher fallback:** selected because it
   preserves intentional PATH configuration and recovers from stale PATH entries
   without downloading software.
4. **Download or bundle Python:** rejected because it adds network, package trust,
   update, security, and rollback responsibilities outside this installer.

## Selected method and reasons for rejecting alternatives

Validate an explicit command when supplied. Otherwise probe PATH `python`; accept
it only at Python 3.11+. If it is absent, malformed, non-executable, or older,
invoke `py -3` only as a discovery mechanism, obtain its `sys.executable`, then
validate and normalize that executable before use. If every candidate fails,
return the prerequisite diagnostic without entering assembly.

## Exact behavior, formula or pseudocode, boundaries, and tie-breaking

```text
if explicit command exists:
    selected = validate(explicit)
    fail if invalid
else:
    selected = validate(first PATH python)
    if invalid:
        launcher_result = probe(first PATH py with -3)
        selected = validate(absolute launcher_result.sys_executable)
    fail if invalid

run assemble, validate, and localize with selected.absolute_path
```

PATH wins only when compatible. The Windows Launcher supplies its own highest
Python 3 runtime; the installer does not rank individual installed versions.

## Parameters, calibration, versioning, and compatibility

The minimum version is the governed installer contract, not a user preference.
The probe syntax remains parseable by Python 2 so old runtimes can be identified
and rejected cleanly. Python 2 is never an execution runtime. The change ships as
the next immutable patch after `0.7.3`.

## Time and space complexity and resource budgets

Selection performs at most three bounded synchronous probes and retains only their
short diagnostic output. There is no persistent state, queue, retry loop, or
product timing budget. Stronger benchmarking cannot change the compatibility
decision for this best-effort user-launched flow.

## Errors, degradation, fallback, and forbidden behavior

- Malformed output, a non-zero exit, a missing executable, or Python below 3.11
  rejects that candidate.
- An invalid explicit command fails directly because explicit injection is
  authoritative.
- An invalid automatic PATH candidate degrades to the Windows Launcher.
- No compatible runtime fails before artifact or Codex side effects.
- Never download Python, accept Python 2/3.10, or probe with syntax those runtimes
  cannot parse.

## Validation cases and evidence

- Compatible explicit Python remains authoritative.
- Compatible PATH Python wins without invoking the launcher.
- A Python 3.10 PATH candidate falls back to compatible `py -3`.
- An explicitly supplied Python 2.7 candidate is rejected before artifact mutation.
- Launcher output resolves to an absolute runtime that performs all three Python
  phases.
- Malformed, non-executable, missing, and below-minimum candidates fail before the
  assembly sentinel and produce actionable logs.
- The complete Windows installer contract suite proves installation, reinstall,
  failure recovery, and exact installed-tree behavior remains intact.

The executable contract is
`powershell -NoProfile -ExecutionPolicy Bypass -File plugins/governed-engineering-skills/tests/test_install_local.ps1`.

## Risks and monitoring

Windows Launcher availability and output behavior vary by machine. Tests cover
absence, malformed responses, stale PATH, explicit override, and actual absolute
runtime use. Future minimum-version changes must update the Spec, this record,
diagnostics, and fixtures together.

## Human approval

- Approved by: Hugo Peng
- Approval date: 2026-08-14
- Approval reference: `SPEC-0013` / `DISC-021`
