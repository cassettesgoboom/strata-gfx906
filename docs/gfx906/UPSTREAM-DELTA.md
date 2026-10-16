# gfx906 upstream delta

This note maps gfx906-relevant features to public upstream commits observed on 2026-10-16. It describes source history only; it does not identify the source commit used to build the archived container.

## Public fork updates

- [PR #11](https://github.com/cassettesgoboom/strata-gfx906/pull/11) adds the README's archived dual-MI50 cached multi-agent measurement table and links the canonical evidence and provenance. It changes documentation only; the archived image and engine are unchanged.
- [PR #12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) introduced a CPU-only comparator for supplied
  serial-OFF / AB/CD-ON native traces. Its v1 singular-token record format is superseded by
  [PR #17](https://github.com/cassettesgoboom/strata-gfx906/pull/17), which uses `native_transaction_trace_v2`:
  ordered native token-ID vectors per committed transaction/window and persistent-state hashes only at window end.
  V1 records are rejected unless regenerated or migrated with original transaction-boundary evidence. The
  comparator output always states `runtime_parity_claim=false`; it cannot authenticate capture or establish runtime
  token/state parity, and does not port AB/CD or change the image.
- [PR #15](https://github.com/cassettesgoboom/strata-gfx906/pull/15) adds an unused host-side transaction lifecycle registry and focused C++ CPU test for slice ownership, snapshots, registry-bound handles, lifecycle transitions, accepted-prefix limits, and drain-before-reuse. Hosted CI passed 42 Python CPU tests and the C++20 transaction test. The registry is not integrated with the verifier or scheduler; this scaffolding does not prove GPU overlap, device completion/drain, or runtime token/state parity and does not change the image.
- [PR #17](https://github.com/cassettesgoboom/strata-gfx906/pull/17) updates the comparator and synthetic fixtures
  to v2 transaction-window token vectors and window-end state comparison. The current
  `python tools/gfx906.py test-cpu` suite passes 44 CPU tests. This remains a comparison contract, not runtime evidence.
- [PR #19](https://github.com/cassettesgoboom/strata-gfx906/pull/19) extends the unused CPU-side transaction
  registry with two-phase commit intent and result. `begin_commit` validates and copies accepted-prefix intent into
  registry-owned state, and its accessor returns a copy; the slice remains undrained while device commit may run.
  `finish_commit` records success only after the runtime observes it. A post-launch failure or abort requires
  explicit device drain followed by session recovery/discard acknowledgement before retirement. Validation is 44
  Python tests plus a separate focused C++20 transaction test. The contract remains unwired to `Verifier`/scheduler and implements no inference,
  QSA rollback, GPU transaction isolation, or parity.

These fork PRs document archived evidence and add CPU-side future-validation scaffolding. They do not alter the
upstream feature history below or supply new source-to-image provenance. The
[current-main blockers in Issue #1](https://github.com/cassettesgoboom/strata-gfx906/issues/1) remain: the lifecycle
registry is not wired into `Verifier` or the scheduler; per-slice graph, staging, and poll ownership is not
integrated; and the registry's commit-intent/result and recovery gates are not connected to actual device work.
Ordinary rejection restores the QSA tail and re-appends accepted keys, but it is not general rollback for failed or
aborted same-session overlapping slices: indexer appends also mutate dead, pooled, and block-position state, and
GDN commit mutates persistent recurrence state in place. The registry requires drain and session recovery/discard
after a post-launch failure or abort, but it does not implement these actions or resolve that rollback gap. The
single next source gate is to integrate this lifecycle and recovery behavior in the current-main verifier/scheduler,
then use a pinned current-main build for isolated serial-versus-AB/CD GPU checks of ordered native token IDs and window-end state
hashes. Keep AB/CD opt-in until those runtime checks pass.

## Feature-to-commit map

| Feature | Upstream commit (date) | Scope and relationship |
| --- | --- | --- |
| AMD gfx906 build support | [`9ff290b493a2`](https://github.com/Niko1221/Strata/commit/9ff290b493a2aaf6a784af69190c82f903ebf221) (2026-10-03) | Opt-in HIP support for gfx906 devices. This establishes public source support, not validation of a particular image or workload. |
| K8/V4 KV cache | [`3597c47ff8cd`](https://github.com/Niko1221/Strata/commit/3597c47ff8cd490dccfdafa2bd9d9b80ba9aa255) (2026-09-29) | Adds the hybrid K8/V4 cache and `--kv k8v4`. |
| Refreshed-residency batch servicing (#1102 equivalent) | [`7ef55e19599f`](https://github.com/Niko1221/Strata/commit/7ef55e19599f1ef009894b3260b40cdbe0d59ba9) (2026-10-07) | Upstream #1118 changes the batch graph/service decision to use per-window `ar_on()` residency. Its commit message identifies #1102 as the same fix for `run_slot_rows()` and `batch_poll()`; #1118 also updates `service()`. This is an upstream equivalent behavior, not evidence that the archived binary contains either commit. |
| Serial batch-MTP windows | [`a0116b2782a5`](https://github.com/Niko1221/Strata/commit/a0116b2782a5b82622358c04a06496485d12b2d6) (2026-10-12) | Adds/retains serial MTP windows with `STRATA_BATCH_MTP_SERIAL=1` or `--batch-groups 1`; the commit states that the default layer-split pipeline takes precedence over `--batch-mtp`. This is the current upstream behavior, not a source attribution for the archived image. |

## Relationship to #1242 and #1253

As observed on 2026-10-16, upstream PR [#1242](https://github.com/Niko1221/Strata/pull/1242) is open and concerns concurrent image-position isolation and batch-MTP draft paths; PR [#1253](https://github.com/Niko1221/Strata/pull/1253) is open and concerns serial multi-GPU batch MTP. The public upstream commit above documents serial windows and their current mode-selection policy, but does not establish that either open PR was merged unchanged or that it reproduces the archived experimental build. Treat the PRs and the current upstream commit as related source history, not interchangeable build provenance.

## Archived build boundary

The archived binary's exact coherent source commit is unknown. Public tag metadata, executable hashes, and current upstream feature presence do not establish which commits or patches produced it. The archived AB/CD path remains opt-in; its source is unpublished and its exact-token and recurrent-state parity remain open. Do not infer that current upstream contains that path or that the archived binary can be reproduced from this source tree.

## License

The [upstream LICENSE](https://github.com/Niko1221/Strata/blob/main/LICENSE) identifies Strata as MIT licensed. Retain its copyright and permission notice in redistributions. ROCm components have separate component-level licensing; see [AMD's ROCm license table](https://rocm.docs.amd.com/en/latest/about/license.html) and the caveat in [RELEASES.md](RELEASES.md).
