# Applicability

Use project facts, stored with the architecture manifest's platform, workload,
execution and design records. Each fact identifies its source and confirmation:
CPU architecture/features/core topology; OS or bare-metal/RTOS facilities; language,
runtime and compiler/ABI; usable RAM, module/stack budgets and allocator; rates,
bursts, deadlines and blocking restrictions; peripheral/DMA/cache constraints.
Installed RAM alone is not the application's budget. Baudrate is not data frequency.

Use the single `coding_rules` binding defined in [rule versioning](rule-versioning.md).
For each rule ID, its `reason` identifies the affected modules/paths and fact-source
references, including different conditions on different paths. `status` records
`applicable` or `not-applicable`; unresolved facts stay explicit in the design and
block the dependent applicability decision rather than creating another result schema.
Do not treat a missing fact as false or an unresolved condition as an exemption.
Independent logical design may continue; dependent platform claims wait for facts.
All rules must be considered; document topic/path exclusions once with their IDs.

Choose transmission methods by scenario. Compare aggregation, direct filling,
block sharing, bounded queues, pulling, credits or watermarks as appropriate.
State capacity and in-flight limits at every stage, copying and holding points,
where pressure reaches, partial progress and the completion level. A writable
socket does not establish that the final writer has consumed or persisted data.
For sources that cannot pause, explicitly choose overflow/stop/gap behavior.
For fan-in explain sequencing, admission, fairness and reply routing. For fan-out
explain each branch's rate, slow-consumer policy and safe shared reclamation.
No topology alone requires batching, RCU, zero-copy, a worker, or a fixed number
of buffers. Compare actual memory and timing costs with the project's requirements.

Use design-checks for semantic decisions, static-checks for supported structural
evidence, and runtime-checks for target-dependent claims. Preserve their limits.

## OS applicability

Evaluate OS-CAP-001, OS-EXEC-001, OS-CHAN-001, OS-SYNC-001, OS-RES-001, OS-TIME-001 and OS-LIFE-001 individually from confirmed platform and execution facts. Bare metal does not imply that synchronization or timing rules are irrelevant; prove the actual condition. Unknown capability, budget or execution mapping remains unresolved. Numeric budgets are project-specific.
