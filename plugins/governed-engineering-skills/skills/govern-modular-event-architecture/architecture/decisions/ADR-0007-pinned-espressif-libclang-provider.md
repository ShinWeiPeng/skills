# ADR-0007: Pin the Espressif libclang provider

- **Status:** accepted
- **Date:** 2026-07-31

## Context

The upstream Python `libclang` wheel can load a bundled native library but its
LLVM target set does not provide the Espressif Xtensa backend required to parse
ESP32-S3 translation units. PATH discovery and unrecorded native libraries also
make AST evidence non-reproducible.

## Decision

Use `clang==20.1.5` only as the Python binding and use the official
`esp-clang-libs 20.1.1_20250829` Win64 and Linux-amd64 distributions as the AST
library provider. Record the artifact URL, archive hash, unique library path,
library hash, cache policy, provider version, and binding version in a project
toolchain lock.

The L1 governance engine owns a `LibclangToolchainPort`. The L0 CLI injects an
L3+ `libclang_toolchain_adapter`. Explicit `toolchain install` may download and
atomically create a per-user immutable cache; gate execution only verifies the
existing cache and never accesses the network. Before calling
`clang.cindex.Config.set_library_file`, verify the receipt and actual library
hash, then run an `xtensa-esp32s3-elf` minimal translation-unit probe and an
Xtensa inline-assembly probe.

Provider or capability failures are `CAST001`; malformed lock, platform, cache,
or receipt configuration is `CAST002`; compilation-database coverage and real
translation-unit parsing failures remain `CAST003`. There is no native or
RISC-V fallback.

## Alternatives considered

- Continue using the upstream bundled libclang: rejected because it lacks the
  required Xtensa backend.
- Discover a DLL from PATH: rejected because provenance and identity cannot be
  proven.
- Bundle the native library in the plugin: rejected because it duplicates a
  large platform artifact and obscures official supply-chain provenance.
- Download during every gate: rejected because governance validation must be
  deterministic and offline after explicit provisioning.

## Benefits, costs, and tradeoffs

AST evidence becomes target-capable and reproducible across supported Windows
and Linux hosts. The cost is a one-time per-user download, a platform-specific
cache, and stricter lock and receipt maintenance.

## Risks and mitigations

- Archive substitution is blocked by the pinned archive SHA-256.
- Extraction attacks are blocked by rejecting absolute, traversal, link, and
  special entries.
- Cache tampering is blocked by receipt and library hash verification before
  loading.
- Binding/library mismatch is blocked by pinned versions and a runtime version
  check.
- Backend regressions are blocked by the two Xtensa capability probes.

## Compatibility and migration impact

This changes host governance tooling only. It does not replace PlatformIO,
Xtensa GCC, firmware compiler flags, product modules, runtime scheduling, or
firmware binary composition. C/C++ projects bootstrapped by the skill receive a
toolchain lock and installation instructions; Python-only projects do not
require libclang installation.

## Validation

- Unit-test every lock, download, archive, cache, receipt, version, and backend
  failure mode.
- Verify official Windows and Linux artifacts with Python 3.11, 3.12, and 3.13.
- Run native and Xtensa inline-assembly fixtures.
- Re-run bootstrap, renderer, architecture, release, version-governance, and
  production-fingerprint checks.
- Verify all governed `env_sensing` translation units use `libclang-ast`
  without provider/backend `CAST001` or `CAST003`.

## Approval

- **Approver:** human project owner
- **Approval date:** 2026-08-01
- **Approval reference:** Codex task approval bound to SHA-256 `c2c5c935f4ae015a2665e16c8e63506528fc2503ddc39984a64ff24b653279f6`
