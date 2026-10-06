# Module and public interface implementation designs

The editable sources are Markdown design records under `architecture/designs/modules/` and `architecture/designs/flows/`. The generated manifest projects top-level
`implementation_design: {version: 1, modules: {}, interfaces: {}, flows: {}}`.
Architecture schema 2.1/2.2 remain readable. When adopting coding-standards v1,
populate this extension before confirming affected implementation designs;
legacy absence is a migration gap, not evidence that module designs were checked.
The same manifest records the rule binding described in
[rule versioning](../../coding-standards/references/rule-versioning.md).

`modules` keys exactly match all existing module IDs. `interfaces` has stable IDs
for every public callable contract, referencing its owner module. Each record has
exactly `module_ref`, `status` (`planned`, `implemented`, `verified`),
`evidence_refs` (fixed evidence references), and `groups`.

Each group has `applicability` (`applicable`, `not-applicable`, `unknown`), `value`,
optional `reason` and `refs`. Applicable values are nonempty; not-applicable needs
a reason; unknown remains a blocking design fact. `refs` maps existing catalog
names to ID lists: modules, interfaces, flows, types, state_objects, ports, events.
Reuse these IDs rather than maintaining copies of ownership/type declarations.

## Module groups

| Group | Meaning |
|---|---|
| identity_scope | Existing module, level, parent, source-set and implementation references |
| responsibility | Responsibility and explicit non-responsibilities |
| public_contracts | References to all public interface, port and event contracts |
| invariants | Common observable invariants and applicable rule IDs |
| variants | Actual private variations, selection conditions and shared contracts; N/A if none |
| type_state_ownership | Existing type/state IDs, mutation authority and lifetime |
| implementation_method | Concrete method, alternatives and choice; private algorithm record references |
| dependencies | Actual permitted dependencies, demand ports and parent mappings |
| execution_synchronization | Contexts, serialization, reentrancy and lock scope |
| resource_timing | Capacity, in-flight limit, allocation, stack/time budgets and their sources |
| error_lifecycle | Boundary protection/events, owner fault state, recovery and stop/cancel/drain |
| traceability | Implementation paths/symbols, contract cases and actual verification evidence |

## Public interface groups

| Group | Meaning |
|---|---|
| identity_purpose | Stable ID, public symbol and semantic purpose |
| call_conditions | Preconditions, allowed contexts, ordering and reentrancy |
| parameters | Names, type IDs, meaning, ranges, units, value/address and nullability |
| access_lifetime | Read/write, borrow/transfer/share, retention, validity and concurrent mutation guarantees |
| completion_result | Sync completion or accepted unfinished work; completion layer, results and correlation |
| state_effects | State IDs, commit points and externally visible effects |
| failure_progress | Rejection, failure/partial completion, remaining data and abnormal events |
| resource_timing | Allocation/wait/stack/time contracts; ABI/compiler evidence where applicable |
| verification | Contract cases, rule IDs and implementation/evidence references |

No nullability, borrowing, lock, allocation or synchronous example is a universal
default. A value copy of a pointer-containing object is not a deep copy. Const
does not establish that another context cannot mutate its storage. No universal
argument-count or byte threshold replaces the target ABI and lifetime contract.

`architecture_cli.py gate` validates adopted design records and catalog links;
`render` projects them to generated/implementation-design.md. The checker cannot
infer every public function from arbitrary languages or establish semantics from
prose: review public-symbol inventory, actual callers and implementation methods.
Verified status additionally needs reviewed evidence, not merely nonempty links.

For an applicable interface `parameters` group, `value` is a list with unique
`name` and nonempty `type`, `meaning`, `passing` and `nullability` fields per
parameter. Add range/units where relevant and refer to `access_lifetime` for the
access, retention and concurrency guarantee. An interface with no parameters uses
not-applicable with that reason. Structured group values must be JSON-compatible;
quote dates in YAML and use string mapping keys so generation stays deterministic.

## State-transition subtable

For a module with a state machine, `error_lifecycle.value.transitions` contains
ordered rows with `state_object_ref`, `from_state`, `to_state`, `trigger`, `guard`
and `effects`. All fields are nonempty strings. `state_object_ref` refers to an
existing owned state object; state labels come from its declared state model.
Describe rejected transitions, commit-before-notify effects, fault recovery and
Stop/cancel behavior where relevant. Reuse port/event/interface IDs in group `refs`.
If there is no state machine, record `transitions_applicability: not-applicable`
and a concrete `transitions_reason` inside `error_lifecycle.value`. Ordinary
mutable data alone does not imply a state machine. The source review determines
this applicability; the checker validates provided rows and references.

## Source format

Use the shared SPEC-owner document format. Module/flow records own `manifest_record`
and their `implementation_design`; interface records own their interface design.
Catalog documents own every remaining manifest field, including extensions. The
source index declares each owner once; the generator rejects duplicate ownership.
