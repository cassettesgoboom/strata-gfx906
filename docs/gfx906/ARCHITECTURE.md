# gfx906 architecture notes

gfx906 (MI50, MI60, Radeon VII) uses 64-lane wavefronts. The existing upstream gfx906 path is a separate opt-in HIP
compatibility build around CUDA-shaped engine sources; it maps the logical 32-lane warp assumptions through a
compatibility layer and has gfx906-specific kernel paths. See upstream [`docs/AMD_HIP.md`](../AMD_HIP.md#gfx906-instinct-mi50--mi60-radeon-vii-wave64-built-from-source)
and [`include/strata/platform/hip_compat/`](../../include/strata/platform/hip_compat/) for implementation details.

The build option is `STRATA_HIP_GFX906`; it is separate from `STRATA_ENABLE_HIP`. The checked-in build recipe and
dependencies are maintained in upstream `docs/AMD_HIP.md`. Do not infer that the fork's present source is rebuildable
from the existence of that recipe or a previously published native binary.

This page records architecture context, not validation. The fork has no GPU validation of upstream v0.1.44.1. Public
historical throughput evidence is limited to the pinned binary, dual MI50 32 GB, and K8/V4 configuration. It does
not validate current source; the archived AB/CD opt-in delta is not ported here and token/state parity remains open.
See [current state](CURRENT-STATE.md), [evidence index](EVIDENCE.md), and
[known limitations](KNOWN-LIMITATIONS.md).
