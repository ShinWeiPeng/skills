<p>
  <a href="https://www.aihero.dev/s/skills-newsletter">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://res.cloudinary.com/total-typescript/image/upload/v1777382277/skills-repo-dark_2x.png">
      <source media="(prefers-color-scheme: light)" srcset="https://res.cloudinary.com/total-typescript/image/upload/v1777382277/skill-repo-light_2x.png">
      <img alt="Skills" src="https://res.cloudinary.com/total-typescript/image/upload/v1777382277/skill-repo-light_2x.png" width="369">
    </picture>
  </a>
</p>

# Skills For Real Engineers

[![skills.sh](https://skills.sh/b/mattpocock/skills)](https://skills.sh/mattpocock/skills)

My agent skills that I use every day to do real engineering - not vibe coding.

Developing real applications is hard. Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve.

These skills are designed to be small, easy to adapt, and composable. They work with any model. They're based on decades of engineering experience. Hack around with them. Make them your own. Enjoy.

If you want to keep up with changes to these skills, and any new ones I create, you can join ~60,000 other devs on my newsletter:

[Sign Up To The Newsletter](https://www.aihero.dev/s/skills-newsletter)

## Installation

Clone this repository, then run the native launcher:

- Windows: double-click **`Install Governed Engineering Skills.cmd`**.
- Ubuntu, Debian, Fedora, or RHEL with GNOME, KDE Plasma, or Xfce:
  double-click **`Install Governed Engineering Skills.desktop`**. On the first
  launch, use the desktop environment's **Allow Launching** or equivalent trust
  action if prompted. The installer opens in the configured terminal, displays
  its exit code, and waits for Enter before closing.
- Linux terminal: run **`./Install Governed Engineering Skills.sh`**.

Cinnamon, MATE, and other Freedesktop-compatible environments may also launch
the desktop entry, but are supported on a best-effort basis.

The launchers install missing Git, Node.js/npm, and a verified minimum Codex CLI
through `winget`, `apt`, or `dnf`; start device authentication when needed; add or
upgrade the `governed-engineering` Git Marketplace; and install the Plugin in
place. Existing compatible newer Codex versions are retained. Start a new Codex
task afterward so the refreshed Skills are loaded.

The installer consumes the generated `marketplace-release` Codex distribution.
ChatGPT web
does not provide this personal account with Git Marketplace installation, so it
is not a supported installation surface for this Plugin.

In Codex, run `/setup-matt-pocock-skills` once per repository when using the
repository-governed engineering workflows. It configures the
local issue tracker, triage labels, and documentation locations used by the
Codex engineering workflows. The compatibility inventory records required Codex,
repository, terminal, and device capabilities; it is not a ChatGPT web support
matrix.

## Why These Skills Exist

I built these skills as a way to fix common failure modes I see with Claude Code, Codex, and other coding agents.

### #1: The Agent Didn't Do What I Want

> "No-one knows exactly what they want"
>
> David Thomas & Andrew Hunt, [The Pragmatic Programmer](https://www.amazon.co.uk/Pragmatic-Programmer-Anniversary-Journey-Mastery/dp/B0833F1T3V)

**The Problem**. The most common failure mode in software development is misalignment. You think the dev knows what you want. Then you see what they've built - and you realize it didn't understand you at all.

This is just the same in the AI age. There is a communication gap between you and the agent. The fix for this is a **grilling session** - getting the agent to ask you detailed questions about what you're building.

**The Fix** is to use:

- [`/grill-me`](./skills/productivity/grill-me/SKILL.md) - for non-code uses
- [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md) - same as [`/grill-me`](./skills/productivity/grill-me/SKILL.md), but adds more goodies (see below)

These are my most popular skills. They help you align with the agent before you get started, and think deeply about the change you're making. Use them _every_ time you want to make a change.

### #2: The Agent Is Way Too Verbose

> With a ubiquitous language, conversations among developers and expressions of the code are all derived from the same domain model.
>
> Eric Evans, [Domain-Driven-Design](https://www.amazon.co.uk/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)

**The Problem**: At the start of a project, devs and the people they're building the software for (the domain experts) are usually speaking different languages.

I felt the same tension with my agents. Agents are usually dropped into a project and asked to figure out the jargon as they go. So they use 20 words where 1 will do.

**The Fix** for this is a shared language. It's a document that helps agents decode the jargon used in the project.

<details>
<summary>
Example
</summary>

Here's an example [glossary](https://github.com/mattpocock/course-video-manager/blob/076a5a7a182db0fe1e62971dd7a68bcadf010f1c/GLOSSARY.md) (still named `GLOSSARY.md` at that pinned commit, from before the skills renamed the convention), from my `course-video-manager` repo. Which one is easier to read?

- **BEFORE**: "There's a problem when a lesson inside a section of a course is made 'real' (i.e. given a spot in the file system)"
- **AFTER**: "There's a problem with the materialization cascade"

This concision pays off session after session.

</details>

This is built into [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md). It's a grilling session, but that helps you build a shared language with the AI, and document hard-to-explain decisions in ADR's.

It's hard to explain how powerful this is. It might be the single coolest technique in this repo. Try it, and see.

> [!TIP]
> A shared language has many other benefits than reducing verbosity:
>
> - **Variables, functions and files are named consistently**, using the shared language
> - As a result, the **codebase is easier to navigate** for the agent
> - The agent also **spends fewer tokens on thinking**, because it has access to a more concise language

### #3: The Code Doesn't Work

> "Always take small, deliberate steps. The rate of feedback is your speed limit. Never take on a task that’s too big."
>
> David Thomas & Andrew Hunt, [The Pragmatic Programmer](https://www.amazon.co.uk/Pragmatic-Programmer-Anniversary-Journey-Mastery/dp/B0833F1T3V)

**The Problem**: Let's say that you and the agent are aligned on what to build. What happens when the agent _still_ produces crap?

It's time to look at your feedback loops. Without feedback on how the code it produces actually runs, the agent will be flying blind.

**The Fix**: You need the usual tranche of feedback loops: static types, browser access, and automated tests.

For automated tests, a red-green-refactor loop is critical. This is where the agent writes a failing test first, then fixes the test. This helps give the agent a consistent level of feedback that results in far better code.

I've built a **[`/tdd`](./skills/engineering/tdd/SKILL.md) skill** you can slot into any project. It encourages red-green-refactor and gives the agent plenty of guidance on what makes good and bad tests.

For debugging, I've also built a **[`/diagnosing-bugs`](./skills/engineering/diagnosing-bugs/SKILL.md)** skill that wraps best debugging practices into a disciplined loop, gated phase by phase.

### #4: We Built A Ball Of Mud

> "Invest in the design of the system _every day_."
>
> Kent Beck, [Extreme Programming Explained](https://www.amazon.co.uk/Extreme-Programming-Explained-Embrace-Change/dp/0321278658)

> "The best modules are deep. They allow a lot of functionality to be accessed through a simple interface."
>
> John Ousterhout, [A Philosophy Of Software Design](https://www.amazon.co.uk/Philosophy-Software-Design-2nd/dp/173210221X)

**The Problem**: Most apps built with agents are complex and hard to change. Because agents can radically speed up coding, they also accelerate software entropy. Codebases get more complex at an unprecedented rate.

**The Fix** for this is a radical new approach to AI-powered development: caring about the design of the code.

This is built in to every layer of these skills:

- [`/to-spec`](./skills/engineering/to-spec/SKILL.md) quizzes you about which modules you're touching before creating a spec

And crucially, [`/improve-codebase-architecture`](./skills/engineering/improve-codebase-architecture/SKILL.md) surveys a codebase for deepening opportunities and hands you the candidates. I recommend running it on your codebase once every few days. It is a survey, not a rescue: on a genuinely old codebase it will find real candidates, but it won't untangle the mud for you.

### Summary

Software engineering fundamentals matter more than ever. These skills are my best effort at condensing these fundamentals into repeatable practices, to help you ship the best apps of your career. Enjoy.

## Reference

User-invoked skills orchestrate explicit requests. Model-invoked skills are also
available automatically when their task fits. The fork retains automatic governed
routing for engineering work.

### Engineering

**User-invoked**

- **[implement](./skills/engineering/implement/SKILL.md)**: Implement a piece of work based on a spec or set of tickets.
- **[implement-spec](./skills/engineering/implement-spec/SKILL.md)**: Implement the result of /to-spec and /to-tickets in code.
- **[improve-codebase-architecture](./skills/engineering/improve-codebase-architecture/SKILL.md)**: Scan an existing codebase for deepening and data-flow opportunities, compare execution cost, real-time feasibility, maintainability, extensibility, and model evidence, present candidates as a visual HTML report, then grill through the selected candidate.
- **[retro](./skills/engineering/retro/SKILL.md)**: Conduct a retrospective on a coding session.
- **[setup-matt-pocock-skills](./skills/engineering/setup-matt-pocock-skills/SKILL.md)**: Configure this repo for the engineering skills — set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills.
- **[to-spec](./skills/engineering/to-spec/SKILL.md)**: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
- **[to-tickets](./skills/engineering/to-tickets/SKILL.md)**: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker — edges as text in one file per ticket locally, or native blocking links on a real tracker.
- **[triage](./skills/engineering/triage/SKILL.md)**: Move issues and external PRs through a state machine of triage roles — categorise, verify, grill if needed, and write agent-ready briefs.

**Model-invoked**

- **[ask-matt](./skills/engineering/ask-matt/SKILL.md)**: Automatically route every software-engineering request, including implementation, modification, debugging, review, code explanation, tests, architecture, and deployment. Model-invoked; users never need to name this skill.
- **[clarify-improvement-proposals](./skills/engineering/clarify-improvement-proposals/SKILL.md)**: Clarify every unresolved ambiguity before producing an improvement proposal, then present rendered Markdown with explicit impacts, tradeoffs, and evidence-backed validation. Invoke implicitly for 改善方案、改進方案、優化方案、重構方案、架構改善、設計改善、改善建議、優化建議、方案比較、方案評估、技術選型、提出建議、怎麼改比較好, and equivalent English requests to propose, compare, review, optimize, refactor, or plan improvements. Do not invoke for a direct copyedit, translation, or wording-only change that does not ask for a proposal or design decision. Invoke explicitly with $clarify-improvement-proposals.
- **[code-review](./skills/engineering/code-review/SKILL.md)**: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\".
- **[codebase-design](./skills/engineering/codebase-design/SKILL.md)**: Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when another skill needs the deep-module vocabulary.
- **[diagnosing-bugs](./skills/engineering/diagnosing-bugs/SKILL.md)**: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
- **[domain-modeling](./skills/engineering/domain-modeling/SKILL.md)**: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or editing an ADR.
- **[engineering-risk-routing](./skills/engineering/engineering-risk-routing/SKILL.md)**: Classify engineering tasks with ordered hard triggers, select required proposal, architecture, code-flow, and runtime-evidence gates, and return a deterministic RoutingDecision. Use when ask-matt or another engineering skill needs a risk class, required gates, PASS/BLOCKED status, next skill, or return-to-flow target. Do not use for standalone learning-note or HackMD creation.
- **[explain-code-flow](./skills/engineering/explain-code-flow/SKILL.md)**: Guide developers through existing code using governed System and L0/L1 Parent views, end-to-end Flows, and progressively deeper explanations. Use for every code-understanding request, including implicit questions such as what code does, how data reaches a driver or other sink, where state changes, or why a branch exists, even when the user does not say explain or trace. Route project or composition-root questions to Level 0, Parent or cross-module from-A-to-B behavior to Level 1, modules and symbols to Level 2, and code regions to Level 3. Keep implementation, debugging, and code-review skills primary when the user's goal is to change, diagnose, or review code. Require supported formal architecture governance for System and Parent guidance, and coordinate with $govern-modular-event-architecture when it is missing, stale, invalid, or unsupported.
- **[formatter-governance](./skills/engineering/formatter-governance/SKILL.md)**: Select, verify, and report repository-aware formatter policy before modifying engineering work. Use for greenfield formatter defaults, existing-project style preservation, safe scaffold preflight, formatter checks, and format-write authorization.
- **[govern-modular-event-architecture](./skills/engineering/govern-modular-event-architecture/SKILL.md)**: Govern cross-language modular event architecture, production-source boundaries, named-type and runtime-state ownership, product algorithms, and hard/soft real-time scheduling analysis. Use when Codex creates, reviews, explains, improves, or refactors architecture or algorithms; changes structs, classes, enums, unions, typedefs, DTOs, schemas, runtime state, configuration, ports, events, callbacks, adapters, module boundaries, data flow, execution units, Tasks, priorities, activation rates, core allocation, generated production sources, or architecture views; or checks conformance. Enforce schema 2.2.0 with exact 2.1.0 compatibility, authoring-first L0-L3+ responsibilities, pre-code boundary/type/state/scheduling gates, Type Catalogs, dependency inversion, contracts, fail-closed C/C++ AST evidence, Algorithm Design Records, Description Views, ADR-controlled exceptions, and validation. Invoke explicitly with $govern-modular-event-architecture.
- **[grill-with-docs](./skills/engineering/grill-with-docs/SKILL.md)**: Interview engineering work when durable project context exists but implementation is absent. Model-invoked by ask-matt; users need not name it.
- **[pr](./skills/engineering/pr/SKILL.md)**: Use when writing a PR body.
- **[prototype](./skills/engineering/prototype/SKILL.md)**: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
- **[research](./skills/engineering/research/SKILL.md)**: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
- **[resolving-merge-conflicts](./skills/engineering/resolving-merge-conflicts/SKILL.md)**: Use when you need to resolve an in-progress git merge/rebase conflict.
- **[spec-governance](./skills/engineering/spec-governance/SKILL.md)**: Persist, reconcile, materialize, reopen, resolve, and verify the canonical repository specification for every modifying engineering change set. Model-invoked by ask-matt and delivery workflows.
- **[tdd](./skills/engineering/tdd/SKILL.md)**: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
- **[validate-on-device](./skills/engineering/validate-on-device/SKILL.md)**: Collect and evaluate bounded runtime evidence from physical devices and operating-system applications. Use for on-device validation, hardware tests, firmware boot/timing/peripheral checks, COM or TCP capture, Windows ETW/WPR, Linux perf/ftrace, iOS Instruments/XCTest, guided user-operated testing, structured VAL_* logs, statistical high-frequency evidence, capability probes, permission gates, and PASS/FAIL/BLOCKED evidence bundles. Do not invoke for ordinary unit tests, build-only checks, static code review, or code explanation without runtime validation. Invoke explicitly with $validate-on-device.
- **[verification-ladder](./skills/engineering/verification-ladder/SKILL.md)**: Plan and govern module-contract, SIL, Adapter Contract, PIL, HIL, and System/Soak verification when engineering claims span host, target, hardware, or long-duration environments. Use for layered verification planning and evidence-authority decisions; use TDD for the implementation loop and validate-on-device for selected device execution.
- **[wayfinder](./skills/engineering/wayfinder/SKILL.md)**: Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
- **[wizard](./skills/engineering/wizard/SKILL.md)**: Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or running a one-off migration or cutover. Don't invoke this for steps the agent can perform itself.

### Productivity

**User-invoked**

- **[handoff](./skills/productivity/handoff/SKILL.md)**: Compact the current conversation into a handoff document for another agent to pick up.
- **[teach](./skills/productivity/teach/SKILL.md)**: Teach the user a new skill or concept, within this workspace.
- **[to-questionnaire](./skills/productivity/to-questionnaire/SKILL.md)**: Turn a decision you can't fully answer into a questionnaire for someone else to fill in.
- **[wait-what](./skills/productivity/wait-what/SKILL.md)**: Stop. That last message did not land: re-pitch it.

**Model-invoked**

- **[grill-me](./skills/productivity/grill-me/SKILL.md)**: Interview a greenfield engineering request when both implementation and durable project context are absent. Model-invoked by ask-matt; users need not name it.
- **[grilling](./skills/productivity/grilling/SKILL.md)**: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
- **[writing-for-agents](./skills/productivity/writing-for-agents/SKILL.md)**: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.
