Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/engineering-risk-routing)

## What it does

`engineering-risk-routing` classifies an engineering task and returns the gates that must pass before work continues. Ordered hard triggers take precedence, so missing evidence cannot be downgraded by a softer rule.

It also recognizes exact fresh-task `開始執行` as a confirmed-spec resume intent. A unique confirmed specification proceeds to verification; several candidates require one selection, and no candidate fails closed. Ordinary discussion containing a quoted or negated phrase is not execution authorization.

## When to reach for it

Codex invokes this automatically through the engineering router. Use it directly when you need to inspect the risk class, required gates, PASS/BLOCKED result, or resume target.

## Fail closed

Its leading idea is **preserve the gate**: unavailable architecture, proposal, code-flow, or runtime evidence remains blocking rather than being replaced by a guess.

The router accepts task and working references and reloads pending decisions before classifying short replies. A factual read-only turn preserves the question; a decision answer returns to specification reconciliation. Keyword hints for Git tracking supplement durable context rather than replacing it.

## Where it fits

This is routing infrastructure behind [ask-matt](https://aihero.dev/skills-ask-matt), not a standalone planning method.

Project verification requirements now follow the current specification across reloads and short continuation commands. The workflow distinguishes implementation progress from acceptance: missing hardware evidence cannot be replaced by host tests or a successful build. The shared validation plan records the applicable layers and their evidence sources.

## Test and evidence boundaries

Tests now have explicit Module or Flow ownership under `tests/`. Authored validation
plans stay under `validation/`; each execution keeps its own immutable run under
`artifacts/`. This keeps specifications readable and prevents later runs from
replacing the evidence they cite. Whole-project checks include existing files and
report misplaced files and broken references. Layout does not impose language
analysis, dependency or isolation proofs; independent architecture and runtime
verification requirements remain applicable; project-specific retention and Git ignore choices remain separate.

## Bounded diagnosis and recovery

Separate discovered skill names, callable CLI capabilities and actual check
verdicts. `test-validation-layout` resolves to the validated `architecture_cli.py
layout` result; a callable FAIL or BLOCKED remains a failed or blocked check.
An explicit caller capability limit is never expanded by discovery.

A blocker records category, original evidence, affected branch, repair suggestion,
authorization requirement, reproducible recheck, success condition and resume target.
Investigate discoverable facts and prepare the concrete repair first. Reuse current
authorization for deterministic repairs within the confirmed contract; ask only
for missing decisions, authority or external conditions. Never change acceptance
thresholds or replace required runtime evidence with host results.

Managed `recover` stores branch state beside the existing execution receipt. It
checks the same task/SPEC binding, reserves each attempt before effects, and allows
at most three attempts and 120 seconds per input cycle. Identical failed inputs
require evidenced temporary failure to retry; changed actual inputs or repair
start a new bounded cycle while preserving history. Unsupported rechecks remain
investigation, never success. Existing discussion repair allowances are untouched.

Discussion entry and synchronization are reported separately. A saved entry with
pending synchronization stays pending; the route exposes recovery while preserving
discussion and read access. Product admission still checks synchronization.

The guided router resolves the spec owner's explicit task/project binding before
collecting repository evidence. Hook, router and owner therefore inspect the same
canonical root even when desktop cwd is its parent. This binding does not change
risk classification or authorize product operations.
