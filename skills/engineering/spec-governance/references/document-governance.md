# Shared document governance

The SPEC owner defines shared identity, format, version, reference and update contracts. Architecture governance owns architecture content; domain modeling owns domain decisions; both use the shared ADR policy. Coding standards owns program requirements. These responsibilities have separate maintained sources.

- Each current design has one editable Markdown source and a stable ID/version. Confirmed references bind ID, version, path and SHA-256; immutable history preserves confirmed bytes.
- A SPEC entry references its requirements, acceptance, discussion and fixed designs. The whole affected collection is confirmed together and bound to the original execution event. Unrelated files do not change that scope.
- Markdown designs own all manifest fields, including extension catalogs. Manifest and diagrams are deterministic products. A hand-edited product cannot hide source drift.
- Unknown applicability is distinct from not applicable and verified. Design feasibility, implementation conformance and acceptance evidence are separate claims.
- Only a completely validated update is effective. Partial files remain unavailable to dependent operations; authorized recovery remains callable.
- Failure requires cause investigation, authorized repair, renewed verification and completion of the original work. Preserved progress or retry availability alone does not satisfy acceptance. Necessary user collaboration records concrete actions and resumes the same work.
- Pure format transitions preserve IDs, semantics, answers, evidence and original authority through complete source/projection proofs. Actual contract changes use the existing confirmation and authorization lifecycle. Unknown history never becomes permission.
