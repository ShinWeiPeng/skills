# ADR-0008: Pin the Espressif libclang provider

- **Status:** accepted
- **Date:** 2026-07-31

## Context

Governed ESP32-S3 translation units require an LLVM library with Espressif's
Xtensa backend. Implicit native-library discovery cannot prove capability or
supply-chain identity.

## Decision

Distribute a demand-owned provider contract and an L3+ adapter with the
`govern-modular-event-architecture` skill. Pin `clang==20.1.5` as bindings and
the official `esp-clang-libs 20.1.1_20250829` Win64/Linux-amd64 artifacts as the
native provider. Explicit install creates an immutable per-user cache; gates
verify it offline and load only its hash-verified library. Capability probes
must parse `xtensa-esp32s3-elf` C and Xtensa inline assembly.

## Alternatives considered

- Bundled upstream libclang: lacks the required Xtensa backend.
- PATH discovery: cannot provide reproducible identity.
- Gate-time download: makes validation network-dependent.
- Native or RISC-V fallback: would not validate the governed target.

## Benefits, costs, and tradeoffs

The plugin gains reproducible target-capable AST evidence. Users and CI must
perform a one-time platform-specific install and retain the version cache.

## Risks and mitigations

Pinned archive and library hashes prevent substitution; safe extraction rejects
unsafe archive entries; receipt verification detects cache mutation; explicit
binding prevents fallback; target probes detect backend regressions.

## Compatibility and migration impact

The change affects host governance tooling only. PlatformIO, Xtensa GCC,
firmware composition, product modules, and target scheduling are unchanged.

## Validation

Run provider unit tests, Windows/Linux artifact verification on Python
3.11-3.13, native and Xtensa fixtures, bootstrap/renderer gates, plugin release
gates, version governance, production fingerprint checks, and the complete
`env_sensing` development gate.

## Approval

- **Approver:** human project owner
- **Approval date:** 2026-08-01
- **Approval reference:** Codex task approval bound to SHA-256 `680f5f5cb7bd58f673123ede36d36b5a827b5ec086d78581b419356f3a9cfcbe`
