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

**Current fork main (checked 2026-10-18):**
[`3f076fea5a98f69d2fec1d364b21380eb1a67e95`](https://github.com/cassettesgoboom/strata-gfx906/commit/3f076fea5a98f69d2fec1d364b21380eb1a67e95).
Since the reviewed engine-source snapshot below, PR [#37](https://github.com/cassettesgoboom/strata-gfx906/pull/37)
refreshed public state and provenance, PR [#38](https://github.com/cassettesgoboom/strata-gfx906/pull/38)
clarified the synthetic v3 command-identity contract, and PR
[#39](https://github.com/cassettesgoboom/strata-gfx906/pull/39) redacted local roots from three benchmark
configuration snapshots. PR [#40](https://github.com/cassettesgoboom/strata-gfx906/pull/40) then refreshed this
state and provenance record. These commits change documentation, parity-contract/tests, or benchmark configuration
records; they do not add a native AB/CD runtime port or new GPU/parity evidence. Fork main remains based on
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
- **Public fork:** main retains upstream ancestry and [PR #2](https://github.com/cassettesgoboom/strata-gfx906/pull/2) is merged. The current `test-cpu` suite passes 77 tests; this does not validate GPU execution. A clean-checkout onboarding review used only public files.
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
