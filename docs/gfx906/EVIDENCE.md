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
