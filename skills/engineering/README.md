# Engineering

Skills I use daily for code work.

## User-invoked

Reachable only when you type them (Claude Code: `disable-model-invocation: true`; Codex: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).

- **[triage](./triage/SKILL.md)** — Move issues through a state machine of triage roles.
- **[improve-codebase-architecture](./improve-codebase-architecture/SKILL.md)** — Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
- **[setup-matt-pocock-skills](./setup-matt-pocock-skills/SKILL.md)** — Configure this repo for the engineering skills (issue tracker, triage labels, domain doc layout). Run once per repo.
- **[to-spec](./to-spec/SKILL.md)** — Turn the current conversation into a spec and publish it to the issue tracker.
- **[to-tickets](./to-tickets/SKILL.md)** — Break any plan, spec, or conversation into a set of tracer-bullet tickets, each declaring its blocking edges — text in a local file, or native blocking links on a real tracker.
- **[implement](./implement/SKILL.md)** — Build the work described by a spec or set of tickets, driving `/tdd` at pre-agreed seams and closing out with `/code-review` before committing.

## Model-invoked

Model- or user-reachable (rich trigger phrasing so the model can reach for them).

- **[ask-matt](./ask-matt/SKILL.md)** — Automatically route software-engineering requests to the appropriate governed workflow.
- **[grill-with-docs](./grill-with-docs/SKILL.md)** — Interview engineering work when durable project context exists but implementation is absent.
- **[clarify-improvement-proposals](./clarify-improvement-proposals/SKILL.md)** — Resolve proposal ambiguities and compare impacts, tradeoffs, and evidence before recommending a change.
- **[engineering-risk-routing](./engineering-risk-routing/SKILL.md)** — Classify engineering risk and select the required proposal, architecture, explanation, and runtime-evidence gates.
- **[explain-code-flow](./explain-code-flow/SKILL.md)** — Explain existing code from governed system and flow views down to selected implementation details.
- **[govern-modular-event-architecture](./govern-modular-event-architecture/SKILL.md)** — Govern module boundaries, type and state ownership, algorithms, and scheduling evidence.
- **[spec-governance](./spec-governance/SKILL.md)** — Maintain the canonical change-set specification and verify requirement-to-evidence traceability.
- **[formatter-governance](./formatter-governance/SKILL.md)** — Select repository-first formatter policy and protect confirmed full-program writes before product-code mutation.
- **[validate-on-device](./validate-on-device/SKILL.md)** — Collect bounded physical-device and operating-system runtime evidence.

- **[prototype](./prototype/SKILL.md)** — Build a throwaway prototype to answer a design question: a runnable terminal app for state/logic, or several toggleable UI variations.

- **[diagnosing-bugs](./diagnosing-bugs/SKILL.md)** — Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test.
- **[research](./research/SKILL.md)** — Investigate a question against high-trust primary sources and capture the findings as a cited Markdown file in the repo, run as a background agent.
- **[tdd](./tdd/SKILL.md)** — Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time.
- **[domain-modeling](./domain-modeling/SKILL.md)** — Actively build and sharpen a project's domain model — challenge terms, stress-test with scenarios, update `CONTEXT.md` and ADRs inline.
- **[codebase-design](./codebase-design/SKILL.md)** — Shared discipline and vocabulary for designing deep modules: small interfaces, clean seams, testable through the interface.
- **[code-review](./code-review/SKILL.md)** — Two-axis review of the diff since a fixed point: **Standards** (does it follow the repo's coding standards, plus a Fowler smell baseline?) and **Spec** (does it faithfully implement the originating issue/PRD?), run as parallel sub-agents.
- **[resolving-merge-conflicts](./resolving-merge-conflicts/SKILL.md)** — Work through an in-progress git merge or rebase conflict hunk by hunk, resolving by intent traced to each side's primary source, then finish the operation — never `--abort`.
- **[wayfinder](./wayfinder/SKILL.md)** — Map a large effort as decision tickets on the issue tracker.
