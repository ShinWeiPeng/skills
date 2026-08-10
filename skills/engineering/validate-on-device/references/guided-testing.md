# Guided form and review contract

Use a form for fact collection and a table for read-only review. Never parse edited Markdown as evidence and never ask the user to assign PASS or FAIL.

## Prepare

`prepare-guided-session` writes three artifacts without overwriting existing files:

- `session.json`: immutable run ID, scenario, phase, evidence mode, maximum duration, profile hash, and ordered step contracts.
- `response.template.json`: facts, evidence paths, blocked reasons, remediation, one confirmation flag.
- `user-guide.md`: offline instructions matching the same step IDs.

With connectivity, ask one step at a time and read the answer back before recording it. Offline, the user fills the JSON while following the Markdown guide. Each response declares `capture_mode: gpt-guided|offline-user`.

## Review and revise

`finalize-guided-session` validates every field, hashes bounded evidence paths inside the project root, and produces `review.json` plus `review.md`. The Markdown table is a projection only. Set `confirmation.confirmed: true` only after the user reviews all rows.

Do not overwrite a response. Revision 1 has no predecessor. Later revisions increment by one and set `supersedes_sha256` to the canonical SHA-256 of the immediately previous response. Supply all revisions in order during evaluation.

Required steps accept only `completed` or `blocked`. Completed steps require an actual observation; evidence-required steps require a hashable bounded file. Blocked steps require both reason and remediation. Any pending, malformed, unconfirmed, missing, or required-blocked step makes the guided review `BLOCKED`.

## Evaluate

Pass `--guided-session`, `--guided-review`, and each `--guided-response` in revision order. The runner recomputes the review and revision chain, matches run/scenario/profile identity, and preserves every JSON/Markdown artifact plus SHA-256 in the evidence bundle. The review status gates evidence admission but does not decide product criteria.
