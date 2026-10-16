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

The pre-merge source-equivalent binary and server were mounted into the archived runtime image for this smoke. The published image still contains the archived binary. Current main `73e01b3a5f1c577899e3f668e7e913759a1f7455` has not been rebuilt or GPU-smoked. These short serial requests do not measure sustained multi-agent throughput, validate AB/CD, or prove exact native-token or recurrent-state parity. They must not be pooled with the historical benchmark table above.

## CPU-only AB/CD trace comparator

[PR #12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) adds a CPU-only comparator for supplied serial-OFF and AB/CD-ON native commit traces, with synthetic fixtures and fail-closed tests. The current v2 contract compares ordered native token IDs per committed window and persistent-state hashes at the end of that window; it also checks matched provenance and inputs, cache history, commit boundaries, and MTP decisions. Its output always sets `runtime_parity_claim` to `false`: matching JSON proves only that the supplied traces compare equal. It does not authenticate trace capture, establish runtime parity, run a model, validate GPU behavior, or port AB/CD to current main. See [the v2 contract](../../benchmarks/gfx906/fixtures/abcd-parity-contract-v2.json). V1 traces require regeneration or a migration justified by original transaction-boundary evidence.
