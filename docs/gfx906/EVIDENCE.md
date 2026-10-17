# gfx906 evidence summary

This is a sanitized historical benchmark summary. It preserves the workload labels and rates provided for this record; it is not a fresh run or a complete benchmark report.

| Workload | Configuration | Strict SSE estimate (tokens/s) | Whole-wave estimate (tokens/s) | Interpretation |
| --- | --- | ---: | ---: | --- |
| P2 serial | 2 lanes, about 96K context | 38.43 | 33.35 | Archived cached multi-agent run. |
| P2 serial | 2 lanes, about 152K context, 512 tokens/lane | 45.19 | 36.19 | Archived cached multi-agent run. |
| P3 serial | 3 lanes, about 99K context | 52.46 | 41.67 | Archived cached multi-agent run. |
| P3 serial | 3 lanes, about 152K context, 512 tokens/lane | 47.37 | 35.93 | Archived cached multi-agent run. |
| P4 AB/CD opt-in | 4 lanes, about 33K context | 67.10 | 55.73 | Archived cached multi-agent run; exact-token and state parity remain open. |
| P4 AB/CD opt-in | 4 lanes, 102K context | 71.17 | 53.94 | Archived cached multi-agent run; emitted 512/512/512/473 tokens and the fourth lane stopped naturally. Exact-token and state parity remain open. |
| P2 capacity run | 2 lanes, about 192K context, cached continuations only, 65 tokens/lane | — | — | Capacity-only observation; not a sustained throughput result. |

