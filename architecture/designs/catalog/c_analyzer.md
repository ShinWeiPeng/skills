# CAT-c_analyzer

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-c_analyzer |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: c_analyzer
value:
  ast:
    status: not-applicable
    rationale: The governed integration contains prompts, JSON contracts, and Python
      tooling but no production C or C++ translation units.
  functional_boundary:
    status: not-applicable
    rationale: The plugin has no C or C++ framework boundary.
    forbidden_includes: []
    forbidden_symbols: []
  forbidden_public_includes: []
  forbidden_public_symbols: []
  forbidden_source_symbols: []
```
