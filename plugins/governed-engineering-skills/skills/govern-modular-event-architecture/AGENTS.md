# Architecture governance

Before changing architecture, named types, runtime state, modules, dependencies, ports, callbacks, or events:

1. Read `architecture/manifest.yaml`, `architecture/ARCHITECTURE.md`, accepted ADRs, and the baseline if present.
2. Before editing source, build the Boundary Design Table, Type Ownership Matrix, State Object Ownership Matrix, actual/intended dependency edges, and parent mappings.
3. Validate the planned manifest. An unresolved owner, authority, dependency, or mapping is `BLOCKED`.
4. Preserve every schema 1.0 through 2.0.1 requirement under schema 2.0.2.
5. Do not mark an ADR accepted without explicit user approval.
6. Update governance files, source, and tests together.
7. Treat `architecture/manifest.yaml` as the only editable description source. Do not hand-edit generated Architecture Description Views.
8. Use schema 2.0.2 and describe logical source sets, modules, ports, events, named types and references, state objects, boundary mappings, source paths, symbols, L0/L1 flows, workloads, execution profiles/units/channels, data access, and microarchitecture profiles. Then run `tools\architecture\render_architecture.py --manifest architecture\manifest.yaml --write`.
9. For C/C++, require pinned libclang, a complete compilation database and target, all governed translation units, and AST PASS. Lexical scanning alone is not PASS.
10. Run the project architecture checker and applicable language analyzers.

Use this command on Windows:

```powershell
python tools\architecture\check.py --manifest architecture\manifest.yaml --format text
```

Treat exit `0` as pass, `1` as a MUST violation, and `2` as `BLOCKED` because configuration, capability, coverage, or parse evidence is incomplete.

Use `tools\architecture\render_architecture.py --manifest architecture\manifest.yaml --check` in CI. The checker also rejects missing, changed, or obsolete generated pages.

For an existing project, also pass `--baseline architecture\baseline.yaml`. In CI, export the target branch's baseline to a temporary file and pass it as `--previous-baseline`; baseline growth is forbidden.
