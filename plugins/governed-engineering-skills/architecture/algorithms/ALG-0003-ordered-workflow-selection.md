# ALG-0003: Ordered intent and workflow selection

## Metadata

- Status: proposed
- Owner module: `workflow_routing_domain`
- Product feature: Automatic authoritative engineering handoff
- Flow IDs: `governed-engineering-route`
- Related ADRs: `ADR-0010`, `ADR-0011`
- Source paths:
  - `skills/engineering-risk-routing/references/intent-rules.json`
  - `skills/engineering-risk-routing/scripts/workflow_selection.py`
  - `skills/engineering-risk-routing/scripts/guided_workflow_router.py`
- Test and benchmark paths: `tests/test_guided_routing.py`
- Supersedes: none

## Problem and observable success

Select the safe primary engineering workflow without letting risk gates replace user
intent or letting model judgment guess ambiguous states. Identical versioned inputs
must produce the same `GuidedRouteDecision`.

## Ordered method

1. Preserve an explicit skill.
2. Otherwise classify versioned hard intents in order: review, diagnosis,
   code-understanding, implementation/design.
3. Keep review and code-understanding read-only unless a versioned connector plus
   mutation term identifies an explicit second action; inherently modifying explicit
   skills remain modifying without relying on prompt wording.
4. Resolve active canonical specification context in this order: an explicitly named
   path, a tracker-provided canonical path, a branch match, then the repository's
   unique confirmed specification. Never select the newest of multiple candidates.
5. Apply ProjectState and specification context to the classified intent.
6. Add R0–R3 required gates without changing the primary intent.
7. Require `spec-verified` before any modifying path reaches TDD or implementation.
8. Check capability and return the authoritative handoff.

Unmatched intent and indeterminate ProjectState stop in one-question grilling.
Review and code explanation remain read-only. A modifying bug diagnoses first and
grills before choosing a fix. Every other modifying path reconciles one working
specification per change set. A confirmed specification verifies on a new task and
resumes execution without another interview unless the request introduces a new
decision or conflict.

## Wayfinder and capability thresholds

Wayfinder requires all three: at least two decision-ticket candidates, at least one
blocking dependency, and at least one imprecise fog area. Missing wayfinder or tracker
capability is `BLOCKED`. Missing `grill-me` may be `DEGRADED` only when `grilling` is
available as the equivalent primitive. All other required capability loss blocks.

## Complexity, errors, and forbidden behavior

Intent matching is `O(n*m)` for prompt length `n` and bounded term count `m`; workflow
selection is constant time. Malformed rules and contracts are fatal. It is forbidden
to guess an indeterminate route, bypass grilling for an explicit implementation
skill, or continue execution through a newly discovered discretionary decision.

## Validation

`tests/test_guided_routing.py` covers intent precedence, all ProjectState routes,
explicit `tdd`, diagnosis, read-only flows, wayfinder thresholds, capability states,
blocked risk gates, and execution re-entry. All cases must pass.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
