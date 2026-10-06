# type-and-state-ownership

| Rule ID | Strength | Applicable conditions | Program requirement |
|---|---|---|---|
| TYPE-001 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Every governed production named type MUST have exactly one semantic owner Module and one source declaration. |
| TYPE-002 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | L0-L2 public types MUST NOT expose adapter bindings, framework handles, wire representations, or storage representations. |
| TYPE-003 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Runtime-state and private-helper types MUST remain private to their owner. Only the owner mutates owner-mutable state. |
| TYPE-004 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | A type containing both a domain reference and an adapter/framework field MUST be either a private L3+ adapter binding or a private L0 composition mapping. |
| TYPE-005 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Type consumers and referenced project types MUST follow the same declared dependency and Port direction rules as code. |
| STATE-001 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Every mutable runtime object has exactly one semantic owner. |
| STATE-002 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | The definition and complete private runtime type reside in the owner's private implementation. |
| STATE-003 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Non-owners MUST NOT obtain state through globals, `extern`, pointers, struct fields, getters, or address passing. |
| STATE-004 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Queries return semantic values or immutable snapshots, never private-state pointers. |
| STATE-005 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Commands ask the owner to mutate state and do not transfer mutable authority. |
| STATE-006 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | An opaque handle is legal only when external code cannot dereference it and all operations remain owner APIs. |
| STATE-007 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Moving a forbidden access into an L0 wrapper does not separate the boundary. |
| TYPE-006 | MUST | Child public contracts. | A parent-owned shared DTO MUST NOT appear in a child public API merely because siblings need similar data. |
