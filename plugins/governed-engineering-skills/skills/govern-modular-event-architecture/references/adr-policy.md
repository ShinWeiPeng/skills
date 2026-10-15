# ADR exception policy

Use an Architecture Decision Record for a MUST-rule exception or a durable architecture choice with meaningful alternatives.

## Required sections

1. Status: `proposed`, `accepted`, `rejected`, or `superseded`.
2. Context and problem.
3. Decision.
4. Alternatives considered.
5. Benefits, costs, and tradeoffs.
6. Risks and mitigations.
7. Compatibility and migration impact.
8. Validation and observable pass conditions.
9. Approval: approver identity, date, and external approval reference.

## Approval boundary

Codex MAY draft or revise a proposed ADR. Codex MUST NOT:

- mark its own proposal accepted;
- invent an approver or approval reference;
- widen the exception scope beyond the user's decision;
- use one ADR to suppress unrelated rules or paths.

Only apply an exception when the user explicitly approves it. Keep the exception narrow and link the manifest entry to the ADR.

## Versioning

Pin `standard_version` and `schema_version` in every project. For an upgrade, compare rules, identify newly failing checks, propose migrations, obtain approval, and then update the pins. Never make an installed Skill silently reinterpret an older project as a newer standard.

