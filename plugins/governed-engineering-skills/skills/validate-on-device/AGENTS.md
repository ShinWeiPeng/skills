# Architecture governance

Before changing architecture, modules, dependencies, ports, callbacks, or events:

1. Read `architecture/manifest.yaml`, `architecture/ARCHITECTURE.md`, accepted ADRs, and the baseline if present.
2. State the architecture impact and required manifest or ADR changes.
3. Preserve L0-L3+ responsibilities, demand-owned ports, parent-coordinated siblings, and event contracts.
4. Do not mark an ADR accepted without explicit user approval.
5. Update governance files, source, and tests together.
6. Treat `architecture/manifest.yaml` as the only editable description source. Do not hand-edit generated Architecture Description Views.
7. For schema 1.1, describe modules, ports, events, source paths, symbols, and L0/L1 flows; then run `tools\architecture\render_architecture.py --manifest architecture\manifest.yaml --write`.
8. Run the project architecture checker and applicable language analyzers.

Use this command on Windows:

```powershell
python tools\architecture\check.py --manifest architecture\manifest.yaml --format text
```

Treat exit `0` as pass, `1` as a MUST violation, and `2` as a configuration or tool error.

Use `tools\architecture\render_architecture.py --manifest architecture\manifest.yaml --check` in CI. The checker also rejects missing, changed, or obsolete generated pages.

For an existing project, also pass `--baseline architecture\baseline.yaml`. In CI, export the target branch's baseline to a temporary file and pass it as `--previous-baseline`; baseline growth is forbidden.
