# Document update and recovery workflow

1. Read the current confirmed collection and retained execution binding. Prepare only the affected design candidates and deterministic generated products. Present concrete module, interface, flow and execution methods before confirmation.
2. Validate every candidate's format, references, applicability, domain feasibility and source/product consistency. Reserve an operation ID, original bytes, base hashes, prepared bytes and binding through `prepare_update`; preserve immutable history.
3. Recheck current authority and every target base before effects. Apply through the managed entry. Journal each completed replacement; do not call a partial set effective.
4. Validate the entire resulting collection, then mark effective. Ordinary readers reject updating/incomplete collections. The reserved recovery entry stays available without first requiring the failed acceptance gate to pass.
5. On failure read the recorded cause and reproduce the failing operation. Repair within the existing scope, then resume the same reserved update. Skip replacements already matching their prepared bytes. Preserve concurrent edits and resolve the actual difference before retrying.
6. For runtime acceptance failures use diagnosing-bugs to reproduce/isolate the cause, then rerun the selected validate-on-device scenario under verification-ladder. Incomplete evidence requires repairing capture or obtaining the necessary user action. Reassess the original criteria; no threshold relaxation or host substitution.
7. Complete only after original work and required evidence pass. Actual contract changes reopen through the SPEC owner; necessary external collaboration names the action, expected evidence and continuation.

Discussion owner recovery uses `document_candidates.py` with `operation: resume-owner-write`, the selected `working_reference` and reserved `operation_id`. It checks the stored original and intended projections, repairs the audit lineage with an explicit recovery event, and grants no product execution. Invalid references and candidates outside the selected SPEC fail before writes.
