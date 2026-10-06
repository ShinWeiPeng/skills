# Shared ADR format

## General decisions


ADRs live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.


## Template

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

That's it. An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why* — not in filling out sections.

## Optional sections

Only include these when they add genuine value. Most ADRs won't need them.

- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`) — useful when decisions are revisited
- **Considered Options** — only when the rejected alternatives are worth remembering
- **Consequences** — only when non-obvious downstream effects need to be called out



## Architecture decision profile

Applies when architecture governance requires an exception or durable architecture choice.

1. Status: `proposed`, `accepted`, `rejected`, or `superseded`.
2. Context and problem.
3. Decision.
4. Alternatives considered.
5. Benefits, costs, and tradeoffs.
6. Risks and mitigations.
7. Compatibility and migration impact.
8. Validation and observable pass conditions.
9. Approval: approver identity, date, and external approval reference.
