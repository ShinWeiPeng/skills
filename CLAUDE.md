# Skills monorepo

- `governed-engineering-skills/` owns the existing engineering package, canonical promoted Skill sources, installers, assembly, version metadata and tests. Read its `AGENTS.md` and `CLAUDE.md` before changing it.
- `doc-coauthoring/` owns the standalone dual-platform documentation package when present.
- Root `.github/`, `release-packages.json`, marketplace catalogs, architecture, validation and canonical specifications coordinate packages. Do not create nested Git repositories or duplicate editable Skill trees.
- Each package has its own changesets, changelog, Version PR branch, immutable version tags and generated consumer branch. A version operation stages only its declared package root.
- Root installers and script entrypoints are compatibility delegates, not second implementations.
- Preserve existing user work and untracked data. Stage explicit reviewed paths; do not use repository-wide `git add -A`. Generated consumer branches are never editable source.

Cross-package tests: `python -m unittest discover -s tests/flows/plugin-integration/monorepo -p "test_*.py" -v`. Engineering assembly: `python governed-engineering-skills/scripts/assemble_plugin.py rehearse`.
