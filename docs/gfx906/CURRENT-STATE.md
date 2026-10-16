# gfx906 current state

**Recorded:** 2026-10-17. **Stage:** public gfx906 foundation and current-main build fixes are merged; a
pre-merge source-equivalent binary passed a short serial MI50 GPU smoke. PR [#11](https://github.com/cassettesgoboom/strata-gfx906/pull/11)
adds archived MI50 measurements. PR [#12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) introduced a
CPU-only AB/CD trace comparator; [#17](https://github.com/cassettesgoboom/strata-gfx906/pull/17) supersedes its
v1 record format with ordered token vectors per committed transaction/window and state hashes at window end.
PR [#15](https://github.com/cassettesgoboom/strata-gfx906/pull/15) adds an unused host-side transaction lifecycle
registry; [#19](https://github.com/cassettesgoboom/strata-gfx906/pull/19) adds two-phase commit intent/result,
accepted-prefix validation and copy, and explicit drain/recovery gates to that CPU contract. The registry remains
unused by the runtime. `python tools/gfx906.py test-cpu` passes 44 Python tests; PR #19 also passes a separate,
focused C++20 transaction test. These changes do not integrate AB/CD into the runtime, establish GPU overlap or
parity, or change the published image.

- **Source base:** upstream `296b59d2f73c8f04a805df29c2fa97655adace78`.
- **Archived native binary:** SHA-256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`.
- **Archived OCI index:** `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- **Public fork:** main retains upstream ancestry and [PR #2](https://github.com/cassettesgoboom/strata-gfx906/pull/2) is merged. The current `test-cpu` suite passes 44 tests locally; this does not validate GPU execution. A clean-checkout onboarding review used only public files.
- **Merged build fixes:** [PR #6](https://github.com/cassettesgoboom/strata-gfx906/pull/6) merged alias fix `8c30f4744f8df7a7ce71805959e426116b271410`; [PR #7](https://github.com/cassettesgoboom/strata-gfx906/pull/7) merged the Blackwell W4A4 CMake exclusion `b65fdb01810fa11914a2c21bef5468b5dee5a623`.
- **Pre-merge current-main-equivalent build receipt:** combined gfx906 HIP Release/Ninja build succeeded in an isolated networkless container with a 6 GiB memory limit. It used ROCm clang `23.0.0git`, GGML/llama.cpp commit `3cf03257f219afbe7334045ff7c6a06ac68c627d`, and source base `02f500b8056f9cc7af27dfa577476e69eaab75a6` before the merged fixes. The associated smoke receipt maps the tested binary to pre-merge fork main `64185a40962121b9adfc20e0e1a45b634cfeb472`; it is not a build of current main `73e01b3a5f1c577899e3f668e7e913759a1f7455`. The newly produced local binary SHA-256 is `73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`. Its CPU-only `--help` path succeeded and 30 CPU tooling tests passed. See the [machine-readable build receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-equivalent.json) and [exact patch bundle](../../benchmarks/gfx906/receipts/2026-10-16-current-main-equivalent.patch) for toolchain, source, command, and artifact details.
- **Build and smoke boundary:** this build did not reproduce the pinned historical benchmarked binary (`ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`). The separate [GPU smoke receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-gpu-smoke.json) identifies its source-equivalent fork main as pre-merge commit `64185a40962121b9adfc20e0e1a45b634cfeb472` and the tested native binary SHA-256 as `73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`. It records short serial inference on dual MI50: 146 generated tokens on a first request, then 130 on a continuation with 70 native reused prompt tokens; MTP accepted/offered totals were 173/208. The server and binary were mounted into the archived runtime image. No new image was published. Current main `73e01b3a5f1c577899e3f668e7e913759a1f7455` has not been rebuilt or GPU-smoked. These short requests do not establish sustained performance, batch AB/CD, or exact token/state parity; archived benchmark measurements below remain scoped to the pinned binary.
- **Archived throughput evidence:** the README table now records six cached multi-agent runs from the published image: P2 serial at ~96K (38.43 strict / 33.35 whole-wave tok/s) and ~152K (45.19 / 36.19); P3 serial at ~99K (52.46 / 41.67) and ~152K (47.37 / 35.93); P4 AB/CD opt-in at ~33K (67.10 / 55.73) and 102K (71.17 / 53.94). The P4 102K run emitted 512/512/512/473 tokens, with the fourth lane stopping naturally. Strict overlap is an SSE-derived estimate; different rows do not establish causal speedup. P2 at ~192K with cached histories and 65-token continuations is capacity evidence only. See [EVIDENCE.md](EVIDENCE.md) for the full table and caveats. All figures apply to the archived binary and public dual-MI50 32 GB / K8-V4 scope.
- **AB/CD comparator boundary:** PR #17 updates the CPU-only comparator to v2 `native_transaction_trace_v2`
  records: each committed transaction/window carries a non-empty ordered `native_token_ids` list, with
  persistent-state hashes compared only at `commit_window_end`. The old v1 singular-token format is rejected;
  existing traces need regeneration or migration backed by original transaction-boundary evidence. Output
  always has `runtime_parity_claim=false`; synthetic equality checks comparator behavior only. The tool cannot
  authenticate capture or prove runtime parity. No current-main AB/CD port or runtime parity validation is included.
- **Transaction lifecycle boundary:** PR #15 introduced a host-side registry for two disjoint row slices, immutable slot/token/position snapshots, and lifecycle transitions. PR #19 adds two-phase commit intent/result: `begin_commit` validates and stores accepted prefixes in registry-owned state; `finish_commit` records success only after the runtime observes the device result. The slice remains undrained during commit. Post-launch failure or abort requires explicit device drain and session recovery/discard before retirement. The accessor copies the validated accepted-prefix intent so later caller-array changes cannot alter it. Validation is 44 Python tests plus a separate focused C++20 transaction test. This remains scaffolding: it is not wired into `Verifier` or the scheduler, and does not implement QSA rollback, GPU transaction isolation, inference, or parity.
- **Current source:** upstream v0.1.44.1 already includes gfx906, K8/V4, and serial batch-MTP paths; see
  [the dated upstream map](UPSTREAM-DELTA.md). A pre-merge source-equivalent build has a short serial GPU smoke,
  but current main `73e01b3a5f1c577899e3f668e7e913759a1f7455` has not been rebuilt or GPU-smoked, has not passed
  batch AB/CD or parity validation, and is not validated by archived binary results.
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
