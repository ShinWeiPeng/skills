# module-boundaries

| Rule ID | Strength | Applicable conditions | Program requirement |
|---|---|---|---|
| MOD-DEP-001 | MUST | Governed modules; apply the stated level and role conditions. | L1 modules MUST name an L0 parent. L2 modules MUST name an L1 parent. |
| MOD-DEP-002 | MUST | Governed modules; apply the stated level and role conditions. | L0-L2 siblings MUST NOT depend directly on one another. Their parent coordinates public input ports and output events. |
| MOD-DEP-003 | MUST | Governed modules; apply the stated level and role conditions. | L0 orchestration depends on L1 public contracts. L1 depends on child L2 public contracts. |
| MOD-DEP-004 | MAY | Governed modules; apply the stated level and role conditions. | A composition module MAY reference concrete adapters only to construct and wire the system. |
| MOD-DEP-005 | MUST | Governed modules; apply the stated level and role conditions. | A functional module MUST NOT reference an L3+ implementation or expose framework-specific types. |
| MOD-DEP-006 | MUST | Governed modules; apply the stated level and role conditions. | A demand-side L0-L2 module owns each port needed from hardware, OS, storage, network, time, or another external technology. An L3+ adapter implements that port. |
| MOD-DEP-007 | MAY | Governed modules; apply the stated level and role conditions. | L3+ adapters MAY depend on the public contracts they implement and on declared technical modules. |
| MOD-DEP-008 | MUST | Governed modules; apply the stated level and role conditions. | Private pure calculations and module-internal helpers do not require ports. |
| MOD-LEVEL-001 | MUST | Module level L0. | Compose the system and coordinate L1 domains; role `composition`, `orchestration` |
| MOD-LEVEL-002 | MUST | Module level L1. | Own a functional domain and coordinate its L2 components; role `domain` |
| MOD-LEVEL-003 | MUST | Module level L2. | Implement an independently testable functional component; role `component` |
| MOD-LEVEL-004 | MUST | Module level L3+. | Implement OS, hardware, storage, network, framework, or shared technical capabilities; role `adapter`, `technical` |
| MOD-LEVEL-P001 | MUST | Governed logical architecture. | Levels are semantic, not mandatory empty folders. Omit a level that has no responsibility. Use feature-first organization in L0-L2 and technical organization in L3+. |
| MOD-LEVEL-P002 | MUST | Governed logical architecture. | L0 owns composition, orchestration, and sibling mapping; it MUST NOT own a child domain's mutable runtime. L1 owns a functional domain, its public contracts, invariants, and domain runtime. L2 owns independently testable components and private algorithm state. L3+ owns external-technology representations and bindings. |
| MOD-MAP-001 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Directly pass a producer-owned contract only when the consumer may legally depend on that owner and the contract already expresses the consumer's required semantics. |
| MOD-MAP-002 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | When direct use creates a sibling or child-to-parent dependency, each side owns its own semantic contract and their parent performs explicit mapping. |
| MOD-MAP-003 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | A parent-private mapping type may exist only inside composition or orchestration and MUST NOT become a child public parameter, field, or return type. |
| MOD-MAP-004 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | Primitive and external standard types do not require wrapper DTOs merely because they cross modules. |
| MOD-MAP-005 | MUST | Governed production types and runtime; apply stated role/visibility conditions. | DTOs contain only contract semantics; private runtime, adapter handles, and framework objects are forbidden. |
| MOD-META-001 | MUST | Architecture descriptions without a separate runtime product requirement. | Do not add a runtime description struct or expose documentation metadata through the product ABI. |
| MOD-CONTRACT-001 | MUST | 模組呼叫端與可替換實作 | 呼叫端依共同公開契約；內部算法可變部分不要求呼叫端讀私有狀態或依算法分支才能滿足共同語意。 |
| API-COMPLETE-001 | MUST | 公開呼叫或提交操作 | 在返回前已完成者可同步提供結果；尚未完成者只宣告接受，後續完成/失敗能關聯；模組、傳輸與遠端完成不得混同。 |
| API-ACCESS-001 | MUST | 傳值、傳址、借用及保存引用 | 讀写權限、有效期間、是否保存、所有權與並行修改保證符合介面契約；const 不能代替底層資料的同步保證。 |
| MOD-OBS-001 | MUST | Runtime evidence and test instrumentation. | Keep native trace, Serial, TCP, test logging, statistics export, clocks, process execution, and evidence storage in L3+ adapters. |
| MOD-OBS-002 | MUST | Runtime evidence and test instrumentation. | Let the demand-side L0-L2 module own the observability or test-control port. Do not let a functional module depend on ETW, perf, Instruments, Serial, TCP, a logger, or a concrete test framework. |
| MOD-OBS-003 | MUST | Runtime evidence and test instrumentation. | Wire test-only adapters in a test composition root. Release composition roots must not include test command parsers or test protocol wiring. |
| MOD-OBS-004 | SHOULD | Runtime evidence and test instrumentation. | Prefer observation at task, Port, and Event boundaries. If a hot internal path needs instrumentation, use a demand-owned metrics port or compile-time test hook whose release wiring is absent. |
| MOD-DEP-009 | MUST | All governed module dependencies. | Dependency cycles are forbidden. |
