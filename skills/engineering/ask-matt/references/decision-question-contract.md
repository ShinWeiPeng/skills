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

In Default/execution mode, present the same two or three options as numbered text
(1, 2, 3 as applicable) and wait for the user's numeric or free-form answer. This
is the intended surface even when a structured choice tool is available. Do not
switch modes merely to ask a question. Respect higher-priority host instructions
if they restrict textual questions; preserve the existing mode and pending state.

If already in Plan mode, stay in that mode and use its structured choice tool when
available. If the host closes the surface, preserve the complete options and yield
for an explicit answer. Do not switch to execution mode because of a timeout.

Do not busy-poll, keep a tool blocked indefinitely, or treat elapsed time as
permission to proceed. Independent read-only work may continue; dependent
modifications remain blocked. Cancel a required question only when the user
explicitly withdraws or replaces it, recording that answer through reconciliation.
Do not claim to control host UI timers or collaboration modes.

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

## Complete the discussion turn

An active specification discussion persists across factual side questions. Read the
whole message for every applicable component: an answer, a requirement correction,
a factual question, or an explicit pause. Do not classify a mixed message solely
as a factual request. Answer the factual part, reconcile the explicit answer and
scope changes, then reload turn-context before choosing the next action.

If open decisions remain, resolve discoverable facts read-only, persist exactly one
next question, and present it in the same turn. Do not end with only “next we need
to decide ...” or “we can discuss later.” For a pure factual question while a choice
is unanswered, answer it and visibly reconnect the same saved question/version;
do not invent an answer, silently change its options or create a duplicate question.

Before finalizing an active discussion, run spec-governance `finish-turn` using the
current working reference and task. Observe the result before sending the final
reply; prepare and present the exact content described by the observation. The
check validates caller-observed evidence, not host display or human authentication.
Only these stopping points are valid:

- A current persisted question has been presented (or visibly reconnected), so wait
  for its answer without a deadline.
- A concrete blocker and required user input have been explained with an evidence
  reference; generic “blocked” or “waiting” labels do not suffice.
- The user explicitly paused discussion/all work; preserve the pending state.
- All decisions are settled and the matching confirmed SPEC/proposal is presented;
  await exact execution authorization, without manufacturing another question.

Product execution suspension does not suspend discussion. Every SPEC revision
still invalidates product authority. No finish-turn result authorizes product work.
A rejected completion means continue with its next_action, not ask the user to say
“continue.” If the user explicitly cancels, honor that request rather than forcing
the interview to continue.
