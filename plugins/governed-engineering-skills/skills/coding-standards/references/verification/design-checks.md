# Design checks

Before SPEC confirmation, present module responsibilities and non-responsibilities,
common public contracts and private variations, state/type owners, allowed
dependencies and parent mappings. Show actual method alternatives and why the
selected method fits the project's constraints. Review every public interface's
argument access/lifetime and completion semantics; do not infer cost from a global
byte or argument-count limit.

For every affected flow show each stage, execution context, copies, buffers,
capacity/in-flight limits, pressure propagation, ordering and completion. Include
full/partial failure, abnormal events, persistent fault state, recovery discovery,
and bounded shutdown. Distinguish same sample frequency from link speed.

Missing design facts remain unresolved; a filled table is not implementation
evidence. Private algorithm steps need not become public flows. Replacement
implementations share observable contract cases without forcing unused variants.
