---
name: gfx906-build
description: Build or investigate Strata's gfx906 HIP wave64 target when a gfx906 build task is requested. Does not imply GPU access or a successful runtime validation.
---

# gfx906 build workflow

Use this only for an explicitly requested gfx906 build or build investigation. Read
[`docs/gfx906/START-HERE.md`](../../../docs/gfx906/START-HERE.md), its current-state and limitation pages, and the
upstream build section in [`docs/AMD_HIP.md`](../../../docs/AMD_HIP.md#gfx906-instinct-mi50--mi60-radeon-vii-wave64-built-from-source).

Use the repository's documented CMake option `STRATA_HIP_GFX906=ON` and `strata` target. Do not invent setup or
doctor commands: upstream documentation says setup does not build gfx906. Keep source SHA, toolchain, build
configuration, and resulting artifact hash together in the report.

Report compilation separately from device enumeration, runtime smoke, correctness, and performance. If a gfx906 GPU
is unavailable, stop at the requested CPU/build checks and state that GPU validation was not run. Do not imply that
the published artifact SHA prefix `ae93901c` can be rebuilt from the current source until that has been demonstrated.
