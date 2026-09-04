Availability:

Install **Governed Engineering Skills** from the personal Git Marketplace on
each product surface, then start a new chat or Codex task.

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/formatter-governance)

## What it does

Formatter governance chooses and verifies the formatting policy before product code
is written. Greenfield projects receive governed defaults, while existing projects
keep their established formatter and style.

## When to reach for it

Type `/formatter-governance`, or the agent reaches for it automatically before a
governed modifying workflow writes tests or product source. Reach for it when a
project needs formatter selection, a safe scaffold boundary, or check evidence.

## The formatter gate

The formatter gate separates a non-mutating check from a formatting write. It can
permit only the minimum greenfield scaffold needed to configure tooling, then stops
product work until the formatter is available and the check passes. Existing paths
and ambiguous project roots fail closed.

## It's working if

- Greenfield and existing projects take different, evidence-backed branches.
- Existing files remain byte-for-byte unchanged when scaffold preflight blocks.
- Reports name the exact root, check command, result, and permission outcome.

## Where it fits

This is a delivery-chain gate coordinated before
[tdd](https://aihero.dev/skills-tdd),
[implement](https://aihero.dev/skills-implement), and
[code-review](https://aihero.dev/skills-code-review). See
[ask-matt](https://aihero.dev/skills-ask-matt) for the router over the full set.
