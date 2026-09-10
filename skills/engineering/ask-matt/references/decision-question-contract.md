# Decision Question Contract

This contract applies to every governed engineering workflow, including an
explicitly invoked downstream skill. Use it whenever the user must choose a design
or specification outcome. It does not turn discoverable facts, status updates, or
ordinary information requests into choices.

## Ask one decision at a time

Ask one decision question at a time. Resolve facts from repository or tool evidence
before asking. After the answer, persist it in the working specification and run the
applicable reconciliation step before asking the next decision question.

## Explain why the decision matters

Before the options, explain:

- the current situation and problem;
- why a decision is needed now;
- which later behavior or work the answer affects.

Offer two or three meaningful, mutually exclusive authored options. For every
option, explain:

- its concrete observable result;
- its main benefits;
- its disadvantages and risks;
- its costs and constraints;
- its downstream consequences;
- when it is suitable and unsuitable.

Recommend an option only when requirements, evidence, or risk analysis supports the
recommendation, and explain why. Otherwise remain neutral and name the missing
evidence.

## Presentation and fallback

Required decisions have no response deadline. Do not switch to Plan mode merely
to expose a choice tool, or switch back because a question tool times out.
Timeout, empty results, preselection, mode changes and unrelated new messages are
not answers or execution authorization. Persist the exact question and its two or
three options using `spec_contract.py question` before displaying them. Recover
the same question ID/version after interruption; do not silently replace options.

Use an available asynchronous question surface without an expiry when supported.
If the host closes that surface, keep complete Markdown options in the reply and
the working spec, then yield for the user's explicit answer. Do not busy-poll,
keep a tool blocked indefinitely, or treat elapsed time as permission to proceed.
Independent read-only work may continue; dependent modifications remain blocked.
Cancel a required question only when the user explicitly withdraws or replaces it,
recording that answer through reconciliation. Do not claim to control host UI
timers unless that capability has actually been verified.

Use the structured choice tool when it is available. When it is unavailable,
present the same two or three options as numbered text and wait for the user's
answer. Missing structured UI alone never blocks the workflow and never requires a
switch to Plan mode.

Tool-provided free-form UI such as `Other` does not count as one of the authored
options. Always accept a free-form, combined, or premise-correcting answer. Preserve
that answer and reconcile any new decision it introduces instead of forcing the
user to select an incomplete option.

## Authorization exclusions

This presentation contract does not change the repository's exact `開始執行`
boundary for product source, tests, configuration, `CONTEXT.md`, ADRs, architecture
artifacts, generated files, Git, or external actions. The narrow exception is
`spec-governance`: after governed grilling begins it may persist local, commit-blocked
`spec-governance/WORKING-SPEC-*` snapshot/journal pairs, and when decision-complete it may create, update, or
reopen `specs/SPEC-####-*.md`. These writes never grant product execution authority.
This boundary is self-contained in the installed plugin; governed workflows never
require or modify a user-global `AGENTS.md`.
The contract also does not add a chat confirmation before a native system permission
prompt or dialog; the native Allow/Deny interaction retains its own contract.
