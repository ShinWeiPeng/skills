# Espressif libclang provider pre-code design

## Boundary Design Table

| Interaction | Producer | Consumer | Parent | Producer contract | Consumer contract | Mapping owner | State accessed | Allowed edges | Forbidden edges |
|---|---|---|---|---|---|---|---|---|---|
| Resolve a pinned provider for C/C++ AST analysis | `governance_engine` | `libclang_toolchain_adapter` | `architecture_tooling` | `LibclangToolchainPort` | `LibclangToolchainPort` | `architecture_tooling` | None; the adapter reads a versioned cache and receipt | L0 to L1; L0 to L3+ | L1 to L3+ concrete adapter; L3+ to L1 internals |
| Explicitly install a provider | `architecture_tooling` | `libclang_toolchain_adapter` | `architecture_tooling` | CLI arguments | `LibclangToolchainPort.install` | `architecture_tooling` | Temporary download/extraction workspace and immutable version cache | L0 to L3+ | Gate to network; overwrite of an existing cache |
| Return provider evidence to AST analysis | `libclang_toolchain_adapter` | `governance_engine` | `architecture_tooling` | `LibclangToolchainEvidence` | `LibclangToolchainEvidence` | `architecture_tooling` | None | Adapter result through injected Port | Import or discovery of a library from PATH or the Python package |

## Type Ownership Matrix

| Type | Owner | Declaration | Visibility | Lifetime / mutability | Consumers | Field roles | Compatibility impact |
|---|---|---|---|---|---|---|---|
| `LibclangToolchainPort` | `governance_engine` | `scripts/libclang_toolchain_contract.py` | cross-module Port | one composition / immutable | L0 and provider adapter | operation boundary | Host tooling only |
| `LibclangToolchainEvidence` | `governance_engine` | `scripts/libclang_toolchain_contract.py` | cross-module value | one invocation / immutable | L0, analyzer, adapter | provider identity, versions, paths, hashes, probe target | Evidence schema extends; firmware ABI unchanged |
| `ToolchainProviderError` | `governance_engine` | `scripts/libclang_toolchain_contract.py` | cross-module failure | one failed operation / immutable | L0, analyzer, adapter | diagnostic rule, location, message | Maps only to `CAST001` or `CAST002` |
| `ToolchainLock` | `libclang_toolchain_adapter` | `scripts/libclang_toolchain_adapter.py` | private | one operation / immutable | adapter | supply-chain policy | YAML storage schema v2 |
| `ToolchainReceipt` | `libclang_toolchain_adapter` | `scripts/libclang_toolchain_adapter.py` | private | persisted per cache / immutable after install | adapter | installed artifact identity and integrity | Local file; never committed |

## State Object Ownership Matrix

No project-owned process-global or module-global mutable state is introduced.

| State | Owner | Storage | Lifetime | Readers / writers | Notes |
|---|---|---|---|---|---|
| Download workspace | `libclang_toolchain_adapter` | temporary directory | explicit install command | adapter / adapter | Removed after success or failure |
| Version cache | `libclang_toolchain_adapter` | per-user filesystem | until manually removed | adapter / explicit installer only | Existing invalid cache is never overwritten |
| Receipt | `libclang_toolchain_adapter` | JSON in version cache | cache lifetime | adapter / explicit installer only | Hash-verified before library loading |
| `clang.cindex.Config` binding | external clang binding | framework-owned process state | process lifetime | adapter configures once; analyzer consumes | Library path is verified before the framework call |

## Intended dependency and parent mappings

- `architecture_tooling -> governance_engine`
- `architecture_tooling -> libclang_toolchain_adapter`
- `governance_engine -> LibclangToolchainPort` (demand ownership, not a concrete module edge)
- `libclang_toolchain_adapter implements LibclangToolchainPort`
- `architecture_tooling` maps adapter evidence into the analyzer invocation.

The provider has no dependency on product source, PlatformIO, Xtensa GCC, or firmware
composition. The analyzer target remains `xtensa-esp32s3-elf`.
