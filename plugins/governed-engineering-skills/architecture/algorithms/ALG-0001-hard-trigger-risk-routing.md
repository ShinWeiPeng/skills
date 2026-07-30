# ALG-0001: Hard-trigger engineering risk routing

## Metadata

- Status: proposed
- Owner module: `risk_routing_domain`
- Product feature: Engineering risk classification and gate selection
- Flow IDs: `governed-engineering-route`
- Related ADRs: `ADR-0002`
- Source paths:
  - `skills/engineering-risk-routing/references/routing-rules.json`
  - `skills/engineering-risk-routing/scripts/classify_risk.py`
- Test and benchmark paths: `tests/test_routing.py`
- Supersedes: none

## Problem and observable success

Select the minimum safe engineering workflow without allowing a low-risk impression to cancel an architecture, hardware, timing, or evidence hard trigger. Success means identical input and capability evidence always produce the same contract-valid decision.

## Inputs, outputs, units, ranges, and data-quality assumptions

Inputs are UTF-8 task text, an optional entry skill, explicit available-skill names, and explicitly passed gates. Output is one `RoutingDecision`. Matching is case-insensitive substring matching over a versioned term table. Empty or unmatched engineering text uses R1.

## Constraints and quantitative acceptance thresholds

- All committed routing fixtures must pass exactly.
- One missing required capability must produce `BLOCKED`.
- An R2/R3 direct mutation entry without governance PASS must produce `BLOCKED`.
- A pure learning-note/HackMD request must produce `task_class=out_of_scope`, `risk_class=null`, and no next skill.
- Classification time must remain linear in prompt length times the bounded term count; no network or model call is permitted inside the classifier.

## Candidate methods and comparative evidence

- Ordered hard triggers: selected because a single critical condition cannot be averaged away.
- Weighted 0–2 score: rejected because weights create false precision and require veto exceptions.
- Hybrid triggers plus scoring: rejected for v1 because the ambiguous remainder does not justify a second tunable method.

## Selected method and reasons for rejecting alternatives

Evaluate classes in `R3 → R2 → R1 → R0` precedence, using R1 as the default. Pure learning-note requests are screened out before engineering classification. Capability and unpassed-gate checks occur after classification and can only change PASS to BLOCKED.

## Exact behavior, boundaries, and tie-breaking

1. Normalize task text with Unicode-aware case folding.
2. If note terms match and no engineering term matches, return the out-of-scope decision.
3. Scan configured classes in precedence order and select the first class with any matching term.
4. Use the R1 default when no configured term matches.
5. Add blockers for explicitly missing required skills.
6. At a mutation entry, add a blocker when R2/R3 governance has not passed.
7. Return BLOCKED when blockers exist; otherwise return PASS.

Multiple terms within one class are retained in configured order. Risk precedence resolves matches across classes.

## Parameters, calibration, versioning, and compatibility

Rules are versioned in `routing-rules.json`. Adding, removing, or reclassifying a term requires fixture updates, algorithm review, and a vendor-lock refresh. Contract fields remain backward compatible within plugin version `0.1.x`.

## Time and space complexity and resource budgets

For prompt length `n` and total configured terms `m`, worst-case time is `O(n*m)` with bounded `m`; auxiliary space is `O(m)` for matches. No persistent state, allocation budget, or runtime thread mapping is required.

## Errors, degradation, fallback, and forbidden behavior

Malformed rule files are fatal validation errors. Missing capabilities or evidence are BLOCKED, never downgraded. It is forbidden to classify a pure learning-note request as an engineering route or to treat builds and ordinary logs as architecture/runtime PASS evidence.

## Validation cases and evidence

Run `python -m unittest discover -s tests -p test_routing.py -v`. The committed cases cover R0–R3, direct-entry blocking and resume, capability failure, highest-risk precedence, ordinary unit tests, and HackMD isolation. Exit code `0` with all cases passing is required.

## Risks and monitoring

Substring terms can overmatch ordinary language. Review false positives during forward tests and change terms only with a regression fixture. Vendor and integration validators prevent absent skills or stale contract paths.

## Human approval

- Approver: pending human review
- Approval date: pending
- Approval reference: pending
