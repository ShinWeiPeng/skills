# Architecture governance

Before changing architecture, named types, runtime state, modules, dependencies, ports, callbacks, or events:

1. Read `architecture/manifest.yaml`, `architecture/adoption.yaml`, `architecture/ARCHITECTURE.md`, accepted ADRs, and the baseline if present.
2. Before editing source, build the Boundary Design Table, Type Ownership Matrix, State Object Ownership Matrix, actual/intended dependency edges, and parent mappings.
3. Validate the planned manifest. An unresolved owner, authority, dependency, or mapping is `BLOCKED`.
4. Preserve every schema 1.0 through 2.0.2 requirement under schema 2.1.0.
5. Do not mark an ADR accepted without explicit user approval.
6. Update governance files, source, and tests together.
7. Treat `architecture/manifest.yaml` as the only editable description source. Do not hand-edit generated Architecture Description Views.
8. Use schema 2.1.0 and describe logical source sets, composition roots, modules, ports, events, named types and references, state objects, boundary mappings, source paths, symbols, L0/L1 flows, workloads, execution profiles/units/channels, workload-driven real-time scheduling studies, data access, microarchitecture, validation profiles, and assurance scope. Then run `python tools\architecture\architecture_cli.py render`.
9. For C/C++, require pinned libclang, a complete compilation database and target, all governed translation units, and AST PASS. Lexical scanning alone is not PASS.
10. Run every gate through the single `architecture_cli.py`; legacy checker, renderer, bootstrap, and analyzer scripts are internal and cannot be invoked directly.
11. Remediate discovered legacy violations by default. Use a temporary baseline only for exact, unexpired, non-AI-approved deferrals; Release requires a zero-entry baseline.

Use this command on Windows:

```powershell
python tools\architecture\architecture_cli.py gate --phase development --manifest architecture\manifest.yaml --adoption architecture\adoption.yaml --baseline architecture\baseline.yaml --format text
```

Treat exit `0` as pass, `1` as a MUST violation, and `2` as `BLOCKED` because configuration, capability, coverage, or parse evidence is incomplete.

Use `python tools\architecture\architecture_cli.py gate --phase release` in CI. The single gate rejects incomplete AST coverage, temporary baseline debt, and missing, changed, or obsolete generated pages.

## Plugin version governance

- Read `docs/versioning.md` before changing the plugin version or release stage.
- Keep `package.json`, `.codex-plugin/plugin.json`, `CHANGELOG.md`,
  `.changeset/release-state.json`, and the production fingerprint consistent.
- Use `python scripts/version_governance.py check` for formal CI validation.
- MAJOR and MINOR releases pass through beta and RC. High-risk PATCH releases
  pass through RC; only low-risk PATCH releases may go directly to stable.
- Stable promotion requires final-RC fingerprint equality, reinstall and
  new-task evidence, no open blockers, and explicit non-AI approval.
- A `+codex.local-*` cachebuster is local-only and must never be committed as a
  formal release version.

For an existing project, also pass `--baseline architecture\baseline.yaml`. In CI, export the target branch's baseline to a temporary file and pass it as `--previous-baseline`; baseline growth is forbidden.
