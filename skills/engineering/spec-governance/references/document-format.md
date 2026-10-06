# Document format version 1

## SPEC collection

`specs/SPEC-####-name.md` contains canonical metadata, summary and entry sections, prefixed with `<!-- document-bundle:1 -->`. Its sibling directory holds `requirements.md`, `acceptance.md`, `discussion.md` and `references.yaml`. The SPEC owner alone reconstructs the ordered canonical projection; readers do not parse just the entry file.

`references.yaml` has exactly `format_version: 1`, `canonical`, ordered `sections` records (`section`, `path`) and fixed `designs` records (`id`, positive integer `version`, portable project `path`, lowercase SHA-256 `sha256`). Section ownership is fixed by `document_bundle.PARTS` and `MAIN`; undeclared, duplicate or missing sections are errors. All existing REQ/DEC/AC/DISC tables and audit events keep their existing contracts.

## Design documents

Each design has `## Identity` containing one `Field | Value` table with `format_version`, `id`, `version`, `kind`. Version is positive; kind is platform, execution, module, interface, flow or catalog. `## Design Data` contains exactly one `<!-- design-data:1 -->` marker and one YAML block.

Identity fields have no duplicate YAML representation. Nested and conditional data belongs in that block. Duplicate keys/IDs, unknown format versions, non-text keys, non-finite numbers, unquoted dates, malformed references and unsupported shapes fail with the source location. Values keep their project's defined units; domain formats define required keys and units. An `unknown` fact retains a reason and cannot substitute for not-applicable or measured evidence.

Current files live in `architecture/designs/{platform,execution,modules,flows,catalog}/`. The maintained index lists each source exactly once. `architecture/history/` is immutable; `specs/SPEC-####/candidates/` is the affected change-set workspace. Confirmed SPEC references pin immutable versions; candidates never modify the current version before authorized application. Generated manifest and views are not second editable sources.

Platform Facts has fixed Field/Status/Value/Unit/Basis/Reason columns. Execution Units has ID/Kind/Responsibility/Call environment columns. Resource Inventory has ID/Kind/Quantity/Unit/Owner/Basis columns. Exact lowercase field names are declared in design_table_format.TABLES; typed cells use JSON scalars, and nested references remain only in Design Data YAML. Duplicate table/YAML owners and malformed cells fail with a table/row location.

Entry links between document-navigation markers are generated navigation and excluded from the authored projection. Candidate staging captures an immutable `BASE-<ID>` catalog in the same fixed collection. It owns candidate ID/version, current source path and an exact base ID/version/path/hash (null only for a new design). Formal application compares this captured baseline, including bytes, before any effect. Historical references remain readable; governed product writes separately require current dependent design versions.
