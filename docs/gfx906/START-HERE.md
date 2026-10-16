# gfx906 fork: start here

This is the entry point for the experimental Strata gfx906 (wave64) fork. It describes the public, checked-in
starting point. The exact build and limited GPU smoke evidence are indexed in [current state](CURRENT-STATE.md).

## Start with these pages

- [Current state](CURRENT-STATE.md): revisions, known evidence, and open validation.
- [Evidence index](EVIDENCE.md): pinned binary, historical throughput scope, and evidence boundaries.
- [Architecture](ARCHITECTURE.md): how the gfx906 compatibility path relates to upstream.
- [Known limitations](KNOWN-LIMITATIONS.md): explicit unsupported and unverified areas.
- [Fork scope decision](DECISIONS/0001-fork-scope.md): why this fork exists and what it will claim.
- [Upstream synchronization](UPSTREAM-SYNC.md): review upstream changes without duplicating a local patch.
- [Upstream gfx906 build notes](https://github.com/Niko1221/Strata/blob/main/docs/AMD_HIP.md#gfx906-instinct-mi50--mi60-radeon-vii-wave64-built-from-source): inherited build instructions.

## Build entry point

The checked-in upstream build path is documented in `docs/AMD_HIP.md` under “gfx906 (Instinct MI50 / MI60,
Radeon VII): wave64, built from source.” It uses CMake with `-DSTRATA_HIP_GFX906=ON` and builds the `strata` target
with Ninja. Read that section for prerequisites and runtime device requirements. This is an inherited recipe, not a
rebuild result for the fork's present source revision.

The [container guide](CONTAINER.md) shows the archived digest-pinned runtime with external model mounts and
experimental AB/CD kept off by default.

## Evidence boundary

The exact source base, archived native binary SHA-256, OCI index digest, and historical AB/CD throughput scope are
listed in [CURRENT-STATE.md](CURRENT-STATE.md) and [EVIDENCE.md](EVIDENCE.md). The archived figures are tied to that
binary and the public dual-MI50 32 GB / K8-V4 configuration; they do not validate the current source.

The short serial dual-MI50 GPU smoke with a cached continuation used a source-equivalent binary for pre-merge
main commit `64185a40962121b9adfc20e0e1a45b634cfeb472` (native SHA-256
`73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`); see the [separate
receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-gpu-smoke.json). It does not validate the
post-merge main at the 2026-10-17 checkpoint (audited checkpoint SHA
`73e01b3a5f1c577899e3f668e7e913759a1f7455`), for which no rebuild or GPU smoke is recorded. The archived AB/CD
opt-in delta is not integrated into current main, and token/state parity remains open. Use exact source and artifact
identities in any new report. Historical throughput measurements are not evidence for the present source.

## Checked-in CLI

The checked-in gfx906 command entry point is [`tools/gfx906.py`](../../tools/gfx906.py). Run
`python tools/gfx906.py doctor` and `python tools/gfx906.py test-cpu` without a GPU. The `build-gfx906` and
`bench-p2`/`bench-p3`/`bench-p4` commands print dry-run plans by default; their `--apply` modes require explicit
inputs. `bench-validate` checks the structure of a versioned evidence record, and `report` renders one. The HTTP
load commands do not establish native decode occupancy or a cached strict-overlap benchmark.
The [benchmark format guide](../../benchmarks/gfx906/README.md) explains the required raw-evidence review.
For a build dry run, provide the paths to your ROCm and llama.cpp installs, for example
`python tools/gfx906.py build-gfx906 --rocm-root /opt/rocm --ggml-dir /path/to/llama.cpp`.

## Conditional workflows

The checked-in [`.agents/skills/`](../../.agents/skills/) guides cover gfx906 builds, inference benchmarking, batching validation, and release
preparation. They apply only when their matching task is explicitly in scope. They do not install dependencies,
obtain hardware, publish releases, or add commands that are absent from the repository.
