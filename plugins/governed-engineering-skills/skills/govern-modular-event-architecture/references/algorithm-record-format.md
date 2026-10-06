# Algorithm record format

## Required record

Use this structure:

```markdown
# ALG-####: Descriptive algorithm name

## Metadata
- Status:
- Owner module:
- Product feature:
- Flow IDs:
- Related ADRs:
- Source paths:
- Test and benchmark paths:
- Supersedes:

## Problem and observable success
## Inputs, outputs, units, ranges, and data-quality assumptions
## Constraints and quantitative acceptance thresholds
## Candidate methods and comparative evidence
## Selected method and reasons for rejecting alternatives
## Exact behavior, formula or pseudocode, boundaries, and tie-breaking
## Parameters, calibration, versioning, and compatibility
## Time and space complexity and resource budgets
## Errors, degradation, fallback, and forbidden behavior
## Validation cases and evidence
## Risks and monitoring
## Human approval
```

The validation section includes applicable golden vectors, property tests,
boundary and fault cases, benchmarks, regression datasets, commands, expected
observable output, pass conditions, and evidence locations.

