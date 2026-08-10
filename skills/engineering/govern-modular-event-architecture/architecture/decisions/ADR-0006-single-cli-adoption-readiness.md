# ADR-0006: Single governance CLI and release-zero adoption policy

- Status: proposed
- Date: 2026-07-31
- Approver: pending
- Approval reference: pending

## Context

An empty legacy baseline could appear complete while composition-root,
Type/State Catalog, analyzer, and generated-view evidence remained incomplete.
Separate public commands also allowed a partial check to be mistaken for the
complete governance gate.

## Decision

- Schema 2.1.0 declares one verified release composition root.
- `architecture_cli.py` is the only public CLI; legacy script entrypoints fail.
- Design, development, and release are distinct gate phases.
- Development recognizes only exact, unexpired, non-AI-approved temporary
  deferrals; Release requires zero temporary baseline entries.
- Durable exceptions require accepted ADRs.
- Adoption Markdown/JSON is generated from authoritative inputs and current
  analyzer evidence.
- Tool-host OS/Python evidence is separate from target Execution Profiles.

## Alternatives considered

Multiple public commands preserve compatibility but cannot guarantee complete
gate execution. An empty baseline is not source-coverage evidence. Indefinite
release debt would hide policy exceptions outside ADR review.

## Consequences

All repository CI and documentation migrate immediately because schema 2.1.0
is unpublished. Internal modules remain importable but are not public CLIs.

## Validation

Tests cover phase dispatch, legacy-command rejection, baseline policy, Python
AST coverage, deterministic adoption documents, bootstrap, and release gates.

## Approval

Pending human approval. Codex must not mark this ADR accepted.
