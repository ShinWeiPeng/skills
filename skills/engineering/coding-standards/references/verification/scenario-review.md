# Coding-rule review cases

These are positive and negative review fixtures for the shared rules. They do not
claim to have run a device, allocation benchmark or long-duration test. The reviewer
must trace actual callers, ownership and effects; a complete design table alone
cannot pass the negative case. Numeric capacities below are fixture values only.

| SPEC-0041 AC | Positive case | Negative case and required finding |
|---|---|---|
| 001 | A PC deadline path uses a preallocated pool; an MCU best-effort initialization path uses its budgeted heap. | Selecting by PC/MCU label alone misses MEM-ALLOC-001 applicability. |
| 002 | A full bounded pool rejects the request and reports exhaustion. | Falling back to an unbudgeted heap violates MEM-ALLOC-001/MEM-CAP-001. |
| 003 | Cancellation stops new work but keeps the shared block until the last reader releases it. | Timeout frees a still-borrowed block: MEM-LIFE-001 failure. |
| 004 | Check multiplication before allocation, then verify valid source length and destination capacity. A static bound may discharge that exact check. | Checking only the wrapped result, or using a check after another writer changed the length, violates BND-CHECK-001. |
| 005 | Invalid configuration preserves the previous setting and reports source, operation and reason through the abnormal-event contract. | Returning an error without the required abnormal-event outlet violates ERR-PROTECT-001. |
| 006 | A partial send keeps its offset and holds unsent storage within the capacity bound. | Allocating another bank on each refusal hides backlog: FLOW-BOUND-001 failure. |
| 007 | Protection executes before attempting event submission; delayed log consumption changes no safety action. | Blocking protection until logging completes violates ERR-PROTECT-001. |
| 008 | First occurrence submits immediately; later occurrences increment bounded counters and report by the declared deadline. | Waiting for a batch before the first report, or skipping repeated protection, violates ERR-REPORT-001. |
| 009 | With queue capacity 2, pending events A/B then C retain B/C and increment overwrite count. A borrowed event uses separate owned storage. | Overwriting the consumer's borrowed bytes violates ERR-QUEUE-001 and MEM-LIFE-001. |
| 010 | A persistent fault remains queryable after its notification is overwritten; only the owner can clear it after recovery. | Queue removal clears fault state: ERR-STATE-001 failure. |
| 011 | Capacity or maximum wait triggers a send attempt; refusal preserves pending data. | A low-rate partial batch waits forever, or refusal is counted as delivery: FLOW-BATCH-001 failure. |
| 012 | Stop refuses new data, drains until its deadline, reports remaining work and safely cancels/releases holds. | Deadline expiry alone frees an outstanding consumer reference: FLOW-STOP-001 failure. |
| 013 | Compare immediate bounded commands against batching; compare per-output copies against shared immutable samples. Choose using latency, copy and retention budgets. | Topology alone mandates batching or makes every output wait for the slowest one: applicability/design failure. |
| 014 | One mutex protects sequence assignment and ordered admission; the record includes source/correlation. IMU outputs use the same data frequency with different physical rates. | A assigns sequence 1, unlocks, B enqueues 2 before A enqueues 1 despite an ordered contract; or equal baudrate is substituted for equal frequency. |
| 015 | Present actual modules, buffers, copies and methods before confirmation, then compare source and callers. | An undeclared copy or buffer added after confirmation must be reported even if schema validation passes. |
| 016 | A display skips according to its declared freshness policy; a recorder stops its own branch according to its completeness policy. Both report gaps and release safely. | A stalled recorder blocks healthy outputs, or a shared block is recycled while retained: FLOW-FANOUT-006/FLOW-SHARE-001 failure. |
| 017 | An invalid setting leaves the old value; a partly completed write reports the completed range and remaining bytes. | Reporting full rollback after external bytes were sent violates ERR-RESULT-001. |
| 018 | A bounded pending-recovery state is checked by the responsible unit within the declared deadline after notification overwrite. | Recovery exists only as an overwritten notification, or retry jobs grow without limit: ERR-RECOVER-001 failure. |
| 019 | An unpausable source declares overflow behavior; an immediate control path avoids batching that misses its deadline; DMA banks retain ownership until completion. | Treating hardware banks as proof of backpressure or overwriting an active DMA buffer violates FLOW-SOURCE-001. |
| 020 | Each rule retains its ID, strength, condition and requirement; SHOULD deviation is explained. | Treating an optional method as permission to waive a MUST, or adding agent steps to rule rows, fails review. |
| 021 | Two collision implementations satisfy the same Process input/result contract; private thresholds stay internal. | The caller branches on a private algorithm flag or obtains private mutable state: MOD-CONTRACT-001/STATE-003 failure. |
| 022 | Manifest IDs populate the 12 module groups; generated output changes with the source. | Unknown facts presented as verified, parallel editable ownership tables, or missing implementation evidence fail the design contract/review. |
| 023 | A synchronous setting update returns its completed result. An asynchronous submit returns acceptance plus correlation and later completion/failure. | Accepted work is reported as finished, or local write completion as remote processing: API-COMPLETE-001 failure. |
| 024 | Eight flow groups reference interface contracts and step-level completion semantics; unrelated fields carry explicit reasons. | Exposing private algorithm steps as fabricated end-to-end flows or inconsistent completion references fails review. |
| 025 | A small value containing a pointer documents the pointed-to storage lifetime; async retention explicitly extends that lifetime. ABI-sensitive costs use the selected compiler/target. | A shallow struct copy is treated as a deep copy, or four parameters/fixed bytes are assumed universally free: API-ACCESS-001/design failure. |
| 026 | Nine interface groups state nullability, retention, access lifetime and synchronization against concurrent modification. | Const is the only justification while another task can mutate the buffer: API-ACCESS-001 failure. |

## Review example: synchronous completion

`Result Process(Input value)` may return completed output when all promised work
finishes before return. A pointer within `Input` remains a separate borrowed or
owned resource. A queued operation instead returns an admission result and a
correlation ID; its completion event has a distinct meaning. Neither design implies
network delivery or remote execution without that additional contract.

## Review example: slow consumers

A producer publishes one immutable block. Each output holds a bounded reference
and advances independently. Before reuse, every retained reference must be released
or transferred by a safe cancellation protocol. Reference counting, epochs and
RCU-like methods are candidate mechanisms, not automatic proof of bounded retention.
If a source cannot pause, the design must declare the exact overflow policy and
observable data loss or stop behavior. A circular buffer alone establishes no
end-to-end backpressure guarantee.
