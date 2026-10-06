# Data flow implementation designs

Use the same manifest extension and group representation as
[module-design-format.md](module-design-format.md). `flows` keys exactly match
declared L0/L1 flow IDs. Link participants and public interfaces by catalog IDs;
private algorithm steps remain private. Generated views are projections only.

| Group | Meaning |
|---|---|
| identity_purpose | Flow ID, owning L0/L1 module, purpose and workload |
| trigger_completion | Trigger, acceptance and exact end/completion condition |
| steps | Ordered participants, interface refs, interaction, completion, handoff and failure |
| data_correlation | Type/event IDs, source, request correlation, sequence, valid length and data frequency |
| ownership_buffers | Every buffer/copy, owner, capacity, in-flight data, holders and release condition |
| execution_timing | Execution/channel/profile refs, rate/burst, latency, deadlines and budget sources |
| transport_coordination | Concrete aggregation/pressure method and reach; partial progress, ordering, fairness and slow-branch policies |
| failure_stop_verification | Reject/drop/gap, events/state/recovery, bounded drain/cancel and verification |

Present the selected method and alternatives before SPEC confirmation. Explain
whether a return means accepted, module-complete, transport-complete or remotely
complete. Different completion levels are not interchangeable. An aggregate
trigger can still encounter backpressure and does not establish delivery.
For multiple command sources state the sequence/enqueue critical section and
source-aware replies. For shared fan-out state the slowest outstanding holder,
bounded reclamation, each branch's capacity and independent exhaustion policy.
Equal data frequency does not require equal physical baudrates or send instants.

For an applicable `steps` group, `value` is an ordered list of records with nonempty
string fields `id`, `producer`, `consumer`, `interface_ref`, `interaction`,
`completion`, `handoff` and `failure`. Step IDs are unique; participants and
interfaces resolve to existing catalog IDs. Each completion states its actual
layer. The gate rejects missing fields or broken references; source review checks
whether the claimed handoff and completion match the implementation.

## Source format

Use the shared SPEC-owner document format. Module/flow records own `manifest_record`
and their `implementation_design`; interface records own their interface design.
Catalog documents own every remaining manifest field, including extensions. The
source index declares each owner once; the generator rejects duplicate ownership.
