# Rule verification map

| Rule IDs | Design | Static capability | Runtime evidence when applicable |
|---|---|---|---|
| MOD-*, TYPE-*, STATE-* | Owner, boundary, dependency and common contract review | Existing architecture/type/state analyzers on supported languages; caller review elsewhere | Shared contract cases and opaque-handle/lifetime behavior |
| MEM-* | Budgets, allocation strategy, owner/borrow/share/reclaim design | Lifetime and error-path source review; tool support depends on language | Capacity exhaustion, outstanding readers, cancel/timeout and target allocation budgets |
| BND-* | Trust boundaries, ranges, size calculations and invalidated assumptions | Proved type/static bounds or actual runtime checks | Overflow, truncation, invalid lengths and concurrent invalidation |
| ERR-* | Protection, event, owner state and recovery obligations | Verify all error exits and bounded reporting | Repeated/full/overwritten events, persistent state, delayed recovery and real-time cost |
| FLOW-* | Concrete method, every buffer, pressure reach, rate, sequence, completion and stop | Compare actual copies/callers/contexts with the design | Both batch triggers, partial writes, refusal, fan-in interleavings, slow fan-out and bounded drain |
| API-* | Access/lifetime, synchronous/accepted/transport/remote completion | Public-contract and call-site review, ABI output when required | Sync/async/partial failure, held references and timing claims |
| EXEC-* | Confirmed platform, candidates and resource/timing budget | Build/ISA/ABI and supported analysis; no generic speed proof | Representative target baseline, counters/equivalent for mechanism claims, full flow budgets |

These patterns cover all catalog IDs; the project's applicability result expands
them to exact IDs and evidence references. The four-column catalog is normative;
this map records checks and limits. A missing tool capability is not a waiver.
ADR checks use plugin references/adr/checks.md. One-time migration uses SPEC-0040's
mapping and source diff review rather than changing daily program requirements.

## OS rules

OS-CAP-001, OS-EXEC-001, OS-CHAN-001, OS-SYNC-001, OS-RES-001, OS-TIME-001 and OS-LIFE-001 map to the architecture-owned os-execution-checks.md. Design validates feasibility and contracts; implementation validates code/build and fault paths; acceptance obtains risk-appropriate target measurements. Retain separate rule ID, design version, AC and evidence references. Format/evidence-presence checks do not certify runtime correctness.
