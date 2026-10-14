Availability:

Add the personal Git Marketplace independently in ChatGPT Work web and Codex Desktop, install **Governed Engineering Skills**, then start a new chat or Codex task.

## When to reach for it

Type `/tdd`, or the [agent](https://www.aihero.dev/ai-coding-dictionary/agent) reaches for it automatically when a task fits: building a feature or fixing a bug test-first, or when you say "red-green-refactor".

Reach for it when there is a concrete behaviour to build, with an input and an observable output, and you want tests that survive a refactor.

| Your situation | Where to go |
| --- | --- |
| A behaviour with defined inputs and outputs (business logic, a request/response contract, a transformation, validation) | `tdd` |
| The behaviour isn't pinned down yet | [to-spec](https://aihero.dev/skills-to-spec), which also agrees the test seams before any code is written |
| The question is really the shape of the interface, not the tests | [codebase-design](https://aihero.dev/skills-codebase-design) |
| You have a [spec](https://www.aihero.dev/ai-coding-dictionary/spec) or [tickets](https://www.aihero.dev/ai-coding-dictionary/ticket) and want the whole build run for you | [implement](https://aihero.dev/skills-implement), which drives `tdd` per ticket |
| Config, wiring, glue, type annotations, straight CRUD delegation | Nothing here fits well; see the open gap below |

That last row is a real gap. The skill decides *where* the seams go, but nothing in it decides *whether* a change is worth the loop at all. If you run it on a change with no independent source of truth to assert against, you get a test that restates the implementation. That is the tautological anti-pattern the skill warns about, reached from the other direction. It is [issue #746](https://github.com/mattpocock/skills/issues/746), and it is open. Until it closes, you make that call yourself, or write the rule into your `CLAUDE.md`.

## Prerequisites

[codebase-design](https://aihero.dev/skills-codebase-design) needs to be installed. `tdd` used to carry its own deep-module and interface-design notes; v1.0 deleted them in favour of the shared skill, and `tdd` now uses its interface-design vocabulary. Nothing else; the skill is [stateless](https://www.aihero.dev/ai-coding-dictionary/stateless) and writes no files of its own.

## The loop, and the seam it runs at

The skill rests on three terms.

**Red-green.** Write the failing test, then only enough code to pass it. Do not write code for the test after next. There is no refactor phase. The skill dropped it in June 2026 because agents almost never performed it, and because review and implementation work better as separate sessions. Refactoring belongs to [code-review](https://aihero.dev/skills-code-review).

**Vertical slice.** Write one test at one seam, then the minimal implementation, then repeat. The first cycle is a **tracer bullet** that proves a single path end to end. The opposite is horizontal slicing: all the tests first, then all the code. Tests written in bulk verify *imagined* behaviour. They check the shape of things rather than what a user does, and they commit you to a test structure before you understand the implementation.

**Pre-agreed seam.** A seam is the public boundary you observe behaviour at without reaching inside. The rule has no exceptions. No test goes at an unconfirmed seam. In the full chain the seams are agreed earlier, during [to-spec](https://aihero.dev/skills-to-spec): "`/tdd` is told to only work at pre-agreed test seams, `/code-review` checks that only agreed-upon test seams were used." Invoked on its own, `tdd` asks you directly.

The three anti-patterns it is written to prevent:

| Anti-pattern | The tell |
| --- | --- |
| Implementation-coupled | The test breaks when you rename an internal function, though behaviour did not change. Mocked internal collaborators, asserted call counts, database queries used to verify instead of the interface. |
| Tautological | The expected value is computed the way the code computes it, so the test passes by construction. Expected values have to come from somewhere else: a known-good literal, a worked example, the spec. |
| Horizontal slicing | A batch of tests landed before any implementation. |

Mocks are for system boundaries only: external APIs, time, randomness, sometimes the filesystem or the database. Never mock your own modules.

## Complete modules on the host

Test production modules through their public interfaces and replace only external
dependencies with Fake or Replay. These module SIL cases verify I/O, state, event
order and recovery; add integration tests for coordination between modules. A host
regression suite can satisfy SIL when it runs this production code and preserves
actual commands, results, cases and source hashes. A build or architecture check
alone cannot complete functional validation. Selected PIL/HIL cases run after the
appropriate target build and flash, with their own recorded results.

## Common questions

**Why doesn't it refactor? The description says "red-green-refactor".**

Because the refactor step was removed and the description was not. The removal was deliberate. Agents almost never did the step, and keeping implementation and review in separate sessions works better. Whether the result still counts as TDD by the book matters less than whether the loop produces better code. The mismatch between the trigger phrase and the body is filed as [issue #589](https://github.com/mattpocock/skills/issues/589) and is still open, so "red-green-refactor" continues to work as a phrase that fires the skill. What you get is red-green, with refactoring in [code-review](https://aihero.dev/skills-code-review).

**It asked me to choose a test seam and I had no idea which to pick.**

This is the most-reported friction with the skill ([issue #607](https://github.com/mattpocock/skills/issues/607)). The prompt lists candidate seams by name only, with nothing about what each one catches or misses, so you are choosing between labels. There is no fix shipped yet. The practical workaround is to ask the agent for the trade-offs before answering: what does the component-level seam miss that the integration seam catches, and how much slower is it. It is also why the chain agrees seams up front in `to-spec`, where you have the whole feature in view rather than one prompt.

**It wrote the implementation before the test, even though the skill says red first.**

It happens. One user pushed the [model](https://www.aihero.dev/ai-coding-dictionary/model) on it and got an unusually honest answer: "I knew the skill said 'one test at a time, watch it fail for the right reason'. I read it. I just defaulted to my normal habit." The skill accepts this. No instruction makes an agent comply 100% of the time, and stricter wording restricts the agent's creativity for little gain. The loop is worth running even when the agent does not follow it strictly, because the results are still better overall. If strict adherence matters for a particular slice, watch the run rather than trusting the skill to enforce it.

**Should it write browser or end-to-end tests first?**

Usually not, and the skill will not stop it. A user reported the agent writing a Playwright test first, then spending a long loop re-running it and concluding the *test* was broken for a feature that did not exist yet. Browser tests are slow enough that the red-green feedback loop stops paying for itself. State in your repo's `CLAUDE.md` that browser tests come after the behaviour works.

**Does `/tdd` replace `/implement`, or the course's `/do-work`?**

No. `/tdd` documents the methodology; `/implement` is a simple work→feedback→commit loop and is the direct stand-in for `/do-work`. The course's single `/do-work` step is now split across `/implement`, `/tdd` and `/code-review`. If you are asking which one to run against a ticket, the answer is almost always `/implement`.

**Where did the deep-modules and interface-design guidance go?**

Into [codebase-design](https://aihero.dev/skills-codebase-design) in v1.0, generalised so several skills share one vocabulary. `refactoring.md` left at the same time; refactoring is now [code-review](https://aihero.dev/skills-code-review)'s job, and that skill carries the Fowler smell baseline.

**Does it know about my other tickets?**

No. Run against one ticket, it can propose work that belongs to a sibling ticket, because it has no view of the rest of the issue graph ([issue #129](https://github.com/mattpocock/skills/issues/129)). This is not `tdd`'s job. Passing the spec alongside the ticket helps; right-sizing the tickets in the first place helps more.

## It's working if

- It stops and names the seams it intends to test at, and waits, before any test file exists.
- One test appears, goes red, gets just enough code to pass, and only then does the next test appear, not a batch of tests followed by a batch of code.
- Test names read as capabilities ("user can checkout with valid cart"), not as internals ("checkout calls paymentService.process").
- Expected values in assertions are literals you can trace to the spec, not values recomputed the way the code computes them.
- Renaming an internal function breaks nothing in the suite.
- Mocks appear only at external boundaries (the payment API, the clock) and never around your own modules.

## Where it fits

`tdd` runs inside the build step of the main chain; it is not a step of its own:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review → retro
```

[implement](https://aihero.dev/skills-implement) is the chain's build step, and it drives `tdd` internally to build each ticket test-first before handing off to [code-review](https://aihero.dev/skills-code-review) — so `tdd` is the engine inside that step rather than a step of its own. You can also reach for it directly, whenever there's a concrete behaviour to build without a full spec. Its other neighbour is [codebase-design](https://aihero.dev/skills-codebase-design), which it leans on to find deep-module seams worth testing at. When you're unsure which skill or flow fits, [ask-matt](https://aihero.dev/skills-ask-matt) routes you.

## Discussion remains active while execution is paused

Across new and existing projects, accepting a requirement updates the current SPEC
before implementation. A pause stops product work while later decisions continue
to be recorded. Routing success never grants write permission. Managed delivery
binds explicit execution evidence to the current project, task and specification,
and checks it inside each supported file replacement. Direct host tools remain
outside that boundary; real assistant traces are required in addition to unit tests.

See the [managed delivery contract](https://github.com/ShinWeiPeng/skills/blob/main/skills/engineering/implement/references/managed-delivery.md)
for request examples, supported operations and evidence limits.

## Test and evidence boundaries

Tests now have explicit Module or Flow ownership under `tests/`. Authored validation
plans stay under `validation/`; each execution keeps its own immutable run under
`artifacts/`. This keeps specifications readable and prevents later runs from
replacing the evidence they cite. Whole-project checks include existing files and
report misplaced files and broken references. Layout does not impose language
analysis, dependency or isolation proofs; independent architecture and runtime
verification requirements remain applicable; project-specific retention and Git ignore choices remain separate.

## Upstream integration

For each proposed test seam, explain the defects it catches and the failure modes it misses before implementing the tests.
