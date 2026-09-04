---
name: formatter-governance
description: Select, verify, and report repository-aware formatter policy before modifying engineering work. Use for greenfield formatter defaults, existing-project style preservation, safe scaffold preflight, formatter checks, and format-write authorization.
---

# Formatter Governance

Own one formatter decision for the whole change set. The delivery workflow invokes
this skill after the canonical specification verifies and before a test or product
source is authored. A `BLOCKED` verdict stops that handoff.

## Establish the policy

Use the ProjectState evidence already captured by `ask-matt`; do not infer a new
state merely because spec or architecture files were created later.

- For `absent / absent`, run `scripts/formatter_policy.py select` with the primary
  language. The command reads the sole governed mapping from
  [references/formatter-policy.json](references/formatter-policy.json).
- For a non-greenfield project, inspect formatter configuration, dependency and
  build metadata, contributor docs, CI, and existing format scripts. Preserve the
  discovered repository formatter, style, file scope, and invocation. Pass the
  formatter identity separately from JSON `check` and `write` argv arrays; never
  combine a command into the identity or replace it with a governed default.
- If either ProjectState axis or the applicable repository convention is
  indeterminate, report `BLOCKED`; do not guess.

Keep check and write commands distinct. A check must be non-mutating. A formatting
write requires the user's repository-mutation authorization and may touch only the
declared target root and file scope.

## Preflight greenfield scaffold

Resolve the exact project root before generating anything. Enumerate every intended
scaffold path and run `scripts/formatter_policy.py preflight`. Treat the command as
read-only evidence; it never creates files.

Only after a PASS may the workflow create package or build metadata, directory
skeletons, formatter dependency declarations and configuration, and unavoidable
generator boilerplate. Use create-only operations. Never merge through an existing
path, pass a force-overwrite option, follow a path outside the resolved root, or
repeat the project name beneath that root. Minimal scaffold contains no product
behavior.

Installing or downloading a formatter is an external mutation. Request explicit
authorization through the native permission boundary immediately before it. A
missing or declined authorization is `BLOCKED`, not permission to substitute a
different formatter.

## Gate product mutation

After minimal scaffold and before product behavior:

1. Verify the selected formatter executable and version in the intended project
   environment.
2. Run the policy's non-mutating check command at the exact root. For command
   templates containing `<files>`, replace it with an explicit, reviewed file list;
   never pass an unexpanded placeholder or an unrelated tree.
3. Hash the formatter's declared file scope before and after the check. Treat a
   changed hash, nonzero exit, missing output semantics, or, for
   `gofmt -l`, non-empty stdout as a failed check.
4. Run `scripts/formatter_policy.py gate --operation product-code` with the exact
   project root, project kind, selected formatter, prior selection/preflight
   statuses, observed availability, and check status. Greenfield work requires both
   prior statuses to be PASS; existing work uses `not-applicable` for preflight.
   Continue only on PASS.

Use `--operation minimal-scaffold` only with greenfield selection PASS and scaffold
preflight PASS. It never authorizes product code. Formatter installation/download requests also pass
`--install-requested`; omit `--install-authorized` until native authorization was
actually granted.

## Evidence

Report the resolved root, original ProjectState and evidence, project kind,
language, selected formatter and policy source, exact check argv and file scope,
tool version, exit code, bounded stdout/stderr, scaffold paths, collision hashes,
permission outcome, and final `PASS` or `BLOCKED`. For an authorized formatting
write, also report the exact write argv and changed paths.

The JSON policy is the only governed language-to-formatter mapping. Routing, TDD,
implementation, review, docs, and manifests may invoke this skill but must not copy
that table.
