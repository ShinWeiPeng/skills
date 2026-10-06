# CAT-source_sets

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | CAT-source_sets |
| version | 1 |
| kind | catalog |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_field: source_sets
value:
- id: repository-production
  classification: production
  include:
  - skills/engineering/**
  - skills/productivity/**
  - scripts/assemble_plugin.py
  - scripts/install-local.ps1
  - scripts/install-marketplace.ps1
  - scripts/install-marketplace.sh
  - scripts/python-runtime-selection-policy.ps1
  - scripts/python-runtime-selection.ps1
  - scripts/windows-artifact-access.ps1
  - scripts/validate_distribution.py
  - distribution/**
  - validation/verification-ladder.yaml
  - validation/layout.yaml
  - plugins/governed-engineering-skills/**
  - plugins/governed-engineering-skills/.codex-plugin
  - plugins/governed-engineering-skills/.codex-plugin/**
  exclude:
  - skills/**/tests/**
  - skills/**/tools/**
  - skills/**/architecture/generated/**
  - skills/**/__pycache__/**
  - tests/flows/plugin-integration/plugin/**
  purpose: Govern the authoritative promoted Skills, tracked Plugin shell, deterministic
    assembly, local Codex installation, compatibility inventory, and optional Git
    Marketplace publication.
  provenance: Human-maintained repository sources assembled into one Plugin artifact.
- id: generated-tool-mirrors
  classification: generated-production
  include:
  - skills/engineering/**/tools/**
  - skills/productivity/**/tools/**
  exclude: []
  purpose: Distribute project-local mirrors generated from canonical skill tooling.
  provenance: Bootstrap-owned copies of canonical skill scripts.
  generator: governed bootstrap tool mirror
  owner: integration_validation_technical
- id: repository-development
  classification: development
  include:
  - tests/**
  - tools/**
  exclude: []
  purpose: Test source and support follow dedicated ownership and dependency rules.
  provenance: Repository-owned Module and Flow tests and development tooling.
- id: repository-derived-docs
  classification: derived-documentation
  include:
  - architecture/generated/**
  - skills/**/architecture/generated/**
  exclude: []
  purpose: Keep deterministic architecture views outside formal product sources.
  provenance: Architecture renderers.
- id: plugin-build-output
  classification: build-output
  include:
  - build/**
  - dist/**
  - .cache/**
  - .codex-arch-deps/**
  - node_modules/**
  - .ruff_cache/**
  - .tmp/**
  - .test-tmp/**
  - plugins/governed-engineering-skills/build/**
  - plugins/governed-engineering-skills/.tmp/**
  - '**/__pycache__/**'
  exclude: []
  purpose: Exclude generated runtime and validation caches.
  provenance: Python and local build tools.
```
