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

When the permitted surface supports choices, offer two or three meaningful, mutually exclusive authored options. When host rules prohibit textual multiple choice in Default, ask one concise open text question without disguised choices. For every
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

Required decisions have no response deadline. Default/execution mode must not
invoke menu-producing question tools: this includes `request_user_input_async`
and `request_user_input`, even if available, accepted, retried or called without
options. Never switch modes to expose a tool. Only an already-active Plan mode
with applicable host/tool permission may use a menu. Unknown or conflicting mode
and policy evidence must never authorize one.

Persist the actual question before presentation. Legacy choice questions retain
two or three options and remain readable. Use `question --kind open-text` without
`--option` when the host prohibits numbered text. Open questions accept free-form
answers and have no authored options. In Default use numbered text only when
higher-priority instructions permit it; otherwise use one concise open text question.
Do not disguise multiple choices inside an open question.

Before selecting or invoking any question surface, run `spec_contract.py
question-policy --project-root <root> --reference <working-id> --task-ref <task>
--host <host-json> --surface <surface>`. The host JSON records `mode` (`default` or
`plan`), `mode_ref`, `policy_ref`, `numbered_text_allowed` and `menu_tool_allowed`.
Derive these from actual current host instructions and available permitted tools;
tool availability alone is not mode evidence. Inspect PASS and `surface_allowed`
before the dependent action; menu tools additionally require `menu_allowed: true`.
Default returns `menu_allowed: false`. This is a managed preflight, not a host tool
interceptor. Its caller-attested references require independent trace verification.

On cannot-see or disappeared-option feedback, first use `question-update` with
`action: presentation-failed`, the current `question_version`, failed `surface`,
original `user_text` and `source_ref`. Do not interpret that feedback as a design
answer or automatically resend the failed menu. Preserve the unresolved decision
and present a permitted durable text question in the same turn. If the question
must change from choice to open text, explicitly revise it before display.

For alternatives or changed question content, use `question-update` with `action:
revise`, current `question_version`, the new `question`, `kind`, `options`, original
`user_text` and `source_ref`. Keep the ID, increment the version and retain history.
Pass current working revision/hash to every update and reload afterwards. Never
show an unpersisted third option or map a stale numeric answer to the new list.
The update returns BLOCKED while the decision is unresolved; inspect persisted
state, not just the verdict. Failure survives restart. Clear it only with explicit
recovery/user retry evidence via `action: retry-requested`; mode policy still applies.

Timeout, empty results, preselection, mode changes and unrelated messages are not
answers or execution authorization. Recover the exact pending ID/version after
interruption. Host UI closure never authorizes switching modes or proceeding.

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
prepared `presentation` must include current `host`, permitted `surface`,
`stage: prepared`, `text` (the exact saved question, including numbered options
for a choice), full final `reply_text`, and `source_ref`. The final reply must
contain the actual answerable question, not only “options sent”. After emission,
trace review separately checks the actual reply content with `stage: emitted`.
Tool acceptance or an assistant-authored file does not establish visible delivery;
`delivery_verified: false` remains explicit. The check never proves user reading.
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

Place the saved question as the final block of the reply. Introductory prose may
precede it; do not add numbered alternatives elsewhere or append unpersisted
options. Completion compares all numbered lines with the saved option list.

For an allowed Plan menu, presentation.text records its exact saved question and
options. The final reply may repeat just that question; do not repeat numbered
choices when the host prohibits them. Menu payload evidence and actual reply
remain separate, and neither proves that the user saw the menu.
