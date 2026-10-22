# ALG-0009: Streaming canonical SPEC input

## Metadata

- Status: proposed; no AI or human algorithm approval is fabricated.
- Owner module: verification_ladder_domain.
- Specification: SPEC-0065 revision 3, REQ-001 through REQ-010.
- Flow: verification-ladder-planning; related algorithms ALG-0004, ALG-0007, ALG-0008.
- Sources: existing project_validation.py, run_storage.py and validation_layout.py; no new sibling dependency.
- Test seams: assess_project, production CLI and existing JSON/run/layout readers.

## Responsibility and boundary design

| Interaction | Producer | Consumer | Parent / mapping | Data and state | Allowed / forbidden |
|---|---|---|---|---|---|
| Validation request | Existing project_validation_adapter | verification_ladder_domain assess_project | Existing project_validation_composition | Existing project/spec/candidate strings and result dict | Existing CLI mapping; no new sibling imports |
| File read | Existing filesystem boundary | Private SPEC reader inside existing verification planner implementation | Existing CLI execution | Regular file descriptor, raw chunks, incremental decoder and digest | Reader-private lifetime; never transfer handle to functional consumers |
| Acceptance parse | Private SPEC reader | Existing spec_contract / acceptance planner | Module-private pure call | Canonical body plus raw-file hash | Raw hash includes audit; owner keeps chain and receipt authority |
| Finite document read | Existing JSON/YAML/run/layout readers | Existing policy/evidence validation | Existing owners | Exact 5,000,000-byte limit | No changes to transport quotas, patch quota or hash chunk size |

## Type and state ownership

No new project-defined named type or persistent state. Existing input/output dict shapes remain. File descriptors, decoder, string buffers, digest, read budget and audit phase are query-local private values owned by the existing implementation. No ABI, storage-format, thread, queue, event or mutable-state authority change.

## Algorithm and invariants

1. Validate canonical relative path and regular-file identity without following a final symlink. Capture device/inode/size/mtime/ctime before opening and verify the opened descriptor matches.
2. Read at most the opening size in fixed-size chunks; update SHA-256 with original bytes while incrementally decoding UTF-8/BOM and universal newlines. A short read or inconsistent closing identity is BLOCKED.
3. A three-phase bounded-tail scanner retains before/audit/after phase, recognizes existing canonical audit markers even across chunks, emits all non-audit body including any suffix, and discards audit content from acceptance parsing. Reject unexpected, repeated or unterminated markers. Owner audit-chain verification remains independent.
4. Return the body and complete raw hash only after successful read consistency checks. Use the same body partition for candidate_text comparisons. Never rewrite the source.
5. Finite readers accept exactly 5,000,000 bytes for format validation and reject greater input with path/actual/limit diagnostics; keep JSON duplicate-key checks and YAML mapping checks.

## Alternatives, costs and evolution

Increasing one global constant alone leaves growing SPECs blocked later; removing only the SPEC guard retains the entire audit in acceptance parsing. The adopted scanner has estimated O(N) I/O/hash cost and O(B+C) retained input memory, where N is full file size, B body size and C chunk/tail size. Existing owner audit processing remains outside this estimate. The existing 30-second adapter timeout stays effective; no hardware timing or overall speedup is claimed. Future audit formats change this scanner and the owner contract; new consumers retain existing CLI/result schemas.

## Faults, recovery and validation

Malformed markers, invalid UTF-8, missing/nonregular/redirected files, I/O failures, short reads and observed file mutations reject without source writes or success publication. Retry opens and verifies current bytes; no evidence/permission reset. SPEC-0065 AC-001 through AC-008 cover exact 1 MiB and 5 MB boundaries, >24.6 MB audit, suffix content, raw hash, mutation/error fixtures, module/SIL/integration and real-file read-only recheck. Fixed-body growing-audit measurements calibrate only the new reader. Windows/Ubuntu matrix remains required CI evidence.

## Human approval

The user adopted streaming/body partitioning and the 5 MB policy in SPEC-0065 DEC-001/002 and explicitly authorized implementation in the next turn. This record remains proposed and does not assert separate algorithm approval. No architectural exception or new public mapping is requested.
