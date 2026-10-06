# OS checks by phase

| Phase | Required checks | Evidence |
|---|---|---|
| Design | All nine applicability categories; platform abilities/call limits; seven execution groups; module/Task mapping; channel delivery/ownership/full/timeout/Stop; synchronization/deadlock/priority inversion; simultaneous resource budgets; conservative timing feasibility; readiness/restart; supported real-time candidate comparison. | Source references, project units and budget basis, human selected methods, supported scheduler analysis; no premature requirement for measurements produced by implementation. |
| Implementation | Code matches the confirmed IDs/versions and rule catalog; OS API/handles remain behind adapters; builds and applicable channel full/timeout, creation failure, cancellation and repeated restart tests. | Tool findings, independent source/caller review, regression tests and declared remaining target evidence. |
| Acceptance | Required deployed stack margins, queue/wait/timing, peak/slow consumer, safe Stop/restart and resource accumulation measurements. | Target evidence selected by verification-ladder and validate-on-device; host results cover only their supported claims. |

Every check records rule IDs, design ID/version, AC, method, environment and evidence status. Tools validate format/binding and evidence presence; reviewers validate semantics and budgets; runtime tests establish observed behavior. The OS-DESIGN-001 checker reports these documentary checks separately from semantic/runtime claims.

Missing facts block dependent decisions; independent work continues. Required acceptance still must pass before completion. Failures follow diagnosing-bugs, repair within the current grant, re-run the relevant verification-ladder/validate-on-device scenario and the original acceptance criterion. Necessary human collaboration specifies the action and required artifact; resume analysis when obtained.

OS isolation reuses MOD-DEP-005, MOD-DEP-006 and TYPE-002. Seven new rule IDs map respectively to capability, mapping, channels, synchronization, resources, timing and lifecycle checks. No global byte, time, Task-count or RAM threshold is introduced.
