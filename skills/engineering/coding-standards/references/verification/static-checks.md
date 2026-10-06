# Static checks

Check unique rule IDs, four-column records, applicability references and matching
catalog versions. Validate manifest references and generated views through the
existing architecture CLI. For supported languages use actual dependency/type/
state analysis and inspect call sites for private-state escape and algorithm leaks.
Preserve the C/C++ AST requirement; lexical matches cannot prove ownership safety.

Compare actual code with the presented method: new buffers, copies, ownership,
thread/task contexts, event publication, completion and error paths must agree.
Type wrappers and const alone do not prove bounds or concurrent immutability.
Unsupported analysis requires explicit review and cannot be reported as automated
PASS. Inspect compiler/ABI results where a constrained path requires cost evidence.
