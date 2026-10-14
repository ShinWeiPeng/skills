Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

## When to reach for it

Type `/diagnosing-bugs`, or the agent reaches for it on its own when a task fits. It is model-invoked, and fires on "diagnose" or "debug this", or on a report that something is broken, throwing, failing, or slow.

`diagnosing-bugs` runs a disciplined diagnosis loop for hard bugs and performance regressions — building a repro, minimising it, aligning the shared computation model when state or accounting is complex, ranking hypotheses, instrumenting, then fixing with a regression test.

| Your situation | Where to go |
| --- | --- |
| A specific defect you can describe as a symptom | This skill |
| A slow endpoint or a timing regression with a known before-and-after | This skill. It has a performance branch (measure a baseline, then bisect) |
| "Where are the bottlenecks in this codebase?", no specific symptom | Not this skill. It diagnoses one known failure, it does not audit |
| A raw bug report from someone else, not yet confirmed or written up | [triage](https://aihero.dev/skills-triage) first |
| Throwaway code to answer a design question, not chase a defect | [prototype](https://aihero.dev/skills-prototype) |
| Building a planned behaviour test-first | [tdd](https://aihero.dev/skills-tdd) |
| Asking what would have prevented the bug, once it is fixed | [retro](https://aihero.dev/skills-retro), run in the same session |
| No good seam exists to lock the bug down | [improve-codebase-architecture](https://aihero.dev/skills-improve-codebase-architecture), which you start yourself |

For counter, epoch, state-machine, timing, concurrency, queue, buffer, and accounting failures, it also refuses to jump from evidence directly to root cause. It first returns a **Debug Model Packet**: evidence boundaries, a decision flow, an event sequence when ordering matters, counter/state contracts, conservation equations, and a minimal event-by-event trace. You confirm this computation model before hypothesis ranking or repair comparison begins.

## When to reach for it

Phase 1 gets the most effort because it is the only hard phase. The skill lists ways to build the loop, roughly in order of preference:

1. A failing test at whatever seam reaches the bug.
2. A curl or HTTP script against a running dev server.
3. A CLI invocation with a fixture input, diffed against a known-good snapshot.
4. A headless browser script asserting on DOM, console, or network.
5. A replayed capture: a saved request, payload, or event log, run through the code path in isolation.
6. A throwaway harness: a minimal subset of the system, one function call.
7. A property or fuzz loop, for "sometimes wrong output".
8. A bisection harness you can hand to `git bisect run`.
9. A differential loop: same input, old version against new.
10. A [human-in-the-loop](https://www.aihero.dev/ai-coding-dictionary/human-in-the-loop) bash script, last resort. The skill ships `scripts/hitl-loop.template.sh` for this: the agent runs the script, you follow prompts in your terminal, and your answers come back as parseable output.

*A* loop is not the goal. **Tight** is: fast (seconds), deterministic (same verdict every run), sharp (asserts your exact symptom, not "didn't crash"), and runnable by the agent without you. A 30-second flaky loop is barely better than none. For a bug that only shows up sometimes, the target is not a clean repro but a **higher reproduction rate**: loop the trigger, parallelise, add stress, inject sleeps, until the flake rate is high enough to debug against.

When the agent cannot build one, the skill tells it to stop and say so, list what it tried, and ask you for [environment](https://www.aihero.dev/ai-coding-dictionary/environment) access, a captured artifact, or permission to add temporary instrumentation. It must not go on to form hypotheses anyway.

## The gates between phases

The phases are gates, not a checklist. The agent cannot enter a phase until a specific condition is true.

| Gate | What has to be true |
| --- | --- |
| Into Phase 2 | A named command, already run and pasted with its output, that can go red on this bug |
| Into Phase 3 | The repro is reproduced *and* minimised: every remaining element is needed to reproduce the bug |
| Into Phase 4 | 3–5 ranked, falsifiable hypotheses exist, each stating its prediction, shown to you before any is tested |
| Into Phase 5 | Probes map to a specific prediction, one variable at a time, every debug log has a tag like `[DEBUG-a4f2]`, so one grep finds them all for cleanup |
| Done | The original repro no longer reproduces, the instrumentation is gone, and the commit message names the hypothesis that turned out correct |

Phase 5 has one exception. The agent writes the regression test before the fix, but only if a **correct seam** exists for it: one where the test exercises the real bug pattern as it occurs at the call site. Where the only available seam is too shallow, the skill tells the agent to say so instead of writing a test that gives false confidence. The missing seam is itself a finding, and the agent records it instead of hiding it.

## Common questions

**It fires on quick questions where I just wanted a direct answer.**
This is the most-reported problem with the skill. On GPT-5.6-Sol especially, users report it triggering on a plain description of a problem: "the model triggers the rather formal diagnosing-bugs skill instead. It then goes on to construct a reproduction scenario (often building a mock scenario with limited value) before giving me a response or suggestion. This results in considerable reply delays." Four separate people reported the same problem on [issue #578](https://github.com/mattpocock/skills/issues/578). The accepted fix is to start with a lighter approach and move to the full diagnosis only when the problem needs it, but that change has not shipped. The skill is tuned for Claude Code's invocation behaviour, and a [model](https://www.aihero.dev/ai-coding-dictionary/model) with a lower activation threshold fires it too often. Until the fix ships, the workaround is to say what you want ("just answer this, don't diagnose") or to disable model invocation for it in your [harness](https://www.aihero.dev/ai-coding-dictionary/harness).

**Can I point it at a codebase and ask where the performance problems are?**
No. It diagnoses one failure you can already name. Its performance branch is for a regression with a symptom (establish a baseline measurement, then bisect, measure first and fix second), not for a proactive sweep. A skill for the proactive version was [proposed and closed](https://github.com/mattpocock/skills/issues/431); no skill does it now.

**Does it stop and ask me before it writes the fix?**
No. Only Phase 3 has a human checkpoint: the ranked hypothesis list is shown to you before any is tested, and the agent continues with its own ranking if you are away. There is no gate between instrumentation and the fix, so the agent can start writing code before you have agreed with its root cause. [Issue #124](https://github.com/mattpocock/skills/issues/124) asks for that gate and is still open. If you want it, say so when you invoke the skill.

**I already ran `/triage` on this bug report. Is this the same work again?**
Partly, and neither skill says so. As one reader put it: "Triage's step 3 is essentially a shallow, bounded instance of diagnosing-bugs Phase 1–2, but neither file mentions the other." Triage does a bounded "is this actually a bug, and what is the surface" pass; this skill does the thorough version. Running triage first is not wasted, because its verification often gives you most of Phase 1's raw material. But expect this skill to redo that work in full, and expect no cross-reference to tell you so.

**Will the repro output it pastes leak secrets?**
It might. The skill asks the agent to paste the invocation and its output, and to request artifacts like HAR files, log dumps, and core dumps. No instruction tells the agent to sanitise them. [Issue #674](https://github.com/mattpocock/skills/issues/674) raises exactly this (credentials, tokens, cookies, and personal data copied into a chat, an issue, or a PR) and proposes a redaction guardrail. It is open and unimplemented. Treat redaction as your job for now, particularly before the output goes anywhere public.

**My security scanner flagged this skill as high risk.**
Snyk flags it, and the flag is a false positive. It is the only skill in the set that ships an executable shell script (`hitl-loop.template.sh`) alongside instructions to run it and to curl a dev server. A shipped `.sh` file, instructions to run it, and outbound HTTP together are enough to trigger a static scanner. The script itself is about 30 lines of `read -r -p` prompts that pause for human input. The scanner rates what the skill could do, not a proven exploit.

**What happened to `/diagnose`?**
v1.0.0 renamed it to `/diagnosing-bugs`. The old name no longer exists. Anything of yours that chains `/diagnose` (a wrapper skill, a saved prompt) needs updating.

## The Debug Model Packet is the shared language

Complex bugs often stay confusing even after they reproduce because words such as “accepted”, “advanced”, “pending”, or “reset” hide different calculations. The packet makes each term auditable: every counter has a unit, scope, update condition, non-update condition, reset rule, threshold or epoch, and a clear statement of what it can and cannot prove.

Mermaid diagrams show branch order and actor timing, while tables and worked traces carry the exact arithmetic. The flowchart visibly marks the observed error path, evaluated branch values, the `FIRST DIVERGENCE`, and the final symptom's evidence ID. Confirmed error paths use error styling plus textual labels; unproven paths must say `INFERRED ERROR PATH` so visual emphasis cannot turn an inference into a fact. A diagram never substitutes for the counter contract or conservation equation. Claims stay labelled as confirmed evidence, inference, or still to verify, and aggregate snapshots are not treated as proof of per-event order.

The understanding gate is risk-based. A direct stateless condition bug can skip it with an explicit reason. A model-alignment bug stops after the packet so you can confirm the calculation or point to the first unclear transition. Confirmation means “this is how the system computes,” not “I agree with the proposed cause or fix.”

## It's working if

- It builds and runs a repro command *before* theorising — and pastes the invocation and its red output.
- The loop asserts the symptom you actually reported, not a nearby failure.
- Model-alignment bugs provide a traceable Debug Model Packet and pause for confirmation before root-cause ranking.
- Every counter or state claim links to an exact condition, trace step, and evidence item rather than a vague description.
- Hypotheses arrive as a ranked, falsifiable list shown to you before any are tested.
- Debug instrumentation is tagged (`[DEBUG-...]`) and grepped away before it declares done.

## Where it fits

`diagnosing-bugs` is a reach-for-it-anytime standalone — you drop into it the moment something is broken, and drop out once the fix and its regression test are in. Its post-mortem hands off to [improve-codebase-architecture](https://aihero.dev/skills-improve-codebase-architecture) when the real finding is that there's no good seam to lock the bug down — the code, not the bug, is the problem. When you're unsure which skill fits, [ask-matt](https://aihero.dev/skills-ask-matt) routes you.

## Discussion is saved from entry

Engineering work automatically starts or resumes a task-specific working record,
including diagnosis and code explanation. Grilling manages that discussion while
specialist skills provide facts. Questions are reserved for decisions the user
must make. A saved explanation does not need a formal SPEC; an adopted change with
complete scope and acceptance does. Suggested changes remain candidates until
accepted and do not expand authorization.

The router and discussion owner are called explicitly with task and turn sources.
No lifecycle hooks are registered, and host trust, loading or firing evidence is
not required. Failed saving reports the unsaved scope while discussion and document
repair remain available. Product changes require the current SPEC and execution
authorization.

## Upstream integration

Before trusting a failing test after a forced mutation, prove the mutation was applied and the running artifact includes it. After a fix, `retro` reviews what could have prevented the bug; a missing test seam is a separate architecture proposal. The governed computation-model understanding gate remains in place.
