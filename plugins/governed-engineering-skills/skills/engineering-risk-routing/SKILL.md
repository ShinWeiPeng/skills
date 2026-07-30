---
name: engineering-risk-routing
description: Classify engineering tasks with ordered hard triggers, select required proposal, architecture, code-flow, and runtime-evidence gates, and return a deterministic RoutingDecision. Use when ask-matt or another engineering skill needs a risk class, required gates, PASS/BLOCKED status, next skill, or return-to-flow target. Do not use for standalone learning-note or HackMD creation.
---

# Engineering risk routing

Classify before an engineering workflow performs mutation. Keep this skill model-invoked; it owns the rule table shared by every governed entry point.

## Run the classifier

1. Read [routing-rules.json](references/routing-rules.json) as the source of truth.
2. Run:

   ```powershell
   python scripts/classify_risk.py --prompt "<task>" --entry-skill "<entry>"
   ```

   Omit `--entry-skill` when routing from `ask-matt`. Add `--passed-gate <skill>` for every gate with valid PASS evidence. Add `--available-skill <skill>` only when capability discovery has produced an explicit set; once supplied, missing required gates fail closed. Use `--governance-status missing` when an R2/R3 existing project has no supported manifest; the result remains BLOCKED until its as-is inventory and baseline exist.

3. Return the classifier JSON without weakening or reordering it:

   - `task_class`
   - `matched_hard_triggers`
   - `risk_class`
   - `required_gates`
   - `next_skill`
   - `status`
   - `return_to_flow`

4. If `task_class` is `out_of_scope`, do not route it through `ask-matt`. Standalone learning-note creation remains owned by the independently installed note skill.
5. If status is `BLOCKED`, state the missing capability or unpassed gate and stop before mutation. Never replace architecture or device evidence with a build, ordinary log, or lower-risk flow.

## Precedence

- `R3 Runtime-critical` outranks `R2 Governed`, which outranks `R1 Standard`, which outranks `R0 Knowledge`.
- Any hard trigger wins over a lower aggregate impression; there is no score that can cancel it.
- A pure learning-note/HackMD request is outside this engineering router. A mixed request is classified only on its engineering work; note production remains a separate user request.
- An existing project that needs governance but lacks a supported manifest must first establish an as-is inventory and baseline.

## Contracts

Validate output against [routing-contract.schema.json](references/routing-contract.schema.json). `GateResult` is the evidence contract used by handoffs and resume checks; Codex may report it but must not invent PASS evidence.
