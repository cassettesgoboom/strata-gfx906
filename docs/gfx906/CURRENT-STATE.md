# gfx906 current state

**Recorded:** 2026-10-18. **Stage:** public gfx906 foundation and current-main build fixes are merged. PR
[#22](https://github.com/cassettesgoboom/strata-gfx906/pull/22) merged a mechanical single-window
`Verifier::WindowContext` refactor. Its source commit passed an isolated gfx906 HIP build and CLI load, and
both hosted CPU checks passed. PR [#25](https://github.com/cassettesgoboom/strata-gfx906/pull/25) merged
opt-in request-ID/native-leg correlation; its changed native parser passed an isolated gfx906 HIP build and
both hosted CPU checks passed. PR [#26](https://github.com/cassettesgoboom/strata-gfx906/pull/26) adds a
separate opt-in serial-window trace; the base request-ID trace still supports batch. A separate pre-merge
source-equivalent binary passed a short serial MI50 GPU smoke. PR [#11](https://github.com/cassettesgoboom/strata-gfx906/pull/11) adds archived MI50 measurements.
PR [#12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) introduced a CPU-only AB/CD trace
comparator; [#17](https://github.com/cassettesgoboom/strata-gfx906/pull/17) supersedes its
v1 record format with ordered token vectors per committed transaction/window and state hashes at window end.
PR [#15](https://github.com/cassettesgoboom/strata-gfx906/pull/15) adds an unused host-side transaction lifecycle
registry; [#19](https://github.com/cassettesgoboom/strata-gfx906/pull/19) adds two-phase commit intent/result,
accepted-prefix validation and copy, and explicit drain/recovery gates to that CPU contract. The registry remains
unused by the runtime. At the PR #19 checkpoint, `python tools/gfx906.py test-cpu` passed 44 Python tests, the
focused C++20 transaction test passed, and the main CPU suite had 60 tests. These
changes do not integrate AB/CD into the runtime, establish GPU overlap or
parity, or change the published image.

PR [#47](https://github.com/cassettesgoboom/strata-gfx906/pull/47) merged at
`3d63da0ab60f3a51208d75a9c08ac4e70174d45d`. It makes the v3 comparator reject
serial/candidate pairs with different evidence classes and reports
`capture_authenticated: false` on equality. The 78-test CPU suite, both hosted
PR checks, and post-merge main workflow `39086600822` passed. This closes a
comparator-labeling gap only; it adds no native capture producer and proves no
runtime parity. PR [#48](https://github.com/cassettesgoboom/strata-gfx906/pull/48)
merged at `a2c308c0be339f7f9fcc5d4a555c4291bc87fdf2`; it documents the pinned
schema-test dependency required in a fresh environment. Its post-merge hosted
CPU workflow passed. Neither PR changes the native runtime or published image.

PR [#31](https://github.com/cassettesgoboom/strata-gfx906/pull/31) merged at
`6cb3c586833966b48e4df77180552b42331e429c`. It replaces the watchdog release
registry's raw `Verifier*` access with fixed-lifetime controls for publishing
wait flags and draining the registered compute/copy streams. Stream query
errors and timeouts are reported as failed drains. The deterministic C++ test
is included in the hosted CPU workflow. Before merge, PR source commit
`429d2a95ac12b753cc81fe3ace93f51bb2bf3f8c` compiled the full `strata` gfx906
HIP target in an isolated 6 GiB container with no GPU devices; the output
hash and toolchain are in the [build receipt](../../benchmarks/gfx906/receipts/2026-10-17-verifier-release-control-build.json).
This is compile and CLI-help evidence only, not GPU runtime validation. The
change does not resolve the separate raw diagnostic callback lifetime or
general graph/session teardown contract, and it does not port AB/CD. Issue #24
remains open.

**Reviewed current-source snapshot (checked 2026-10-18):** fork `main` at the engine-source review resolved to
[`3f076fea5a98f69d2fec1d364b21380eb1a67e95`](https://github.com/cassettesgoboom/strata-gfx906/commit/3f076fea5a98f69d2fec1d364b21380eb1a67e95),
merged by PR [#40](https://github.com/cassettesgoboom/strata-gfx906/pull/40). Earlier PRs
[#37](https://github.com/cassettesgoboom/strata-gfx906/pull/37), [#38](https://github.com/cassettesgoboom/strata-gfx906/pull/38),
and [#39](https://github.com/cassettesgoboom/strata-gfx906/pull/39) updated public state, parity-contract/tests,
and sanitized benchmark configuration snapshots. Later PR [#42](https://github.com/cassettesgoboom/strata-gfx906/pull/42)
refreshed documentation, and PR [#43](https://github.com/cassettesgoboom/strata-gfx906/pull/43) registered existing
native trace helper tests with CMake/CTest. Those follow-up changes do not modify inference runtime behavior, add
a native AB/CD runtime port, or provide new GPU/parity evidence. Fork main retains ancestry from
[upstream `Niko1221/Strata`](https://github.com/Niko1221/Strata), and the latest upstream release checked here is
[v0.1.45](https://github.com/Niko1221/Strata/releases/tag/v0.1.45).

**Reviewed engine-source snapshot (checked 2026-10-17 UTC):** the reviewed fork `main` at that source review was
[`af45b70bf5cb7e61a0e0825c632397190a97e18b`](https://github.com/cassettesgoboom/strata-gfx906/commit/af45b70bf5cb7e61a0e0825c632397190a97e18b),
with [PR #36](https://github.com/cassettesgoboom/strata-gfx906/pull/36) just merged. This update changes docs only
and does not change engine source. Upstream's
latest official release is [v0.1.45](https://github.com/Niko1221/Strata/releases/tag/v0.1.45); its tag and
current [`main`](https://github.com/Niko1221/Strata/commit/477ac13cbe8e582c20484871ce459d20d82df09d)
resolve to `477ac13cbe8e582c20484871ce459d20d82df09d`. Fork draft [PR #4](https://github.com/cassettesgoboom/strata-gfx906/pull/4)
and [issues #1](https://github.com/cassettesgoboom/strata-gfx906/issues/1) and
[#24](https://github.com/cassettesgoboom/strata-gfx906/issues/24) remain open; upstream [PR #1242](https://github.com/Niko1221/Strata/pull/1242)
and [PR #1253](https://github.com/Niko1221/Strata/pull/1253) remain open. These public revision and status facts do
not add GPU or parity validation.

- **Source base:** upstream `296b59d2f73c8f04a805df29c2fa97655adace78`.
- **Archived native binary:** SHA-256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`.
- **Archived OCI index:** `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- **Public fork:** main retains upstream ancestry and [PR #2](https://github.com/cassettesgoboom/strata-gfx906/pull/2) is merged. The current `test-cpu` suite passes 78 tests; this does not validate GPU execution. A clean-checkout onboarding review used only public files.
- **Merged build fixes:** [PR #6](https://github.com/cassettesgoboom/strata-gfx906/pull/6) merged alias fix `8c30f4744f8df7a7ce71805959e426116b271410`; [PR #7](https://github.com/cassettesgoboom/strata-gfx906/pull/7) merged the Blackwell W4A4 CMake exclusion `b65fdb01810fa11914a2c21bef5468b5dee5a623`.
- **Pre-merge main-equivalent build receipt:** combined gfx906 HIP Release/Ninja build succeeded in an isolated networkless container with a 6 GiB memory limit. It used ROCm clang `23.0.0git`, GGML/llama.cpp commit `3cf03257f219afbe7334045ff7c6a06ac68c627d`, and source base `02f500b8056f9cc7af27dfa577476e69eaab75a6` before the merged fixes. The associated smoke receipt maps the tested binary to pre-merge fork main `64185a40962121b9adfc20e0e1a45b634cfeb472`; it is not a build of post-merge main at the earlier 2026-10-17 checkpoint (audited checkpoint SHA `73e01b3a5f1c577899e3f668e7e913759a1f7455`). The newly produced local binary SHA-256 is `73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`. Its CPU-only `--help` path succeeded and 30 CPU tooling tests passed. See the [machine-readable build receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-equivalent.json) and [exact patch bundle](../../benchmarks/gfx906/receipts/2026-10-16-current-main-equivalent.patch) for toolchain, source, command, and artifact details.
- **Build and smoke boundary:** this build did not reproduce the pinned historical benchmarked binary (`ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`). The separate [GPU smoke receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-gpu-smoke.json) identifies its source-equivalent fork main as pre-merge commit `64185a40962121b9adfc20e0e1a45b634cfeb472` and the tested native binary SHA-256 as `73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`. It records short serial inference on dual MI50: 146 generated tokens on a first request, then 130 on a continuation with 70 native reused prompt tokens; MTP accepted/offered totals were 173/208. The server and binary were mounted into the archived runtime image. No new image was published. No rebuild or GPU smoke is recorded for post-merge main at the 2026-10-17 checkpoint (audited checkpoint SHA `73e01b3a5f1c577899e3f668e7e913759a1f7455`). These short requests do not establish sustained performance, batch AB/CD, or exact token/state parity; archived benchmark measurements below remain scoped to the pinned binary.
- **Archived throughput evidence:** the README table now records six cached multi-agent runs from the published image: P2 serial at ~96K (38.43 strict / 33.35 whole-wave tok/s) and ~152K (45.19 / 36.19); P3 serial at ~99K (52.46 / 41.67) and ~152K (47.37 / 35.93); P4 AB/CD opt-in at ~33K (67.10 / 55.73) and 102K (71.17 / 53.94). The P4 102K run emitted 512/512/512/473 tokens, with the fourth lane stopping naturally. Strict overlap is an SSE-derived estimate; different rows do not establish causal speedup. P2 at ~192K with cached histories and 65-token continuations is capacity evidence only. See [EVIDENCE.md](EVIDENCE.md) for the full table and caveats. All figures apply to the archived binary and public dual-MI50 32 GB / K8-V4 scope.
- **AB/CD comparator boundary:** PR #17 updates the CPU-only comparator to v2 `native_transaction_trace_v2`
  records: each committed transaction/window carries a non-empty ordered `native_token_ids` list, with
  persistent-state hashes compared only at `commit_window_end`. The old v1 singular-token format is rejected;
  existing traces need regeneration or migration backed by original transaction-boundary evidence. Output
  always has `runtime_parity_claim=false`; synthetic equality checks comparator behavior only. The tool cannot
  authenticate capture or prove runtime parity. No current-main AB/CD port or runtime parity validation is included.
- **Transaction lifecycle boundary:** PR #15 introduced a host-side registry for two disjoint row slices, immutable slot/token/position snapshots, and lifecycle transitions. PR #19 adds two-phase commit intent/result: `begin_commit` validates and stores accepted prefixes in registry-owned state; `finish_commit` records success only after the runtime observes the device result. The slice remains undrained during commit. Post-launch failure or abort requires explicit device drain and session recovery/discard before retirement. The accessor copies the validated accepted-prefix intent so later caller-array changes cannot alter it. Validation is 44 Python tests plus a separate focused C++20 transaction test. This remains scaffolding: it is not wired into `Verifier` or the scheduler, and does not implement QSA rollback, GPU transaction isolation, inference, or parity.
- **PR #22 compile-only build:** the merged one-window `Verifier::WindowContext` mechanical refactor is
  source commit `22cae852bbbe433c1cdf65ab4daaef7bfeaf650d`. Its isolated gfx906 HIP Release/Ninja `strata`
  build passed, producing native SHA-256
  `cb7f37249a34b7e8d24232f4e57da9a035c473d5bd598e83b53bad8d781c8db2`; `strata --help` loaded. The
  44-test CPU suite and both hosted CPU checks passed. This is compile and CLI evidence only: there was no
  GPU runtime test or inference, no two-slice AB/CD isolation, no token or recurrent-state parity check, and
  no new image publication. The PR comment records the build details.
- **PR #25 native trace build:** opt-in request-ID transport/native-leg correlation passed an isolated gfx906
  HIP build. Its native binary SHA-256 is
  `c3aebb611d91f104786b6b8bc5773977727ed12be6fafa44064c8c14b76566ca`, built with llama.cpp commit
  `3cf03257f219afbe7334045ff7c6a06ac68c627d` in build image
  `sha256:06c8bd0e6ede3614ad3467a056cce06e111ca854e3c7251cc0a140e89c9c32fb`. Both hosted CPU checks passed.
  This did not include a model-backed native protocol test, GPU runtime smoke, token or recurrent-state parity,
  an AB/CD port, a new image, or a current-main GPU smoke.
- **PR #26 serial-window trace build:** the separate `STRATA_CORRECTNESS_WINDOW_TRACE=1` opt-in serial-window
  trace passed an isolated gfx906 HIP compile, producing native binary SHA-256
  `68b582aeee55707082b0db49c3cdc7ae3e464c515a651e3ed758cfb628c92594`. Both hosted CPU checks passed. The
  base request-ID trace continues to support batch requests. This binary later received a separate short serial
  GPU smoke, documented below. The smoke is trace-accounting evidence only; it is not an AB/CD comparison,
  token/state parity result, or new image build.
- **PR #29 synthetic state-checkpoint validator:** PR [#29](https://github.com/cassettesgoboom/strata-gfx906/pull/29)
  merged in main at `a9e6712c`. It adds a synthetic state-checkpoint validator. The suite had 60 tests at that revision.
  The validator compares `diagnostic_records_equal` only and emits `runtime_parity_claim=false`; synthetic equality
  validates the diagnostic comparison path, not runtime state parity or capture authenticity.
- **V3 native state-trace contract:** the checked-in [v3 contract](../../benchmarks/gfx906/fixtures/native-runtime-parity-contract-v3.json),
  [trace schema](../../benchmarks/gfx906/fixtures/native-runtime-parity-trace-v3.schema.json), and
  [CPU comparator](../../tests/gfx906/runtime_parity_v3.py) add an initial prompt/cache checkpoint plus absolute
  commit boundaries for ordered native token IDs and model-declared GDN, QSA, PLE, and MTP
  state. Tests cover prompt-tail and rolling PLE predecessor IDs, accepted MTP prefixes, exact mode-specific state
  fields, component serialization descriptors, bounded trace loading, and architecture-derived inventories. All
  fixtures are synthetic and output keeps `runtime_parity_claim=false`; this does not authenticate capture or digest
  source bytes, add native capture, run inference, integrate AB/CD, or establish runtime parity. V2 remains unchanged
  and requires recapture for the additional v3 boundaries. The v3 `command_sha256` contract now specifies a versioned
  normalized identity, JCS serialization, and the sole AB/CD toggle exclusion. No native producer implements this
  contract, and the comparator cannot authenticate its normalization or capture. The full CPU suite passes 77 tests.
- **PR #26 serial-window GPU smoke:** a short serial smoke exercised the PR #26 native binary
  (`68b582aeee55707082b0db49c3cdc7ae3e464c515a651e3ed758cfb628c92594`) on two gfx906 MI50 cards at 4096
  context. It used the archived OCI runtime as a base and overmounted the newer binary; no new image was built
  or published. A repeated warm request recorded 75 prompt and 146 output tokens, with 70 reused prompt tokens.
  A continuation using the actual assistant response recorded 173 prompt, 130 output, and 70 reused tokens.
  Contiguous native windows contained 51 and 57 records, respectively; native token-ID counts matched
  client/native completion counts of 146 and 130. MTP accepted/offered counts were 96/118 and 76/88. The initial
  native-log collection attempt was corrected by repeating the short requests inside the same candidate. This
  receipt covers trace accounting only: it is not an AB/CD comparison, state-parity check, or throughput benchmark.
  The model-backed raw trace remains private, so this sanitized receipt is not independently reproducible. The
  copied build source had no Git metadata; the tested binary is identified by its PR #26 source association and
  hash, but an exact post-merge whole-tree build identity is unproven.
  See the [sanitized receipt](../../benchmarks/gfx906/receipts/2026-10-17-pr26-serial-smoke.json).
- **Current upstream release and branch:** the latest official release is v0.1.45, and its tag and current
  upstream `main` resolve to `477ac13cbe8e582c20484871ce459d20d82df09d`. The dated feature map in
  [UPSTREAM-DELTA.md](UPSTREAM-DELTA.md) records the gfx906, K8/V4, and serial batch-MTP source history. A
  pre-merge source-equivalent build has a short serial GPU smoke.
  At the earlier 2026-10-17 checkpoint (SHA `73e01b3a5f1c577899e3f668e7e913759a1f7455`), no build or GPU smoke
  was recorded for post-merge main. PR #22 subsequently built source commit `22cae852bbbe433c1cdf65ab4daaef7bfeaf650d`,
  but there is still no GPU runtime result for that refactor or for the reviewed fork source snapshot
  `af45b70bf5cb7e61a0e0825c632397190a97e18b`. PR #25/#26 add trace instrumentation; PR #26 now has the separate
  short serial smoke described above. Its copied build source had no Git metadata, so the smoke does not prove an
  exact post-merge whole-tree build identity. No public GPU receipt identifies the exact whole-tree source for
  reviewed fork source snapshot `af45b70bf5cb7e61a0e0825c632397190a97e18b`, and no current-main AB/CD or parity validation is
  recorded.
  The current-main tree is not validated by archived binary results.
  [Draft PR #4](https://github.com/cassettesgoboom/strata-gfx906/pull/4) preserves a privacy-adapted historical
  AB/CD source candidate against v0.1.41 for review only. PR #17 supplies a CPU transaction-trace comparison
  contract but does not port that candidate to current main, reproduce the archived executable, or pass runtime
  token/state parity.

See [evidence index](EVIDENCE.md) for scope and provenance. The
[build-receipt schema](../../benchmarks/gfx906/build-receipt-v1.schema.json) supports future reproducible build records.
**Issue #1 current-main verifier blockers:** the PR #15/#19 registry remains unused scaffolding, not wired into
`Verifier` or the scheduler. Current main still needs per-slice graph, staging, and poll ownership and must tie
commit intent to observed device results. The CPU contract requires post-launch failure/abort to drain device work
and obtain session recovery/discard acknowledgement before retirement, but it does not implement those runtime
actions. Ordinary reject handling restores the QSA tail and re-appends accepted keys, but it is not general rollback
for failed or aborted same-session overlapping slices: indexer appends also mutate dead, pooled, and block-position
state, while GDN commit mutates persistent recurrence state in place. This rollback gap remains unresolved.
**Next source gate:** wire the transaction lifecycle and recovery contract into the current-main verifier/scheduler,
including slice-local resource ownership, device drain, and recovery of affected session state after failure or
abort; then build from a pinned current-main revision and run an isolated GPU comparison against serial for ordered
native token IDs and recurrent-state hashes at matching window ends. Keep AB/CD opt-in until those runtime checks
pass. Archived source-to-image proof remains open.

**PR #41 merged in current main (2026-10-18):** [PR #41](https://github.com/cassettesgoboom/strata-gfx906/pull/41)
merged at [`9efd4da532b041be4cdef273e8da6cbd946a49d2`](https://github.com/cassettesgoboom/strata-gfx906/commit/9efd4da532b041be4cdef273e8da6cbd946a49d2).
Its narrow change uses the existing `OnDevice` scope around `MtpDrafter::idle()` stream synchronization and
destructor cleanup, selecting the CUDA/HIP device captured by that drafter and restoring the caller's device.
It does not change scheduling, MTP acceptance, model arithmetic, or AB/CD behavior.

PR validation recorded 77 passing tests from `python tools/gfx906.py test-cpu`, a passing workflow-equivalent C++20
fake-runtime compile/run, and a passing CPU CMake target `on_device_scope_test` with CTest 1/1 using the pinned
local llama.cpp dependency. The isolated Release/Ninja gfx906 HIP `strata` target completed 147/147 steps;
`ldd` resolved all dependencies and `strata --help` passed with no GPU devices or model assets. The
[compile receipt](../../benchmarks/gfx906/receipts/2026-10-17-mtp-device-scope-hip-build.json) records the
toolchain, dependency and binary identity. The CPU helper test covers `OnDevice`; it would not fail if either
MTP call-site guard were removed.

The separate [2026-10-18 smoke receipt](../../benchmarks/gfx906/receipts/2026-10-18-mtp-device-scope-smoke.json)
preserves the source and binary provenance for a short model-backed serial inference and conversation-reuse
smoke. It used the archived runtime image as a base with the PR-source binary and Python server source mounted;
no image was built or published. It had no MTP accepted/offered counters. No defect or call-site runtime failure
was reproduced, and the smoke did not exercise the changed device-scoping path. This change does not port AB/CD,
establish token or recurrent-state parity, or qualify a production image.

**Current-main validation after PR #49 (2026-10-18):** [PR #49](https://github.com/cassettesgoboom/strata-gfx906/pull/49)
merged at [`fe16acb527ac593c2f8037b6d4883bede131597e`](https://github.com/cassettesgoboom/strata-gfx906/commit/fe16acb527ac593c2f8037b6d4883bede131597e).
Its hosted CPU workflow [run `39086817840`](https://github.com/cassettesgoboom/strata-gfx906/actions/runs/39086817840)
succeeded. A fresh `python tools/gfx906.py test-cpu` run at this
revision passed 78 tests. These checks validate CPU tooling only.

The PR #41 [HIP build receipt](../../benchmarks/gfx906/receipts/2026-10-17-mtp-device-scope-hip-build.json)
records binary SHA-256 `3e6d46636e5671c5920b374ce55202dadbf2e111e5db3e8ba4fb46b69ae701c8` for an isolated,
compile-only gfx906 HIP Release build. It records base commit
`3f076fea5a98f69d2fec1d364b21380eb1a67e95` and these changed native-file fingerprints:
`include/strata/core/mtp.hpp` `e9d7c23e8c8617d621fd94c466d8463bd80ed063867735f48ab2b0aeb6091ad6`,
`src/core/mtp.cpp` `5f97261e06660162b374d80499cf95735d25ac84106196fb11f58ac640156d83`. The build receipt has no
explicit built Git commit. The fingerprints match the PR #41 runtime change commit
`7face86d0eb42712a068a19fdb7d661ecfe4755d`, its merge `9efd4da532b041be4cdef273e8da6cbd946a49d2`, and
current main at PR #49 merge `fe16acb527ac593c2f8037b6d4883bede131597e`; neither native-source path changed
between the PR #41 merge and that current-main revision. This binary is not the archived benchmark binary
`ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`. The build receipt establishes neither
source reproduction nor inference or parity. The separate smoke receipt records short serial inference, but
does not establish that the changed device-scoping path was exercised, MTP proposal activity, token parity, or
persistent recurrent-state parity.

**PR #52 upstream gfx906 file-tier policy (2026-10-18):** [PR #52](https://github.com/cassettesgoboom/strata-gfx906/pull/52)
merged at [`2bbf2a64f4d4507cc39f71fa1392a21620fa7f8e`](https://github.com/cassettesgoboom/strata-gfx906/commit/2bbf2a64f4d4507cc39f71fa1392a21620fa7f8e).
It selectively ports upstream [commit `1d6fd9f97ab09da231b35cbbd84a2879adb6d77f`](https://github.com/Niko1221/Strata/commit/1d6fd9f97ab09da231b35cbbd84a2879adb6d77f)
(PR #1752, KevinX8) in the Linux expert file-tier cache decision. On Linux,
gfx906 builds use the older full-read rule by default; other builds retain the
hot-read rule. `STRATA_FILE_CACHE_OLD_RULE=1` selects the older rule and
`STRATA_FILE_CACHE_OLD_RULE=0` selects the hot-read rule. The existing
`STRATA_UNBUFFERED_LOAD` force setting returns before this selection and retains
precedence.

The checked-in [build receipt](../../benchmarks/gfx906/receipts/2026-10-18-pr1752-gfx906-hip-build.json)
records a compile-only gfx906 HIP Release build (147/147 Ninja steps) from base
`294fe5248273ec1a9c7331d81d0708ce8e66423c` plus a patch bundle, with no GPU
devices or model assets; its binary SHA-256 is
`805ffbf38e0e0030f99f7b62b96aa129350d96fe016d08e580abab3fe98806f8`. This is
not a local MI50 runtime or performance comparison. The policy change does not
port AB/CD, establish token/state parity, or identify the source of the archived
benchmark binary. Issue #24's runtime ownership, drain, and recovery gate remains
open.