These are the archived MI50 figures documented in [PR #11](https://github.com/cassettesgoboom/strata-gfx906/pull/11) and the repository README, not fresh measurements. Strict overlap is estimated from client SSE timing over the common-overlap interval. The P2/P3/P4 rows use different runs and schedulers; their rates do not establish a direct causal speedup. The P2 192K entry is capacity evidence only and must not be represented as a throughput benchmark. AB/CD remains opt-in pending exact-token and state parity evidence.

## Measurement caveat

These values are sanitized historical estimates, not independently reproduced here. Keep the strict SSE estimate and whole-wave estimate distinct. Do not combine them into one rate or imply that either value proves the image's source provenance. Artifact identity and source limitations are documented in [PROVENANCE.md](PROVENANCE.md).

## Pre-merge source-equivalent serial GPU smoke

The [2026-10-16 machine-readable receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-gpu-smoke.json) identifies the tested source-equivalent fork main as pre-merge commit `64185a40962121b9adfc20e0e1a45b634cfeb472` and the native binary SHA-256 as `73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`. It records that binary running on two MI50 cards. The first 4K-context request generated 146 tokens. Its continuation, constructed with the actual first answer, generated 130 tokens and reused 70 prompt tokens according to native request metrics. Both returned HTTP 200 with `stop` finish reasons; MTP accepted 173 of 208 offered proposals across the two requests. Candidate swap and OOM counters remained zero, and the isolated candidate shut down cleanly.

The pre-merge source-equivalent binary and server were mounted into the archived runtime image for this smoke. The published image still contains the archived binary. No rebuild or GPU smoke is recorded for post-merge main at the 2026-10-17 checkpoint (audited checkpoint SHA `73e01b3a5f1c577899e3f668e7e913759a1f7455`). These short serial requests do not measure sustained multi-agent throughput, validate AB/CD, or prove exact native-token or recurrent-state parity. They must not be pooled with the historical benchmark table above.

## PR #22 one-window verifier refactor build

[PR #22](https://github.com/cassettesgoboom/strata-gfx906/pull/22) merged the mechanical refactor that groups
existing single-window verifier state into `Verifier::WindowContext`. Its source commit
`22cae852bbbe433c1cdf65ab4daaef7bfeaf650d` passed an isolated gfx906 HIP Release/Ninja `strata` build; the
resulting native binary SHA-256 is `cb7f37249a34b7e8d24232f4e57da9a035c473d5bd598e83b53bad8d781c8db2`,
and its `--help` path loaded. The 44-test CPU suite and both hosted CPU checks passed. This is compile and CLI
evidence only: no GPU runtime test or inference, no two-slice AB/CD isolation, no native-token or recurrent-state
parity, and no new image publication were performed. The PR comment contains the sanitized build receipt.

## PR #25 opt-in native request correlation build

[PR #25](https://github.com/cassettesgoboom/strata-gfx906/pull/25) merged opt-in request-ID transport and
native-leg correlation for future correctness traces. Its isolated gfx906 HIP build produced native binary
SHA-256 `c3aebb611d91f104786b6b8bc5773977727ed12be6fafa44064c8c14b76566ca`, using llama.cpp commit
`3cf03257f219afbe7334045ff7c6a06ac68c627d` and build image
`sha256:06c8bd0e6ede3614ad3467a056cce06e111ca854e3c7251cc0a140e89c9c32fb`. Both hosted CPU checks passed.
This did not include a model-backed native protocol test, GPU runtime smoke, token or recurrent-state parity,
an AB/CD port, a new image, or a current-main GPU smoke.

## PR #26 opt-in serial-window trace build

[PR #26](https://github.com/cassettesgoboom/strata-gfx906/pull/26) adds a separate
`STRATA_CORRECTNESS_WINDOW_TRACE=1` serial-window trace mode; the base request-ID trace continues to support
batch requests. The isolated gfx906 HIP compile produced native binary SHA-256
`68b582aeee55707082b0db49c3cdc7ae3e464c515a651e3ed758cfb628c92594`. Both hosted CPU checks passed. This
does not by itself establish model-backed capture, GPU runtime behavior, token parity, recurrent-state hash parity,
or publication of a new image. A later short serial GPU smoke of this binary is summarized below.

## PR #26 serial-window GPU smoke

The [sanitized receipt](../../benchmarks/gfx906/receipts/2026-10-17-pr26-serial-smoke.json) records a short
serial smoke on two gfx906 MI50 cards at 4096 context. It exercised the PR #26 native binary
`68b582aeee55707082b0db49c3cdc7ae3e464c515a651e3ed758cfb628c92594` over the archived OCI runtime base with
the newer binary overmounted. No new image was built or published. The repeated warm request recorded 75 prompt,
146 output, and 70 reused prompt tokens; the actual-assistant continuation recorded 173 prompt, 130 output, and
70 reused tokens. The contiguous native windows contained 51 and 57 records. Native token-ID counts matched the
146 and 130 client/native completion counts. MTP accepted/offered counts were 96/118 and 76/88. An initial
native-log collection attempt was corrected by repeating the short requests inside the same candidate; only the
corrected trace accounting is summarized here. This is not a throughput benchmark, AB/CD comparison, or state
parity result, and it must not be pooled with the archived throughput evidence. The model-backed raw trace remains
private, so this sanitized receipt is not independently reproducible. The copied build source had no Git metadata:
the tested binary is identified by its PR #26 source association and hash, but the exact post-merge whole-tree
build identity is unproven. No GPU smoke has a proven exact post-merge whole-tree source identity, and no
current-main AB/CD or parity validation is established.

## PR #29 synthetic state-checkpoint validator

[PR #29](https://github.com/cassettesgoboom/strata-gfx906/pull/29) merged at `a9e6712c`. The 60-test CPU suite
passes. The synthetic validator compares `diagnostic_records_equal` only and keeps
`runtime_parity_claim=false`. It validates comparator behavior on supplied diagnostic records; it does not
authenticate runtime capture or establish token or persistent-state parity.

## CPU-only AB/CD trace comparator

[PR #12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) adds a CPU-only comparator for supplied serial-OFF and AB/CD-ON native commit traces, with synthetic fixtures and fail-closed tests. The current v2 contract compares ordered native token IDs per committed window and persistent-state hashes at the end of that window; it also checks matched provenance and inputs, cache history, commit boundaries, and MTP decisions. Its output always sets `runtime_parity_claim` to `false`: matching JSON proves only that the supplied traces compare equal. It does not authenticate trace capture, establish runtime parity, run a model, validate GPU behavior, or port AB/CD to current main. See [the v2 contract](../../benchmarks/gfx906/fixtures/abcd-parity-contract-v2.json). V1 traces require regeneration or a migration justified by original transaction-boundary evidence.
