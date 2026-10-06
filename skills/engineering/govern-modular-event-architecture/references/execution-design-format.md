# Execution design format

Use the shared SPEC-owner document format (Identity table plus one Design Data YAML block). One source owns each fact. Numeric values require units and estimate/measurement basis. Unknown and not-applicable are distinct and carry reasons. Confirmed references pin ID/version/path/hash through the shared collection owner.

`execution_design` is an envelope with `id`, `version`, `data`. Data owns `platform_ref`, `design_refs`, `applicability`, `groups`, `evidence`. ID/version references link platform, module, interface and flow sources; fixed path/hash resolution belongs to shared document governance.

Applicability covers `environment`, `units`, `module_mapping`, `scheduling_timing`, `synchronization_channels`, `resources`, `lifecycle`, `os_boundary`, `verification`. Each has status applicable/not-applicable/unknown and reason. Unknown does not pass dependent confirmation. Each group has the same status/reason and `details`; not-applicable details are empty. Applicable details require these fields:

| Group | Fields |
|---|---|
| units | items |
| scheduling | items; each row: unit_ref, trigger, frequency_burst, priority, deadline, execution_budget, wait_budget, core_assignment, analysis |
| channels | items; each row: id, senders, receivers, purpose, os_tool, capacity, call_environment, ordering, delivery_completion, coalescing, full_wait_timeout, stop, ownership |
| synchronization | shared_objects, access_permissions, protection, holding_wait, deadlock_avoidance, priority_inversion, failure_cleanup |
| resources | capacities, owners, allocation, budget_basis, total_simultaneous, os_overhead, shared_accounting, reclamation, exhaustion |
| lifecycle | coordinator, states, readiness, initialization, start, stop, cancel, restart, stale_activity, failure_cleanup |
| verification | rule_refs, design_refs, acceptance_refs, methods, required_evidence, evidence_status |

Nested details use the shared YAML representation. Units and basis accompany timing/rate/capacity values. `design_refs` reuse existing module/interface/flow contracts instead of copying them. `evidence` has design/implementation/acceptance records, each with status pass/pending/not-applicable, method, refs and environment. Not-applicable needs its method/reason; pass requires inspectable references. Host checks do not replace required target evidence.

Execution Units and Resource Inventory are fixed tables defined by design_table_format. Nested module_refs and resource source_refs live only in the designated YAML maps by row ID. units.details.items is the reconstructed inventory; it is not duplicated in YAML. Resource capacities are reconstructed from the resource table. Every timing/rate/capacity quantity has exactly value (finite nonnegative number), unit, basis and nonempty source_refs; time accepts ns/us/ms/s, frequency Hz, bursts count, channel capacity count/B/KiB/MiB, memory B/KiB/MiB/GiB. Referenced module/interface/flow versions are resolved against the actual source index; a well-shaped nonexistent reference is invalid.

Scheduling items contain one unique contract per execution-unit ID (`unit_ref`). Channel items contain a unique channel `id`; senders/receivers are lists of execution-unit IDs. These rows live only in Design Data YAML. Different Tasks and channels keep independent typed timing/capacity quantities; duplicate or unresolved references are errors. Channel capacity is positive.
