# C/C++ analyzer

The single `architecture_cli.py gate` dispatches the internal C/C++ analyzer
when the manifest requires it. Direct `c_analyzer.py` invocation is unsupported.
Schema 2.1.0 requires AST evidence; lexical scans are supplemental and cannot
establish an ownership PASS.

## Inputs

- `architecture/manifest.yaml`
- project-local `.c`, `.h`, `.cc`, `.cpp`, `.hpp`, and `.hh` files under declared module paths
- complete `compile_commands.json`, target triple, and every governed translation unit
- pinned `libclang==18.1.1`
- required schema 2.1.0 `source_sets`, `types`, `state_objects`, `type_exclusions`, `boundary_mappings`, `c_analyzer.ast`, and `c_analyzer.functional_boundary`
- optional manifest `c_analyzer.forbidden_public_includes`, `forbidden_public_symbols`, and `forbidden_source_symbols`

## Checks

1. Map source and header files to exactly one declared module.
2. Resolve quoted project-local includes and derive actual module edges.
3. Require every actual edge in `depends_on`.
4. Apply core direction, sibling, adapter, and cycle rules.
5. Scan L0-L2 public contract headers for configured framework includes and symbols.
6. Report file and line for every source diagnostic.
7. Verify every C/C++ entrypoint and public symbol at its declared path.
8. Scan every governed C/C++ source and header for configured forbidden identifiers.
9. Resolve canonical named C/C++ declarations, typedefs, forward declarations, macro-expanded references, and compare kind and shape with the Type Catalog.
10. Scan every L0-L2 source, not only public headers, for configured external-technology includes and symbols.
11. Discover types in excluded vendor/generated paths and reject their use in L0-L2 public contracts.
12. Build the actual named-type reference graph and reject illegal type dependencies with `CTYPE005`.
13. Build state definition and read/write graphs, address escape and pointer passing evidence, public contract exposure, private runtime member dereferences, and function ownership.
14. Fully catalog `production`, parse `generated-production` for boundary evidence, and reject development, derived, or build-output entries in the production compilation database.
15. Report generated mutable globals as `CSTATE007` catalog-only evidence without moving them into the formal State Catalog. Reject access outside the declared L3+ owner.

For an `implemented` module, a missing declared path, source file, or C/C++ symbol is a MUST violation. For a `planned` module, the same absence is a SHOULD warning because the declaration describes intended implementation. Languages without an installed analyzer still require complete declarations and receive an explicit "not verified" warning.

For governed C/C++, the only passing source-evidence mode is `libclang-ast`. `CAST001` blocks missing capability or an invalid AST applicability declaration. `CAST002` blocks missing or invalid compilation database configuration. `CAST003` blocks missing translation units, uncovered headers, and parse failures. These are configuration failures and return exit code `2` / `BLOCKED`; the analyzer never downgrades them to lexical PASS.

`CSTATE001` blocks unregistered or stale production state objects. `CSTATE002` blocks definition path, storage, type, or owner mismatch. `CSTATE003` blocks unauthorized reads. `CSTATE004` blocks unauthorized writes, address taking, or mutable pointer escape. `CSTATE005` blocks private state leaked through `extern`, headers, or public contracts. `CSTATE006` blocks non-owner private-runtime dereference. `CSTATE007` is informational catalog-only generated-state evidence.

Never recommend moving, copying, redeclaring, or hand-editing generated code as remediation. Correct the consumer boundary, source classification, generator template, or owning adapter.

Conservative pointer analysis treats an uncertain mutable address passed outside owner-controlled operations as escape. An opaque handle passes only when the complete representation remains private and callers can operate on it solely through owner APIs.

## AST configuration

```yaml
c_analyzer:
  ast:
    status: required
    rationale: "Governed C/C++ code requires source-level ownership evidence."
    compilation_database: "compile_commands.json"
    target_triple: "arm-none-eabi"
```

Projects with no governed C/C++ translation units declare `status: not-applicable` and a rationale. A project with C/C++ source cannot use that status.

## Functional boundary configuration

Projects with governed C/C++ L3+ sources configure at least one external-technology include or symbol marker:

```yaml
c_analyzer:
  functional_boundary:
    status: configured
    rationale: "STM32 GPIO is implemented only by gpio_adapter."
    forbidden_includes: ["stm32f10x.h"]
    forbidden_symbols: ["GPIO_SetBits", "GPIO_ReadInputDataBit", "GPIO_TypeDef"]
```

Projects without C/C++ L3+ sources use `status: not-applicable`, empty marker lists, and a non-empty rationale. `CFUN001` and `CFUN002` block marker use anywhere in L0-L2 source even when the manifest incorrectly labels the file as functional.

## Example leakage configuration

```yaml
c_analyzer:
  forbidden_public_includes:
    - "freertos/"
    - "driver/"
  forbidden_public_symbols:
    - "QueueHandle_t"
    - "esp_err_t"
```

Keep this list project-specific; do not assume that every C project uses ESP-IDF or FreeRTOS.

## Source-wide forbidden identifiers

Use `forbidden_source_symbols` for retired types, globals, functions, macros, or
other identifiers that must not reappear anywhere under declared module paths:

```yaml
c_analyzer:
  forbidden_source_symbols:
    - "LegacyIdentity"
    - "LegacyRouteLookup"
```

The values must be a list of non-empty strings. The analyzer performs exact
identifier matching in `.c`, `.h`, `.cc`, `.cpp`, `.hh`, and `.hpp` files. It
checks implementation code and preprocessor directives, but ignores comments,
string literals, and character literals. A match is a blocking `CSRC001`
diagnostic with a project-relative file and line. Invalid configuration is a
tool error with exit code `2`.

This is a lexical check. It does not expand macros, apply conditional
compilation, or prove a product-specific positive semantic invariant. Keep
those behavioral claims in focused project tests.

`CTYPE001` through `CTYPE004` cover missing, stale, mismatched, or leaking type declarations. Generic `TYP001` through `TYP007` diagnostics cover catalog ownership, shape, semantic mixing, mutation/consumer authority, and structured exclusions.
