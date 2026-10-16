# gfx906 evidence summary

This is a sanitized historical benchmark summary. It preserves the workload labels and rates provided for this record; it is not a fresh run or a complete benchmark report.

| Workload | Configuration | Strict SSE estimate (tokens/s) | Whole-wave estimate (tokens/s) | Interpretation |
| --- | --- | ---: | ---: | --- |
| P4 | 4 lanes, about 102K context, AB/CD on | 71.17 | 53.94 | Historical multi-lane run. AB/CD exact-token and state parity remain open. |
| P3 | 3 lanes, about 152K context, serial, 512 tokens/lane | 47.37 | 35.93 | Historical serial run. |
| P2 capacity run | 2 lanes, about 192K context, cached continuations only, 65 tokens/lane | — | — | Capacity-only observation; not a sustained throughput result. |
| P2 sustained run | 2 lanes, about 152K context, 512 tokens/lane | 45.19 | 36.19 | Historical sustained run. |

The P4, P3, and P2 runs use different lane counts, context sizes, cache conditions, and token counts. Their rates do not establish a direct causal speedup between configurations. The P2 192K entry is capacity evidence only and must not be represented as a throughput benchmark. AB/CD remains opt-in pending exact-token and state parity evidence.

## Measurement caveat

These values are sanitized historical estimates, not independently reproduced here. Keep the strict SSE estimate and whole-wave estimate distinct. Do not combine them into one rate or imply that either value proves the image's source provenance. Artifact identity and source limitations are documented in [PROVENANCE.md](PROVENANCE.md).

## Current-source serial GPU smoke

The [2026-10-16 machine-readable receipt](../../benchmarks/gfx906/receipts/2026-10-16-current-main-gpu-smoke.json) records a new, separate source-equivalent gfx906 binary (`73a0f98105938850c749a3f0ed1dfe08e1753a97379aa9741c7fb73351c0137c`) running on two MI50 cards. The first 4K-context request generated 146 tokens. Its continuation, constructed with the actual first answer, generated 130 tokens and reused 70 prompt tokens according to native request metrics. Both returned HTTP 200 with `stop` finish reasons; MTP accepted 173 of 208 offered proposals across the two requests. Candidate swap and OOM counters remained zero, and the isolated candidate shut down cleanly.

The new binary and current-source server were mounted into the archived runtime image for this smoke. The published image still contains the archived binary. These short serial requests do not measure sustained multi-agent throughput, validate AB/CD, or prove exact native-token or recurrent-state parity. They must not be pooled with the historical benchmark table above.
