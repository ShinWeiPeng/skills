# Architecture exception policy


Use an Architecture Decision Record for a MUST-rule exception or a durable architecture choice with meaningful alternatives.


Use the plugin shared references/adr/{format,workflow,checks}.md; in this checkout their source is plugins/governed-engineering-skills/references/adr/.

Approval and exception-scope checks use the shared ADR workflow and checks.

Describe the actual structure first, then remediate every discovered MUST violation by default. A non-AI developer may temporarily defer one exact rule/location in `architecture/baseline.yaml` only with rationale, approval reference, captured revision, review date, and removal condition. New code and touched scope comply immediately; baseline growth is forbidden and Release requires zero temporary entries. A durable exception requires an accepted ADR.
